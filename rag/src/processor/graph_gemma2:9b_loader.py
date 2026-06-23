"""
FILE: graph_gemma2:9b_loader.py
ROLE: [비용 0원 완벽 통제] 대용량 스트리밍 및 이어하기 모드를 지원하며,
      카테고리 분류 및 실물 상품 구매 링크(link) 전량 보존 적재가 가능한 엔진
"""
import os
import json
import time
import requests
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# 💡 출력 JSON 포맷 스펙에 link 속성을 강제 반영한 프롬프트
SYSTEM_PROMPT = """
너는 만개의 레시피 JSON 데이터를 Neo4j 지식그래프에 적재하기 위해 깨끗하게 정제하는 데이터 엔지니어다.
반드시 다른 설명이나 마크다운 따옴표를 절대 하지 말고, 오직 지정된 JSON 구조로만 답변하라.

[정제 필수 규칙]
1. 표준재료명: '사각어묵 4~5장' 등 수량/용량이 섞인 단어는 '어묵'처럼 순수 핵심 재료명 단어로 표준화하라.
2. 계량 수치화: 용량 단위를 분석하여 수치(Float)와 표준단위(g, ml, 개, 큰술, 작은술, 약간)로 분리하라. (계산 불가 시 value는 0, unit은 "약간")
3. 카테고리 추론: 레시피 제목과 재료를 기반으로 이 요리가 {한식, 중식, 일식, 양식, 분식, 디저트, 다이어트, 기타} 중 어디에 속하는지 한 단어로 추론하라.
4. 쿠팡 광고 컷오프: 요리와 관계없는 광고 상품은 버리고, 요리에 쓰이는 진짜 식재료 상품만 products 리스트에 매핑하라. 원천 데이터의 purchase_link 값을 반드시 link 필드에 보존하라.

[출력 JSON 포맷]
{
  "title": "레시피 제목",
  "category": "추론된 카테고리 한 단어",
  "servings": "몇인분 (모를 경우 빈 문자열)",
  "ingredients": [
    {
      "name": "표준재료명",
      "amount_value": 200.0,
      "amount_unit": "g",
      "raw_string": "사각어묵 4~5장 200g"
    }
  ],
  "products": [
    {
      "name": "매핑된_쿠팡상품명",
      "price": 7100,
      "delivery_type": "일반배송",
      "link": "원천 데이터의 실제 purchase_link 문자열"
    }
  ]
}
"""

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

class GraphOllamaPurifier:
    def __init__(self):
        self.db_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_file = os.path.abspath(os.path.join(base_dir, "../../data/raw_mankae_recipes.jsonl"))
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "gemma2:9b"

    def stream_unique_recipes(self):
        if not os.path.exists(self.input_file):
            print(f"❌ 원천 파일 경로 오류: {self.input_file}")
            return
            
        seen_ids = set()
        with open(self.input_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    rid = data.get("recipe_id")
                    if rid and rid not in seen_ids:
                        seen_ids.add(rid)
                        yield data
                except: 
                    continue

    def is_already_inserted(self, recipe_id):
        cypher = "MATCH (r:Recipe {id: $recipe_id}) RETURN count(r) AS cnt"
        with self.db_driver.session() as session:
            result = session.run(cypher, recipe_id=str(recipe_id))
            record = result.single()
            return record["cnt"] > 0 if record else False

    def execute_parameterized_queries(self, recipe_id, purified_data):
        if not purified_data: return 0
        
        lines_inserted = 0
        with self.db_driver.session() as session:
            # 1. Recipe 노드 생성
            recipe_cypher = """
            MERGE (r:Recipe {id: $recipe_id})
            SET r.title = $title, r.servings = $servings
            """
            session.run(recipe_cypher, recipe_id=str(recipe_id), title=purified_data.get("title", ""), servings=purified_data.get("servings", ""))
            lines_inserted += 1
            
            # 2. Category 노드 생성 및 연결
            category_name = purified_data.get("category", "기타")
            category_cypher = """
            MERGE (c:Category {name: $category_name})
            WITH c
            MATCH (r:Recipe {id: $recipe_id})
            MERGE (r)-[:BELONGS_TO]->(c)
            """
            session.run(category_cypher, recipe_id=str(recipe_id), category_name=category_name)
            lines_inserted += 1
            
            # 3. Ingredient 관계 생성
            for ing in purified_data.get("ingredients", []):
                ing_cypher = """
                MERGE (i:Ingredient {name: $name})
                WITH i
                MATCH (r:Recipe {id: $recipe_id})
                MERGE (r)-[rel:REQUIRES]->(i)
                SET rel.amount_value = $amount_value,
                    rel.amount_unit = $amount_unit,
                    rel.raw_string = $raw_string
                """
                session.run(ing_cypher, 
                            recipe_id=str(recipe_id),
                            name=ing.get("name"),
                            amount_value=float(ing.get("amount_value", 0)),
                            amount_unit=ing.get("amount_unit", "약간"),
                            raw_string=ing.get("raw_string", ""))
                lines_inserted += 1

            # 4. Product 관계 생성 (💡실제 구매 링크 매핑 구동)
            for prod in purified_data.get("products", []):
                prod_cypher = """
                MERGE (p:Product {name: $name})
                SET p.price = $price, 
                    p.delivery_type = $delivery_type,
                    p.link = $link
                WITH p
                MATCH (r:Recipe {id: $recipe_id})
                MERGE (r)-[rel:MATCHED_PRODUCT]->(p)
                """
                session.run(prod_cypher,
                            recipe_id=str(recipe_id),
                            name=prod.get("name"),
                            price=int(prod.get("price", 0)),
                            delivery_type=prod.get("delivery_type", "일반배송"),
                            link=prod.get("link", "https://www.coupang.com"))
                lines_inserted += 1
                
        return lines_inserted

    def query_local_ollama(self, recipe_data):
        prompt_content = f"{SYSTEM_PROMPT}\n\n변환할 원천 레시피 데이터:\n{json.dumps(recipe_data, ensure_ascii=False)}"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt_content,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1}
        }
        
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=90)
            if response.status_code == 200:
                res_json = response.json()
                raw_ai_text = res_json.get("response", "{}").strip()
                
                if raw_ai_text.startswith("```"):
                    raw_ai_text = raw_ai_text.replace("```json", "").replace("```", "").strip()
                    
                return json.loads(raw_ai_text)
        except Exception as e:
            print(f"\n❌ Ollama 통신 에러: {e}")
            return None
        return None

    def process_all_production(self):
        print(f"📦 [로컬 gemma2:9b] 카테고리 및 고유 주소 매핑 레이어 포함 무한 동력 가동")
        success_count = 0
        skip_count = 0
        idx = 0
        
        for recipe in self.stream_unique_recipes():
            idx += 1
            recipe_id = recipe['recipe_id']
            
            if self.is_already_inserted(recipe_id):
                skip_count += 1
                if skip_count % 100 == 0:
                    print(f"⏭️ [이어하기 탐색 완료] 현재까지 {skip_count}개 레시피 건너뜀... (누적 스캔: {idx}건)")
                continue

            print(f"🔄 [{idx}번째 라인] 레시피 ID: {recipe_id} 로컬 AI 정제 집도 중...", end="", flush=True)
            
            try:
                purified_json = self.query_local_ollama(recipe)
                if not purified_json:
                    print(" ➔ ⚠️ AI 무응답 패스")
                    continue
                    
                line_inserted = self.execute_parameterized_queries(recipe_id, purified_json)
                if line_inserted > 0:
                    success_count += 1
                    print(f" ➔ 🟢 적재 완료 (반영 쿼리: {line_inserted}줄 / 이번 세션 누적: {success_count}개)")
                else:
                    print(" ➔ ⚠️ 반영된 데이터 없음")
                    
            except json.JSONDecodeError:
                print(" ➔ ❌ AI 반환 포맷 파싱 에러 패스")
                continue
            except Exception as e:
                print(f" ➔ ❌ 에러 패스: {e}")
                continue

        print(f"\n🎉 [대장정 완수] 새로 적재: {success_count}개 / 기적재 패스: {skip_count}개 (총 {idx}건 처리 완료)")

    def close(self):
        if self.db_driver: self.db_driver.close()

if __name__ == "__main__":
    purifier = GraphOllamaPurifier()
    try:
        purifier.process_all_production()
    finally:
        purifier.close()