"""
FILE: graph_category_updater.py
ROLE: [비용 0원 데이터 재활용] 기존에 적재된 Recipe 노드를 탐색하여 
      카테고리(Category) 노드만 실시간으로 수정/보완하는 마이그레이션 엔진
"""
import os
import json
import time
import requests
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# 카테고리 추론에만 집중하도록 극도로 콤팩트하게 설계된 프롬프트
SYSTEM_PROMPT = """
너는 요리 레시피 제목을 보고 이 요리가 어느 카테고리에 속하는지 분류하는 데이터 엔지니어다.
반드시 다른 설명이나 마크다운 따옴표를 절대 하지 말고, 오직 지정된 JSON 구조로만 답변하라.

[분류 규칙]
레시피 제목을 기반으로 {한식, 중식, 일식, 양식, 분식, 디저트, 다이어트, 기타} 중 가장 잘 어울리는 카테고리를 한 단어로 선택하라.

[출력 JSON 포맷]
{
  "category": "추론된 카테고리 한 단어"
}
"""

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

class GraphCategoryUpdater:
    def __init__(self):
        self.db_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "gemma2:9b"

    def get_recipes_without_category(self):
        """💡 기존 DB에서 카테고리가 연결되지 않은 레시피만 골라서 가져옴 (수정 타겟 추출)"""
        cypher = """
        MATCH (r:Recipe)
        WHERE NOT (r)-[:BELONGS_TO]->(:Category)
        RETURN r.id AS id, r.title AS title
        """
        with self.db_driver.session() as session:
            result = session.run(cypher)
            return [{"id": record["id"], "title": record["title"]} for record in result]

    def query_local_ollama(self, recipe_title):
        payload = {
            "model": self.model_name,
            "prompt": f"{SYSTEM_PROMPT}\n\n레시피 제목: {recipe_title}",
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1}
        }
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=30)
            if response.status_code == 200:
                res_json = response.json()
                raw_ai_text = res_json.get("response", "{}").strip()
                return json.loads(raw_ai_text)
        except:
            return None
        return None

    def update_category(self, recipe_id, category_name):
        """💡 기존 레시피 노드에 카테고리를 실시간으로 매핑/수정하는 함수"""
        cypher = """
        MERGE (c:Category {name: $category_name})
        WITH c
        MATCH (r:Recipe {id: $recipe_id})
        MERGE (r)-[:BELONGS_TO]->(c)
        """
        with self.db_driver.session() as session:
            session.run(cypher, recipe_id=str(recipe_id), category_name=category_name)

    def run_migration(self):
        targets = self.get_recipes_without_category()
        if not targets:
            print("✨ 이미 모든 레시피에 카테고리가 올바르게 반영되어 있습니다!")
            return

        print(f"🛠️ [데이터 수정 가동] 총 {len(targets)}개의 레시피 노드에 카테고리 추가 적용을 시작합니다.")
        updated_count = 0

        for idx, recipe in enumerate(targets, 1):
            print(f"🔄 [{idx}/{len(targets)}] ID: {recipe['id']} | 제목: {recipe['title']} ➔ 카테고리 분석 중...", end="", flush=True)
            
            ai_res = self.query_local_ollama(recipe["title"])
            if ai_res and "category" in ai_res:
                category = ai_res["category"]
                self.update_db_category(recipe["id"], category)
                updated_count += 1
                print(f" 🟢 [{category}] 매핑 완료")
            else:
                print(" ⚠️ AI 무응답 패스")

        print(f"\n🎉 [마이그레이션 완료] 총 {updated_count}개의 레시피 데이터 수정 성공!")

    def update_db_category(self, recipe_id, category):
        cypher = """
        MERGE (c:Category {name: $category})
        WITH c
        MATCH (r:Recipe {id: $recipe_id})
        MERGE (r)-[:BELONGS_TO]->(c)
        """
        with self.db_driver.session() as session:
            session.run(cypher, recipe_id=str(recipe_id), category=category)

    def close(self):
        if self.db_driver: self.db_driver.close()

if __name__ == "__main__":
    updater = GraphCategoryUpdater()
    try:
        updater.run_migration()
    finally:
        updater.close()