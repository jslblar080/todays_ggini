"""
FILE: graph_recipe_llm_hydrator.py
ROLE: [조리법 정제 + 메뉴명 단축 통합 통합본] 
      - 평문 라인 파서 아키텍처를 유지하면서, 만개의레시피 특유의 미사여구와 광고성 제목을 
        '기사식당 돼지불백', '유자파운드케이크'처럼 핵심만 남긴 단축 메뉴명(refined_title)으로 동시 정제 및 적재합니다.
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

    def clean_raw_text_dynamic(self, text: str) -> str:
        """💡 [인코딩 노이즈 격리] 보이지 않는 공백 문자와 깨진 특수문자를 전처리 단계에서 소멸"""
        if not text:
            return ""
        text = " ".join(text.split())
        text = re.sub(r'[◆■▶▲➔✔💡⚠️❌➔💎🔥═\-=+#/\?,\.:;^$@\*\"~~]+', ' ', text)
        return text.strip()[:4000]

    def ask_gemma_to_hydrate_recipe(self, title: str, raw_text: str) -> tuple:
        """Gemma2에게 평문 형태로 답변을 유도하여 1) 단축 메뉴명과 2) 조리 순서 리스트를 동시에 반환받음"""
        if not raw_text or raw_text in ["NO_BODY_TEXT_FOUND", "BAD_RECIPE_ID"]:
            return None, []

        purified_context = self.clean_raw_text_dynamic(raw_text)

        # 💡 [핵심 프롬프트 튜닝]: 메뉴명 단축 규칙(Rules 1)과 조리 순서 규칙(Rules 2)을 명확히 분리하여 평문 출력을 요구합니다.
        system_instruction = f"""You are a Food-Tech data engineering expert and culinary database administrator.
Analyze the given recipe title [{title}] and its web source text to extract two things: 
1. A refined, short, and clear Korean menu name (e.g., '간단하지만 중독성있게맛있는 간장파스타' -> '간장파스타', '<다이어트 건강식>초간단 닭가슴살 토마토 스튜' -> '닭가슴살 토마토 스튜').
2. Chronological cooking steps from the source text.

[Rules for Menu Name]
- Remove all buzzwords, brackets, icons, descriptions, and adjectives (e.g., 하트, 다이어트, 초간단, 신혼밥상, 밥도둑).
- Print the refined menu name on the very first line starting with "TITLE: ".

[Rules for Cooking Steps]
- Exclude ads, greetings, and metrics.
- Print each sequential action step on a new line starting exactly with "1. ", "2. ", "3. ".

Example Output:
TITLE: 간장파스타
1. 양파와 대파를 잘게 다집니다.
2. 양념장 재료를 넣고 잘 섞어 줍니다."""

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Source Text:\n{purified_context}"}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 1500,
                "num_ctx": 6144
            }
        }

        try:
            response = requests.post(LLM_API_URL, json=payload, timeout=60)
            if response.status_code != 200:
                return None, []
                
            res_json = response.json()
            response_text = res_json.get("message", {}).get("content", "").strip()
            
            if not response_text:
                return None, []

            if "```" in response_text:
                response_text = response_text.replace("```json", "").replace("```", "").strip()

            # 💡 [동적 파서 아키텍처 개정] 평문 텍스트 라인을 순회하며 TITLE 라인과 STEPS 라인을 분리 파싱
            refined_title = None
            steps = []
            
            for line in response_text.split('\n'):
                line = line.strip()
                
                # 1. 단축 제목 추출
                if line.startswith("TITLE:"):
                    refined_title = line.replace("TITLE:", "").strip()
                    # 혹시 남아있을 수 있는 따옴표 제거
                    refined_title = re.sub(r'[\'\"\[\]]', '', refined_title)
                    continue
                
                # 2. 조리 순서 추출
                if re.match(r'^\d+\.', line) and len(line) > 5:
                    steps.append(line)
            
            # 모델이 TITLE 태그를 빼먹었을 경우를 위한 방어 코드
            if not refined_title:
                refined_title = title[:15] # 원본에서 앞글자 일부만 강제 슬라이싱
                    
            return refined_title, steps

        except Exception as e:
            print(f"   ❌ 오케스트레이션 장애: {e}")
            return None, []

    def run_llm_hydration(self, limit: int = 10):
        print("============================================================")
        print("💡 [2단계: Gemma2 오케스트레이션 및 메뉴명 단축 + 조리 순서 적재 시작]")
        print("============================================================")
        
        find_query = """
        MATCH (r:Recipe)
        WHERE r.hydration_status = 'RAW_COLLECTED' AND r.raw_html_text IS NOT NULL
        RETURN elementId(r) as node_id, r.title as title, r.raw_html_text as raw_text
        LIMIT $limit
        """
        
        # 🟢 [Neo4j 마이그레이션 레이어 개정]: 원래 title은 원본 추적을 위해 유지하거나 덮어쓰고, 
        # 서비스용 refined_title 속성을 새롭게 노드에 영구 장착합니다.
        finalize_query = """
        MATCH (r:Recipe)
        WHERE elementId(r) = $node_id
        SET r.refined_title = $refined_title,
            r.steps = $steps,
            r.hydration_status = 'SUCCESS',
            r.hydrated_at = datetime()
        REMOVE r.raw_html_text
        RETURN r.refined_title
        """

        with self.driver.session() as session:
            records = list(session.run(find_query, limit=limit))
            if not records:
                return 0

            print(f"🔄 이번 턴에 AI가 정제할 대상 노드: 총 {len(records)}건 탐색 완료.")
            success_count = 0
            
            for rec in records:
                node_id = rec["node_id"]
                title = rec["title"]
                raw_text = rec["raw_text"]
                
                print(f" ➔ 🧠 Gemma2 가공 진입: '{title}'", end="", flush=True)
                
                time.sleep(0.05)
                
                start_time = time.time()
                # 단축 메뉴명과 순서를 동시에 획득
                refined_title, refined_steps = self.ask_gemma_to_hydrate_recipe(title, raw_text)
                elapsed = round(time.time() - start_time, 2)
                
                if not refined_steps or len(refined_steps) == 0 or not refined_title:
                    print(f" ➔ ❌ AI 정제 실패 (패스 처리)")
                    continue
                
                # DB 최종 반영
                session.run(finalize_query, node_id=node_id, refined_title=refined_title, steps=refined_steps)
                print(f" ➔ 🟢 [AI 가공 완수] [{refined_title}] 변환 및 {len(refined_steps)}단계 적재 완료! ({elapsed}초)")
                success_count += 1
                
        return len(records)

    def close(self):
        if self.driver:
            self.driver.close()

if __name__ == "__main__":
    hydrator = GraphRecipeLLMHydrator()
    try:
        batch_size = 20
        iteration = 1
        total_hydrated = 0
        
        while True:
            print(f"\n🚀 [배치 반복 턴 #{iteration}] 마이그레이션 탐색 기동...")
            processed_count = hydrator.run_llm_hydration(limit=batch_size)
            
            if processed_count == 0:
                print("\n✨ 모든 'RAW_COLLECTED' 상태 레시피 노드의 AI 정밀 가공 처리가 완전히 종결되었습니다!")
                break
                
            total_hydrated += processed_count
            print(f"💤 턴 #{iteration} 완료 (배치 크기: {processed_count}건 | 누적 가공: {total_hydrated}건)")
            print("🕒 로컬 GPU/API 및 DB 안정성을 확보하기 위해 3초간 인터벌 휴식을 가집니다.")
            time.sleep(3.0)
            iteration += 1
            
    finally:
        hydrator.close()