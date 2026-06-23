"""
FILE: graph_nutrient_analyzer.py
ROLE: [비용 0원 완벽 통제] 로컬 gemma2:9b 모델을 활용하여 
      지식그래프 내 모든 Ingredient 노드의 100g당 영양성분을 추론하고 
      실시간 수정 시간(DateTime)을 주입하는 마이그레이션 엔진
"""
import os
import json
import time
import requests
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# 💡 영양성분 4대 지표(칼로리, 탄, 단, 지) 추론에 최적화된 마스터 프롬프트
SYSTEM_PROMPT = """
너는 식재료 이름을 보고, 해당 식재료의 '가공되지 않은 상태의 100g당 표준 영양성분'을 추론하는 데이터 과학자이자 영양사다.
반드시 다른 설명이나 마크다운 따옴표를 절대 하지 말고, 오직 지정된 JSON 구조로만 답변하라.

[분역 및 추론 규칙]
1. 모든 수치의 기준은 해당 식재료 '100g' 당 기준이다.
2. 수치는 소수점 첫째 자리까지의 실수(Float)로만 표현하라.
3. 정확한 수치를 알기 어려운 특이 식재료라면, 네가 가진 지식을 총동원하여 가장 근접한 농축산물 분류의 평균 데이터로 추론하여 채워라.

[출력 JSON 포맷]
{
  "calories_per_100g": 120.5,
  "carbo_per_100g": 15.2,
  "protein_per_100g": 8.4,
  "fat_per_100g": 3.1
}
"""

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

class GraphNutrientAnalyzer:
    def __init__(self):
        self.db_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "gemma2:9b"

    def get_target_ingredients(self):
        """💡 5,862개 데이터 중 영양성분이 아직 없거나, 과거에 갱신되지 않은 노드만 추출 (이어하기 지원)"""
        cypher = """
        MATCH (i:Ingredient)
        WHERE i.calories_per_100g IS NULL 
           OR i.nutrient_last_updated IS NULL
        RETURN i.name AS name
        """
        with self.db_driver.session() as session:
            result = session.run(cypher)
            return [record["name"] for record in result if record["name"]]

    def query_local_ollama(self, ingredient_name):
        """💡 Ollama API를 호출하여 안전하게 구조화된 영양소 데이터 반환"""
        prompt_content = f"{SYSTEM_PROMPT}\n\n분석할 식재료 명칭: {ingredient_name}"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt_content,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1}
        }
        
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=45)
            if response.status_code == 200:
                res_json = response.json()
                raw_ai_text = res_json.get("response", "{}").strip()
                
                if raw_ai_text.startswith("```"):
                    raw_ai_text = raw_ai_text.replace("```json", "").replace("```", "").strip()
                    
                return json.loads(raw_ai_text)
        except Exception:
            return None
        return None

    def update_ingredient_nutrients(self, name, nutrients):
        """💡 [구분자 핵심 수립] 4대 영양소와 함께 시, 분, 초, 밀리초까지 포함된 Neo4j 표준 datetime() 주입"""
        cypher = """
        MATCH (i:Ingredient {name: $name})
        SET i.calories_per_100g = $calories,
            i.carbo_per_100g = $carbo,
            i.protein_per_100g = $protein,
            i.fat_per_100g = $fat,
            i.nutrient_last_updated = datetime() // 연, 월, 일, 시, 분, 초, 타임존 자동 각인
        """
        with self.db_driver.session() as session:
            session.run(
                cypher,
                name=name,
                calories=float(nutrients.get("calories_per_100g", 0)),
                carbo=float(nutrients.get("carbo_per_100g", 0)),
                protein=float(nutrients.get("protein_per_100g", 0)),
                fat=float(nutrients.get("fat_per_100g", 0))
            )

    def run_analysis(self):
        targets = self.get_target_ingredients()
        total_targets = len(targets)
        
        if total_targets == 0:
            print("✨ 모든 식재료 노드에 이미 영양성분 및 타임스탬프가 완벽하게 동기화되어 있습니다!")
            return

        print(f"📦 [로컬 gemma2:9b 영양소 분석 모드 가동] 총 {total_targets}개의 식재료 분석을 시작합니다.")
        success_count = 0

        for idx, name in enumerate(targets, 1):
            print(f"🔄 [{idx}/{total_targets}] '{name}' 영양소 인공지능 분석 중...", end="", flush=True)
            
            # CPU/GPU 열화 방지 및 트래픽 완충을 위한 초단기 휴지기
            time.sleep(0.05)
            
            nutrients = self.query_local_ollama(name)
            if nutrients:
                try:
                    self.update_ingredient_nutrients(name, nutrients)
                    success_count += 1
                    print(f" ➔ 🟢 [반영완료] Cal: {nutrients.get('calories_per_100g')}kcal | 탄: {nutrients.get('carbo_per_100g')}g | 단: {nutrients.get('protein_per_100g')}g | 지: {nutrients.get('fat_per_100g')}g")
                except Exception as e:
                    print(f" ➔ ❌ DB 주입 실패 패스 ({e})")
            else:
                print(" ➔ ⚠️ AI 추론 실패 패스")

        print(f"\n🎉 [대장정 완수] 총 {success_count}개 식재료 노드에 영양소 스펙트럼 및 타임스탬프 수정 주입 완료!")

    def close(self):
        if self.db_driver: self.db_driver.close()

if __name__ == "__main__":
    analyzer = GraphNutrientAnalyzer()
    try:
        analyzer.run_analysis()
    finally:
        analyzer.close()