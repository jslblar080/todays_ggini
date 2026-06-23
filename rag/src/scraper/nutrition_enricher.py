"""
FILE: nutrition_enricher.py
ROLE: 지식 그래프 내 모든 식재료의 100g당 영양성분(칼로리, 탄단지)을 Ollama를 통해 전수 조사 및 적재
"""
import os
import time
import json
import re
from neo4j import GraphDatabase
from langchain_ollama import OllamaLLM
from dotenv import load_dotenv

load_dotenv()

class NutritionEnricher:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"), 
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "your_password"))
        )
        # 영양소 추정을 위한 Ollama 설정
        self.llm = OllamaLLM(model="llama3", temperature=0)

    def fetch_nutrition_from_ai(self, ingredient_name: str) -> dict:
        """Ollama를 한국 식품영양성분 전문가로 페르소나 설정하여 데이터 추출"""
        prompt = f"""
        You are a South Korean food nutrition database expert.
        Analyze the ingredient '{ingredient_name}' and provide its nutritional facts per 100g.
        
        Return ONLY a strict JSON object with the following keys. No conversational text, no markdown block.
        {{
          "calories": (kcal, float or int),
          "carbohydrate": (g, float or int),
          "protein": (g, float or int),
          "fat": (g, float or int)
        }}
        JSON:"""
        
        default_value = {"calories": 0, "carbohydrate": 0, "protein": 0, "fat": 0}
        try:
            res = self.llm.invoke(prompt).strip()
            # JSON만 추출하기 위한 정해진 방어 로직
            json_match = re.search(r'\{.*\}', res, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                # 수치 데이터 무결성 확보 (음수 방지 및 실수 변환)
                return {
                    "calories": max(0.0, float(data.get("calories", 0))),
                    "carbohydrate": max(0.0, float(data.get("carbohydrate", 0))),
                    "protein": max(0.0, float(data.get("protein", 0))),
                    "fat": max(0.0, float(data.get("fat", 0)))
                }
            return default_value
        except Exception as e:
            print(f"   ❌ AI 영양소 분석 실패 ({ingredient_name}): {e}")
            return default_value

    def enrich_ingredients(self):
        with self.driver.session() as session:
            # 영양 정보가 비어있는 식재료 추출
            print("🚀 영양성분 전수 조사를 시작합니다.")
            query = """
            MATCH (i:Ingredient)
            WHERE i.name IS NOT NULL AND i.name <> '물' AND i.name <> ''
            RETURN i.name AS name
            """
            result = session.run(query)
            
            for record in result:
                name = record['name']
                print(f"📊 영양가 분석 중: {name}")
                
                nutrition = self.fetch_nutrition_from_ai(name)
                
                # Neo4j 식재료 노드에 100g당 영양가 정보 이식
                session.run("""
                    MATCH (i:Ingredient {name: $name})
                    SET i.calories_per_100g = $calories,
                        i.carbo_per_100g = $carbohydrate,
                        i.protein_per_100g = $protein,
                        i.fat_per_100g = $fat,
                        i.nutrition_updated = datetime()
                """, name=name, **nutrition)
                
                print(f"   ✅ {name} (100g당) -> 칼로리: {nutrition['calories']}kcal | 탄: {nutrition['carbohydrate']}g | 단: {nutrition['protein']}g | 지: {nutrition['fat']}g")
                time.sleep(0.5) # 로컬 LLM 과열 방지

    def close(self):
        self.driver.close()

if __name__ == "__main__":
    enricher = NutritionEnricher()
    try:
        enricher.enrich_ingredients()
    finally:
        enricher.close()