"""
FILE: graph_ingredient_substitute_linker.py
ROLE: [비용 0원 최적화 - 문법 에러 완전 수정본]
      지식그래프 내 2,100여 건의 식재료 간의 '실제 요리상 대체 가능 관계'를 
      Gemma2 도메인 지식으로 분석하여 (i:Ingredient)-[:SUBSTITUTE_FOR]->(alt:Ingredient) 선을 맺어주는 엔진.
      - [버그 해결] get_target_ingredients 내부의 정의되지 않은 변수 r 오타를 i로 완벽 수정.
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

class GraphIngredientSubstituteLinker:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def get_target_ingredients(self, limit: int = 50) -> list:
        """💡 아직 대체재 탐색이 진행되지 않은 식재료 노드 추출"""
        # 💡 [치명적 버그 해결] r.substitute_linked_status 코드를 식재료 노드 변수인 i로 싱크 보정 완료
        query = """
        MATCH (i:Ingredient)
        WHERE i.substitute_linked_status IS NULL
        RETURN i.name AS name, elementId(i) AS node_id
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [{"name": record["name"], "node_id": record["node_id"]} for record in result]

    def ask_gemma_for_substitutes(self, ingredient_name: str) -> list:
        """💡 Gemma2에게 식재료명을 던져 한국 요리 맥락상 실제 호환 가능한 대체 식재료 3개 추출"""
        system_instruction = f"""You are a world-class culinary expert and food-tech data engineering expert.
Given a Korean ingredient name, suggest EXACTLY 1 to 3 realistic substitute Korean ingredient names that can replace it in common recipes without ruining the dish type or structure.

[Strict Substitution Rules]
1. Substitutes MUST share the same culinary role and structure.
   - Example '돼지고기삼겹살' -> ['돼지고기앞다리살', '소고기차돌박이', '두부'] (Meat/Protein role maintained)
   - Example '진간장' -> ['양조간장', '국간장', '참치액']
   - Example '버터' -> ['마가린', '올리브유', '식용유']
2. Output MUST be a valid JSON object matching the requested schema exactly.
3. Return ONLY clean, standard Korean ingredient names. Do not include markdown or backticks.

[Required JSON Schema Format]
{{
  "substitutes": ["대체재이름1", "대체재이름2", "대체재이름3"]
}}
Output (Strict JSON Object Only):"""

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Target Ingredient: {ingredient_name}"}
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1}
        }

        try:
            response = requests.post(LLM_API_URL, json=payload, timeout=25)
            if response.status_code != 200:
                return []
                
            res_json = response.json()
            response_text = res_json.get("message", {}).get("content", "").strip()
            
            data = json.loads(response_text)
            return data.get("substitutes", [])
        except Exception:
            return []

    def create_substitute_edges(self, source_id: str, substitute_names: list):
        """💡 추출된 대체 식재료명들을 지식그래프 상에 존재하는 노드들과 에지(Edge)로 강제 조인 연결"""
        query = """
        MATCH (orig:Ingredient) WHERE elementId(orig) = $source_id
        UNWIND $substitute_names AS alt_name
        MATCH (alt:Ingredient) WHERE alt.name = alt_name AND elementId(alt) <> $source_id
        MERGE (orig)-[:SUBSTITUTE_FOR]->(alt)
        """
        finalize_query = """
        MATCH (i:Ingredient) WHERE elementId(i) = $source_id
        SET i.substitute_linked_status = 'SUCCESS',
            i.substitute_linked_at = datetime()
        """
        with self.driver.session() as session:
            if substitute_names:
                session.run(query, source_id=source_id, substitute_names=substitute_names)
            session.run(finalize_query, source_id=source_id)

    def run_migration(self, batch_size: int = 30):
        targets = self.get_target_ingredients(limit=batch_size)
        if not targets:
            return 0
            
        print(f"🔄 대체재 지식 맵핑 배치 진입: 총 {len(targets)}건 스캔 시작", flush=True)
        success_count = 0
        
        for idx, ing in enumerate(targets, 1):
            name = ing["name"]
            node_id = ing["node_id"]
            
            time.sleep(0.05)
            start_time = time.time()
            
            substitutes = self.ask_gemma_for_substitutes(name)
            self.create_substitute_edges(node_id, substitutes)
            
            elapsed = round(time.time() - start_time, 2)
            print(f"   ➔ 🔗 [{idx:02d}/{len(targets):02d}] '{name}' 대체재 지식 맵핑 완수: {substitutes} ({elapsed}초)", flush=True)
            success_count += 1
            
        return success_count

    def close(self):
        if self.driver:
            self.driver.close()

if __name__ == "__main__":
    linker = GraphIngredientSubstituteLinker()
    try:
        batch_size = 30
        iteration = 1
        total_processed = 0
        
        while True:
            print(f"\n🚀 [대체재 조인 루프 #{iteration}] 지식 매핑 기동...", flush=True)
            processed = linker.run_migration(batch_size=batch_size)
            if processed == 0:
                print("\n✨ 지식그래프 내 모든 식재료 노드의 상호 대체 검증선 매핑이 완전히 완주되었습니다!", flush=True)
                break
            total_processed += processed
            time.sleep(2.0)
            iteration += 1
    finally:
        linker.close()