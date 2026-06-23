"""
FILE: graph_ingredient_classifier_gemma.py
ROLE: [비용 0원 최적화 - 데이터 오염 차단 종결본]
      지식그래프 내 unique한 Ingredient 노드들을 Gemma2를 통해 단 한 번만 분류하여 
      i.category 속성에 영구 박제하는 오프라인 오케스트레이터.
      - 에러 발생 시 '기본재료'로 오염시키는 버그를 제거하고 건너뛰기(Skip) 구조로 리팩토링.
      - Ollama 강제 인식을 위한 options 규격 및 타임아웃 보정 완수.
DEPENDENCY: pip install requests neo4j python-dotenv
"""
import os
import json
import time
import requests
from typing import Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

# 💡 Ollama API 설정
OLLAMA_BASE_URL = os.getenv("GEMMA_API_URL", "http://localhost:11434").replace("/api/generate", "").replace("/api/chat", "").rstrip("/")
LLM_API_URL = f"{OLLAMA_BASE_URL}/api/chat"
MODEL_NAME = "gemma2:9b"

class GraphIngredientClassifier:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def get_target_ingredients(self, limit: int = 100) -> list:
        """💡 category 속성이 비어있는 Ingredient 노드 추출"""
        query = """
        MATCH (i:Ingredient)
        WHERE i.category IS NULL
        RETURN i.name AS name, elementId(i) AS node_id
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [{"name": record["name"], "node_id": record["node_id"]} for record in result]

    def ask_gemma_to_classify(self, ingredient_name: str) -> Optional[str]:
        """💡 Gemma2에게 식재료 명을 던져 카테고리 추출 (실패 시 무조건 None 리턴으로 DB 오염 차단)"""
        system_instruction = """You are a Food-Tech data engineer and culinary expert.
Classify the given Korean ingredient name into EXACTLY one of the following four standardized categories.

[Standardized Categories]
1. "주재료" (Main ingredient: Meat, Seafood, Rice, Noodles, Main vegetables that form the core of the dish)
2. "부재료" (Sub-ingredient: Garnish, Sub-vegetables, Toppings, Eggs, Mushrooms, Tofu, etc.)
3. "양념/소스" (Condiments/Sauce: Soy sauce, Sugar, Salt, Oil, Vinegar, Sesame oil, Gochujang, Spices, Stock/Broth, Water)
4. "기본재료" (Default: If it's extremely ambiguous or doesn't fit any of the above)

[Strict Output Rules]
1. Return ONLY a valid JSON object matching the requested schema.
2. The 'category' field must contain exactly one of the four standardized category names: "주재료", "부재료", "양념/소스", or "기본재료".
3. Do not include any markdown, explanations, or backticks.

[Required JSON Schema Format]
{
  "category": "주재료"
}
Output (Strict JSON Object Only):"""

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Ingredient Name: {ingredient_name}"}
            ],
            "stream": False,
            "format": "json", # 정밀한 JSON 락 활성화
            "options": {
                "temperature": 0.1,
                "num_predict": 512,  # 식재료 카테고리는 짧으므로 VRAM 절약을 위해 타이트하게 튜닝
                "num_ctx": 4096
            }
        }

        try:
            response = requests.post(LLM_API_URL, json=payload, timeout=30)
            if response.status_code != 200:
                print(f"\n   ⚠️ [API HTTP 에러] Status: {response.status_code}")
                return None
                
            res_json = response.json()
            response_text = res_json.get("message", {}).get("content", "").strip()
            
            if response_text.startswith("```"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()

            data = json.loads(response_text)
            category = data.get("category", "").strip()
            
            # 허용된 표준 카테고리 검증 락
            if category in ["주재료", "부재료", "양념/소스", "기본재료"]:
                return category
                
            print(f"\n   ⚠️ [비표준 카테고리 노이즈 진입]: {category} -> 기본재료 강제 보정")
            return "기본재료"
            
        except json.JSONDecodeError:
            print(f"\n   ⚠️ [포맷 노이즈 발생] JSON 디코딩 실패. 날것의 응답: {response_text}")
            return None
        except Exception as e:
            print(f"\n   ❌ Ollama 연결 끊김 또는 예기치 못한 에러: {e}")
            return None

    def update_ingredient_category(self, node_id: str, category: str):
        """💡 식재료 노드에 카테고리를 저장하고 타임스탬프 기록"""
        query = """
        MATCH (i:Ingredient)
        WHERE elementId(i) = $node_id
        SET i.category = $category,
            i.category_updated_at = datetime()
        """
        with self.driver.session() as session:
            session.run(query, node_id=node_id, category=category)

    def run_batch_classification(self, batch_size: int = 50) -> int:
        targets = self.get_target_ingredients(limit=batch_size)
        if not targets:
            return 0
            
        print(f"🔄 이번 배치 타겟 식재료: 총 {len(targets)}건 가공 진입", flush=True)
        success_count = 0
        
        for idx, ing in enumerate(targets, 1):
            name = ing["name"]
            node_id = ing["node_id"]
            
            time.sleep(0.05) # 완충 마진
            
            start_time = time.time()
            category = self.ask_gemma_to_classify(name)
            elapsed = round(time.time() - start_time, 2)
            
            # 💡 [핵심 구출] AI 연산 실패 시 DB 수정을 생략(Skip)하여 데이터 순수성 보존
            if category is None:
                print(f"   ➔ ❌ [{idx:02d}/{len(targets):02d}] '{name}' 분류 실패 - DB 반영 생략 (다음 기회에 재시도)")
                continue
                
            self.update_ingredient_category(node_id, category)
            print(f"   ➔ 🏷️ [{idx:02d}/{len(targets):02d}] '{name}' 분류 완수: [{category}] ({elapsed}초)", flush=True)
            success_count += 1
            
        return success_count

    def close(self):
        if self.driver:
            self.driver.close()

if __name__ == "__main__":
    classifier = GraphIngredientClassifier()
    try:
        batch_size = 50
        iteration = 1
        total_processed = 0
        
        print("============================================================")
        print("🚀 [오프라인 정제 엔진] Gemma2 식재료 카테고리화 일괄 매핑 기동")
        print("============================================================")
        
        while True:
            print(f"\n[Turn #{iteration}] DB 미분류 식재료 조회 중...", flush=True)
            processed = classifier.run_batch_classification(batch_size=batch_size)
            
            if processed == 0:
                # 💡 안전핀 장착: 진짜 노드가 없는 건지, 이번 턴에 전부 실패한 건지 대기열 재순회 검증
                remaining = classifier.get_target_ingredients(limit=1)
                if not remaining:
                    print("\n✨ 지식그래프 내의 모든 Ingredient 노드가 성공적으로 표준화/카테고리화 되었습니다!", flush=True)
                    break
                else:
                    print("\n⚠️ 미분류 식재료가 남아있으나 현재 턴에서 모두 실패했습니다. Ollama 상태를 확인하세요.")
                    print("🕒 인프라 안정을 위해 10초 휴식 후 다음 턴으로 강제 이동합니다.")
                    time.sleep(10.0)
                    continue
                
            total_processed += processed
            print(f"💤 Turn #{iteration} 완료 (이번 턴 성공: {processed}건 | 누적: {total_processed}건)", flush=True)
            print("🕒 시스템 열화 방지를 위해 2초간 일시 휴식합니다.", flush=True)
            time.sleep(2.0)
            iteration += 1
            
    finally:
        classifier.close()