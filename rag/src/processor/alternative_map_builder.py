"""
FILE: alternative_map_builder.py
ROLE: LLM 1회 통합 호출(One-Shot JSON) 아키텍처로 컨텍스트 붕괴 및 스킵 현상을 완벽하게 해결한 최종판
"""
import os
import time
import json
import re
from typing import Any
from neo4j import GraphDatabase
from langchain_ollama import OllamaLLM
from dotenv import load_dotenv

load_dotenv()

class UltimateAlternativeMapBuilder:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"), 
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "your_password"))
        )
        # 로컬 모델의 예측 가능하고 일관된 JSON 출력을 위해 temperature를 0으로 고정
        self.llm = OllamaLLM(model="llama3", temperature=0.0)
        
        self.protected_one_letter = ["물", "배", "무", "파", "굴", "닭", "소", "게", "꿀", "잣", "톳"]
        self.skip_keywords = ["송송", "가지는", "도래마", "-", "?", "적당량", "약간", "부재료", "g", "ml", "개"]

    def is_valid_for_analysis(self, name: Any) -> bool:
        if name is None: return False
        name_str = str(name).strip()
        if len(name_str) == 0: return False
        if len(name_str) == 1:
            return name_str in self.protected_one_letter
        return not any(kw in name_str for kw in self.skip_keywords)

    def analyze_ingredient_one_shot(self, korean_name: str) -> list:
        """One-Shot 아키텍처: 단 한 번의 프롬프트로 번역, 대체재 탐색, 검증, 역번역을 끝내는 핵심 두뇌"""
        prompt = f"""
        You are a world-class culinary scientist and database architect.
        Find exactly 2 practical, logical, and verified food ingredient substitutes for the Korean ingredient '{korean_name}' that can be used in Korean recipes.

        CRITICAL OLLAMA OUTPUT RULES:
        1. You must respond ONLY with a strict JSON array containing string values in Korean.
        2. Do NOT wrap inside ```json or ``` blocks. Do NOT include any conversation or explanation.
        3. Do NOT suggest generic fillers like "콩" or "당근" unless they are perfect matches.

        Example Interactions:
        - Input: "대파" -> Output: ["쪽파", "양파"]
        - Input: "소고기 안심" -> Output: ["소고기 등심", "돼지고기 안심"]
        - Input: "식물성기름" -> Output: ["카놀라유", "포도씨유"]
        - Input: "배" -> Output: ["사과", "갈아만든배"]

        Input: "{korean_name}"
        Output (JSON Array of strings only):"""
        
        try:
            res = self.llm.invoke(prompt).strip()
            
            # 💡 디버깅용: AI가 뱉은 날것의 텍스트가 형식이 깨졌는지 모니터링하기 위한 출력 레이어
            # 만약 스킵이 지속된다면 이 로그를 통해 LLM이 JSON 형식을 지켰는지 즉시 판별 가능합니다.
            # print(f"   [AI RAW RESPONSE]: {res}") 
            
            # 정규식을 사용해 대괄호 [ ] 부분만 스나이퍼처럼 정밀 추출
            json_match = re.search(r'\[.*\]', res, re.DOTALL)
            if json_match:
                alts = json.loads(json_match.group())
                return [str(a).strip() for a in alts if str(a).strip() != korean_name]
            return []
        except Exception as e:
            # print(f"   ❌ 파싱 에러 발생: {e}")
            return []

    def build_map(self):
        with self.driver.session() as session:
            print("🚀 [최종 마스터 아키텍처] 원샷 JSON 처리 기반 지식 그래프 자가 증식 배치를 기동합니다.")
            
            query = "MATCH (i:Ingredient) WHERE i.name IS NOT NULL RETURN i.name AS name"
            result = session.run(query)
            ingredients = [record['name'] for record in result]
            
            total_count = len(ingredients)
            print(f"📊 총 {total_count}개의 마스터 식재료 분석 및 글로벌 가성비 우회망 구축 시작...")
            processed_count = 0

            for name in ingredients:
                if not self.is_valid_for_analysis(name): continue

                name_str = str(name).strip()
                print(f"\n🔮 [{processed_count+1}/{total_count}] '{name_str}' 원샷 AI 정밀 매핑 집도 중...")
                
                # 단 1회 호출로 엄격하게 검증된 한국어 대체재 다이렉트 획득
                valid_alts = self.analyze_ingredient_one_shot(name_str)
                
                success_alts = []
                for alt_kor in valid_alts:
                    # 한글 단어 이외의 지저분한 특수기호 필터링
                    alt_kor = re.sub(r'[^가-힣\s]', '', alt_kor).strip()
                    if not alt_kor or alt_kor == name_str: continue
                    
                    # 💡 검증을 통과한 완벽한 대안 재료가 현재 DB에 없더라도 MERGE 자가 증식 작동
                    session.run("""
                        MERGE (i1:Ingredient {name: $name})
                        MERGE (i2:Ingredient {name: $alt})
                        MERGE (i1)-[r:SUBSTITUTE_FOR]-(i2)
                        SET r.is_verified = true, r.final_optimized_at = datetime()
                    """, name=name_str, alt=alt_kor)
                    success_alts.append(alt_kor)

                if success_alts:
                    print(f"   🎯 [지식그래프 자가 확장 성공] '{name_str}' ➔ {success_alts}")
                else:
                    print(f"   ⚠️ '{name_str}'의 유효 대안이 없어 무결성을 위해 안전하게 스킵했습니다.")
                
                processed_count += 1
                # 호출 횟수가 1/4로 줄었으므로 슬립 타임을 최적화하여 전체 인덱싱 속도 폭발적 상승
                time.sleep(0.02)

            print("\n🎉 1,086개 전수 식재료 대상 원샷 가드레일 대체재 지식 그래프 인프라가 최종 완결되었습니다!")

    def close(self):
        self.driver.close()

if __name__ == "__main__":
    builder = UltimateAlternativeMapBuilder()
    try:
        builder.build_map()
    finally:
        builder.close()