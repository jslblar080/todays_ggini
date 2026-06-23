"""
FILE: post_cleaner.py
ROLE: [본질 노드 통합 + 관계 속성 분리] 작업 중 발생하는 null 값 에러 방지 및 
      중단 지점부터 재시작 가능한 고도화된 정제 엔진.
"""
import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM

load_dotenv()

class PostCleaner:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )
        self.llm = OllamaLLM(model="llama3", temperature=0, format="json")

    def close(self):
        self.driver.close()

    def get_dirty_ingredients(self):
        """
        정제가 필요한 노드들을 가져오되, 
        이미 standard_name이 부여된 관계와 연결된 노드는 제외하여 효율성을 높입니다.
        """
        with self.driver.session() as session:
            # 아직 standard_name 속성이 없는 REQUIRES 관계를 가진 Ingredient 노드 추출
            query = """
            MATCH (m:Menu)-[r:REQUIRES]->(i:Ingredient)
            WHERE r.standard_name IS NULL
            RETURN DISTINCT i.name as name
            """
            result = session.run(query)
            return [record["name"] for record in result]

    def fetch_mapping_from_llm(self, names):
        prompt = f"""
        당신은 식품 데이터 전문가입니다. 아래 재료 리스트를 [본질]과 [상태]로 분리하세요.

        [규칙]
        - base: 재료의 핵심 명칭 (예: '다진 양파' -> '양파', 'minced garlic' -> '마늘')
        - state: 가공 상태 (예: '다진', '말린', '불린', '가루' 등) 없으면 null.
        - 응답은 반드시 {{ "원본명": {{"base": "본질", "state": "상태"}}, ... }} 형식의 JSON이어야 합니다.
        - base 값은 절대 null이나 빈 문자열일 수 없습니다.

        [리스트]
        {", ".join(names)}
        """
        try:
            response = self.llm.invoke(prompt)
            data = json.loads(response)
            
            # 응답 데이터 보정: base가 null이면 원본명을 집어넣음
            cleaned_mapping = {}
            for original, info in data.items():
                if info and info.get("base"):
                    cleaned_mapping[original] = info
                else:
                    # 방어 로직: LLM이 누락시킨 경우 원본 텍스트를 base로 사용
                    cleaned_mapping[original] = {"base": original, "state": None}
            return cleaned_mapping
        except Exception as e:
            print(f" [!] LLM 분석 오류: {e}")
            return {}

    def reformat_graph(self, mapping):
        """
        null 방어 로직이 추가된 그래프 재편성 쿼리
        """
        with self.driver.session() as session:
            query = """
            UNWIND $batch AS item
            // item.base가 null인 경우 실행하지 않도록 보호
            WITH item WHERE item.base IS NOT NULL
            
            MATCH (old:Ingredient {name: item.original})
            MATCH (m:Menu)-[old_r:REQUIRES]->(old)
            
            // 1. 본질 노드 생성 (MERGE)
            MERGE (new:Ingredient {name: item.base})
            
            // 2. 관계 복사 및 속성 갱신
            MERGE (m)-[new_r:REQUIRES]->(new)
            SET new_r += properties(old_r),
                new_r.state = item.state,
                new_r.standard_name = item.base
            
            // 3. 기존 관계 및 고립 노드 삭제
            DELETE old_r
            WITH old
            OPTIONAL MATCH (old)-[remaining_r]-()
            WITH old, count(remaining_r) AS rel_count
            WHERE rel_count = 0
            DELETE old
            """
            batch = [{"original": k, "base": v["base"], "state": v.get("state")} 
                     for k, v in mapping.items()]
            
            if batch:
                session.run(query, batch=batch)

    def run(self):
        all_names = self.get_dirty_ingredients()
        total = len(all_names)
        print(f"[*] 정제 대상 재료: {total}개")
        
        if total == 0:
            print("✅ 이미 모든 재료가 정제되었습니다.")
            return

        batch_size = 30 # 안정성을 위해 배치 사이즈를 약간 하향
        for i in range(0, total, batch_size):
            chunk = all_names[i : i + batch_size]
            print(f"[*] {i} ~ {min(i + batch_size, total)} 처리 중...")
            
            mapping = self.fetch_mapping_from_llm(chunk)
            if mapping:
                try:
                    self.reformat_graph(mapping)
                except Exception as e:
                    print(f" [!] Cypher 실행 중 에러 발생 (건너뜀): {e}")
                    continue
                
        print("✅ 사후 정제 프로세스 종료")

if __name__ == "__main__":
    cleaner = PostCleaner()
    cleaner.run()
    cleaner.close()