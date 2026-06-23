"""
FILE: src/scraper/collector.py
ROLE: 식약처 API 수집 및 파이프라인 제어
"""
import os
import requests
from dotenv import load_dotenv
from src.processor.refiner import RecipeRefiner

load_dotenv()

class RecipePipeline:
    def __init__(self):
        self.api_key = os.getenv("FOOD_SAFETY_API_KEY")
        self.base_url = "http://openapi.foodsafetykorea.go.kr/api"
        self.refiner = RecipeRefiner()

    def fetch_raw_recipes(self, start_idx: int, end_idx: int):
        if not self.api_key:
            return []
        endpoint = f"/{self.api_key}/COOKRCP01/json/{start_idx}/{end_idx}"
        response = requests.get(self.base_url + endpoint)
        if response.status_code == 200:
            return response.json().get('COOKRCP01', {}).get('row', [])
        return []

    def run_pipeline(self, start: int, end: int):
        raw_data = self.fetch_raw_recipes(start, end)
        refined_results = []
        for item in raw_data:
            menu_name = item.get('RCP_NM')
            ingredients_text = item.get('RCP_PARTS_DTLS')
            # MANUAL 필드 전체 취합
            manuals = [item.get(f'MANUAL{i:02d}').strip() for i in range(1, 21) if item.get(f'MANUAL{i:02d}')]
            full_instructions = "\n".join(manuals)
            
            refined_recipe = self.refiner.refine_recipe_text(menu_name, ingredients_text, full_instructions)
            if refined_recipe:
                refined_results.append(refined_recipe)
        return refined_results