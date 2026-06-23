"""
FILE: graph_healer.py
ROLE: Ollama LLM을 이용해 instructions에서 실제 재료를 추출, 오염된 지식 그래프 관계(id: 392)를 전면 복구
"""
import os
import time
import json
import re
from neo4j import GraphDatabase
from langchain_ollama import OllamaLLM
from dotenv import load_dotenv

load_dotenv()

class GraphHealer:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"), 
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )
        self.llm = OllamaLLM(model="llama3", temperature=0)

    def extract_ingredients_from_steps(self, menu_name: str, steps: list) -> list:
        """조리법 텍스트를 분석하여 실제 사용된 식재료 단어만 추출"""
        steps_text = " ".join(steps)
        prompt = f"""
        Recipe Name: {menu_name}
        Instructions: {steps_text}
        
        Extract all core raw food ingredients used in this recipe as a simple Korean word list.
        Exclude actions, units, or kitchenware. (e.g., "소고기", "배추", "콩나물", "북어채")
        
        Return ONLY a strict JSON array of strings. No explanation.
        Example: ["소고기", "배추", "깻잎"]
        JSON:"""
        
        try:
            res = self.llm.invoke(prompt).strip()
            json_match = re.search(r'\[.*\]', res, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except:
            return []

    def heal_database(self):
        with self.driver.session() as session:
            # 1. 오염된 933개의 메뉴와 instructions 로드
            query = """
            MATCH (m:Menu)-[r:REQUIRES]->(i:Ingredient)
            WHERE i.name = "" OR i.name IS NOT NULL
            RETURN m.name AS menu_name, m.instructions AS instructions, elementId(m) as menu_id
            """
            result = session.run(query)
            
            # 중복 방지를 위해 메모리에 할당
            records = [{"id": r["menu_id"], "name": r["menu_name"], "steps": r["instructions"]} for r in result]
            print(f"🏥 총 {len(records)}개의 오염된 메뉴 치료 작업을 시작합니다.")

            for rec in records:
                if not rec["steps"]: continue
                print(f"🔮 '{rec['name']}' 레시피 분석 중...")
                
                # AI를 통해 진짜 재료 명사 추출
                real_ingredients = self.extract_ingredients_from_steps(rec["name"], rec["steps"])
                
                if real_ingredients:
                    print(f"   ✨ 추출된 진짜 재료: {real_ingredients}")
                    
                    # 2. 기존 유령 노드(id:392)와의 잘못된 관계선만 도려내기
                    session.run("""
                        MATCH (m:Menu)-[r:REQUIRES]->(i:Ingredient)
                        WHERE elementId(m) = $menu_id AND (i.name = "" OR i.name IS NULL)
                        DELETE r
                    """, menu_id=rec["id"])
                    
                    # 3. 진짜 재료 노드를 생성(MERGE)하고 메뉴와 올바르게 재연결
                    for ing_name in real_ingredients:
                        if len(ing_name.strip()) == 0: continue
                        session.run("""
                            MATCH (m:Menu) WHERE elementId(m) = $menu_id
                            MERGE (i:Ingredient {name: $ing_name})
                            MERGE (m)-[r:REQUIRES]->(i)
                            ON CREATE SET r.numeric_value = 100.0, r.unit = "g" // 기본 용량 빌드
                        """, menu_id=rec["id"], ing_name=ing_name.strip())
            
            # 4. 마지막으로 아무 데도 연결 안 된 유령 노드(id: 392) DB에서 완전히 삭제
            session.run("MATCH (i:Ingredient) WHERE i.name = '' OR i.name IS NULL DETACH DELETE i")
            print("🎉 지식 그래프 수술이 완료되었습니다! 유령 노드가 제거되었습니다.")

    def close(self):
        self.driver.close()

if __name__ == "__main__":
    healer = GraphHealer()
    try:
        healer.heal_database()
    finally:
        healer.close()