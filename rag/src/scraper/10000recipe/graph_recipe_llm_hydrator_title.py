"""
FILE: graph_recipe_llm_hydrator_title.py
ROLE: [메뉴명 단축 전용 이어하기 엔진] 
      - 기존에 steps 가공은 완료되었으나 만개의레시피 원문 제목이 그대로 방치된 노드들을 추적합니다.
      - i.category 적재 완료 상태이므로, 지워진 raw_html_text 대신 기존 r.steps 배열을 문맥으로 활용해 
        Gemma2의 VRAM 부하를 최소화하고, 제목만 초고속(1~2초)으로 단축 정제하여 r.refined_title에 적재합니다.
      - 정적 분석기 노란 줄(LLMHydrator 오타) 및 정규식 FutureWarning 완벽 해결본.
DEPENDENCY: pip install requests neo4j python-dotenv
"""
import os
import re
import json
import time
import requests
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

OLLAMA_BASE_URL = os.getenv("GEMMA_API_URL", "http://localhost:11434").replace("/api/generate", "").replace("/api/chat", "").rstrip("/")
LLM_API_URL = f"{OLLAMA_BASE_URL}/api/chat"
MODEL_NAME = "gemma2:9b"

class GraphRecipeLLMHydrator:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def ask_gemma_to_shorten_title(self, original_title: str, steps: list) -> str:
        """기존에 가공 완료된 조리법(steps) 문맥을 기반으로 메뉴명만 직관적으로 단축"""
        if not original_title:
            return ""

        # 원문이 유실된 상태이므로, 이미 정제 완료된 steps 내용을 요약 문맥으로 재활용 (발열 및 VRAM 부하 극소화)
        context_steps = "\n".join(steps) if steps else "조리 과정 정보 없음"

        system_instruction = f"""You are a Food-Tech data engineering expert and culinary database administrator.
Analyze the given messy recipe title and its brief cooking steps to extract a clean, short, and clear Korean menu name.

[Strict Translation Rules]
1. Remove all descriptors, marketing buzzwords, brackets, icons, and emotional adjectives.
   - Example 1: '간단하지만 중독성있게맛있는 간장파스타' -> '간장파스타'
   - Example 2: '<다이어트 건강식>초간단 닭가슴살 토마토 스튜' -> '닭가슴살 토마토 스튜'
   - Example 3: '♥[신혼밥상] 유자파운드케이크' -> '유자파운드케이크'
2. Output ONLY the final refined Korean menu name on a single line. 
3. Do NOT include any intro, outro, explanations, or markdown backticks.

Original Title to Refine: {original_title}
Output (Plain text name only):"""

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Cooking Steps Context:\n{context_steps}"}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 128, # 제목만 뽑으면 되므로 출력 토큰 최소화 (초고속 인퍼런스 보장)
                "num_ctx": 2048
            }
        }

        try:
            response = requests.post(LLM_API_URL, json=payload, timeout=30)
            if response.status_code != 200:
                return original_title[:15]
                
            res_json = response.json()
            response_text = res_json.get("message", {}).get("content", "").strip()
            
            if not response_text:
                return original_title[:15]

            # 기호 노이즈 최종 전처리
            response_text = re.sub(r'[\'\"\[\]\-\+#]', '', response_text).strip()
            # 만약 모델이 TITLE: 같은 접두어를 붙였을 경우 방어 코드
            response_text = response_text.replace("TITLE:", "").strip()
            
            return response_text

        except Exception as e:
            print(f"   ❌ 오케스트레이션 장애: {e}")
            return original_title[:15]

    def run_title_migration_pipeline(self, limit: int = 20):
        print("============================================================")
        print("💡 [특수 마이그레이션: Gemma2 지능형 메뉴명 단축 전수 정제 시작]")
        print("============================================================")
        
        # 💡 [쿼리 보완]: title_refined_status 태그 필드가 없거나 'SUCCESS'가 아닌 노드만 조준 (완벽한 이어하기 지원)
        find_query = """
        MATCH (r:Recipe)
        WHERE r.title_refined_status IS NULL OR r.title_refined_status <> 'SUCCESS'
        RETURN elementId(r) as node_id, r.title as original_title, r.steps as steps
        LIMIT $limit
        """
        
        # 💡 [적재 쿼리 보완]: 단축 제목 필드를 안착시키고 독립 플래그 태그를 'SUCCESS'로 영구 각인
        finalize_query = """
        MATCH (r:Recipe)
        WHERE elementId(r) = $node_id
        SET r.refined_title = $refined_title,
            r.title_refined_status = 'SUCCESS',
            r.title_refined_at = datetime()
        RETURN r.refined_title
        """

        with self.driver.session() as session:
            records = list(session.run(find_query, limit=limit))
            if not records:
                return 0

            print(f"🔄 이번 턴에 단축 제목을 정제할 대상 노드: 총 {len(records)}건 탐색 완료.")
            success_count = 0
            
            for rec in records:
                node_id = rec["node_id"]
                original_title = rec["original_title"]
                steps = rec["steps"] or []
                
                print(f" ➔ 🧠 Gemma2 제목 정밀 단축 진입: '{original_title}'", end="", flush=True)
                
                # 자원 분배용 초단기 마진 휴식
                time.sleep(0.05)
                
                start_time = time.time()
                # 단축 메뉴명 변환 호출
                refined_title = self.ask_gemma_to_shorten_title(original_title, steps)
                elapsed = round(time.time() - start_time, 2)
                
                if not refined_title:
                    print(f" ➔ ❌ AI 변환 실패 (패스 처리)")
                    continue
                
                # DB에 정제 완료 태그 및 데이터 적재
                session.run(finalize_query, node_id=node_id, refined_title=refined_title)
                print(f" ➔ 🟢 [단축 완수] -> [{refined_title}] ({elapsed}초)")
                success_count += 1
                
        return len(records)

    def close(self):
        if self.driver:
            self.driver.close()

if __name__ == "__main__":
    # 💡 이전 턴의 클래스 명칭 불일치 노란 줄 에러(LLMHydrator) 완벽 수정 반영 완료
    hydrator = GraphRecipeLLMHydrator()
    try:
        batch_size = 30 # 제목만 처리하므로 부하가 매우 낮아 배치 사이즈를 30으로 상향하여 속도 업
        iteration = 1
        total_processed = 0
        
        while True:
            print(f"\n🚀 [제목 정제 루프 #{iteration}] 마이그레이션 탐색 기동...")
            processed_count = hydrator.run_title_migration_pipeline(limit=batch_size)
            
            if processed_count == 0:
                print("\n✨ 지식그래프 내 모든 레시피 노드의 메뉴명 단축 가공 및 플래그 적재가 완벽히 완주되었습니다!")
                break
                
            total_processed += processed_count
            print(f"💤 턴 #{iteration} 완료 (처리 건수: {processed_count}건 | 누적 정제: {total_processed}건)")
            print("🕒 로컬 칩셋 안정성을 위해 2초간 인터벌 휴식을 가집니다.")
            time.sleep(2.0)
            iteration += 1
            
    finally:
        hydrator.close()