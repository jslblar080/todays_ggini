import json
import re
from typing import Optional, Any, List
from langchain_ollama import OllamaLLM
from src.processor.models import RecipeSchema

class RecipeRefiner:
    def __init__(self, model_name: str = "llama3"):
        self.llm = OllamaLLM(model=model_name, temperature=0, format="json")

    def _clean_name(self, name: str) -> str:
        """물리적 노이즈 제거 및 표준화"""
        if not name: return "알수없음"
        # 괄호 및 내용 제거, 영문 제거, 사이시옷 교정
        name = re.sub(r'\(.*\)', '', name)
        name = re.sub(r'[a-zA-Z]', '', name)
        name = name.replace("고춧", "고추").replace("후춧", "후추").replace("깻잎잎", "깻잎").replace("들깻잎", "들깨잎")
        return name.strip()

    def _ensure_string_list(self, raw_list: Any) -> List[str]:
        if not isinstance(raw_list, list): return []
        return [str(item.get("text") if isinstance(item, dict) else item) for item in raw_list]

    def refine_recipe_text(self, raw_menu: str, raw_ingredients_text: str, raw_instructions: str) -> Optional[RecipeSchema]:
        prompt = f"""
        당신은 대한민국 요리 지식 그래프 전문가입니다. 반드시 한국어로 정제된 JSON을 출력하세요.

        [명령]
        1. category: 메뉴명을 보고 [한식/중식/일식/양식]과 [밥/국/반찬/일품/후식]을 조합해 직접 추론하세요.
        2. ingredients: 영문은 번역하고, 모든 필드(base_name, state, numeric_value, unit, substitute)를 반드시 포함하세요.
        3. instructions: 모든 조리 단계를 생략 없이 상세히 기록하세요. (최소 5단계 이상)

        [구조]
        {{
            "menu_name": "{raw_menu}",
            "category": "추론된 카테고리",
            "ingredients": [
                {{
                    "raw_name": "원문재료명",
                    "mapped_name": "표준명",
                    "base_name": "본질명",
                    "state": "상태",
                    "numeric_value": 0.0,
                    "unit": "g",
                    "substitute": "대체재료"
                }}
            ],
            "instructions": ["1단계 상세내용", "2단계 상세내용", "..."]
        }}

        [데이터]
        메뉴: {raw_menu} / 재료: {raw_ingredients_text} / 조리법: {raw_instructions}
        """
        
        try:
            response_text = self.llm.invoke(prompt)
            data_dict = json.loads(response_text)
            
            # --- [강력한 데이터 보정 및 에러 방어] ---
            
            # 1. 메뉴명 및 카테고리 보정
            data_dict["menu_name"] = data_dict.get("menu_name") or raw_menu
            if isinstance(data_dict.get("category"), list):
                data_dict["category"] = ", ".join(data_dict["category"])
            if not data_dict.get("category") or data_dict["category"] == "추론결과":
                data_dict["category"] = "기타, 일품"

            # 2. 재료 필드 누락 및 노이즈 보정
            if "ingredients" in data_dict:
                for ing in data_dict["ingredients"]:
                    # 물리적 노이즈 제거 적용
                    raw_base = ing.get("base_name") or ing.get("mapped_name") or "알수없음"
                    cleaned_base = self._clean_name(raw_base)
                    
                    ing["base_name"] = cleaned_base
                    ing["mapped_name"] = ing.get("mapped_name") or cleaned_base
                    ing["raw_name"] = ing.get("raw_name") or cleaned_base
                    ing["state"] = str(ing.get("state") or "보통")
                    ing["unit"] = str(ing.get("unit") or "g")
                    ing["substitute"] = str(ing.get("substitute") or "없음")
                    
                    if ing.get("numeric_value") is None:
                        ing["numeric_value"] = 0.0
            
            # 3. 조리법 보정
            if "instructions" in data_dict:
                data_dict["instructions"] = self._ensure_string_list(data_dict["instructions"])
                if len(data_dict["instructions"]) < 2:
                    data_dict["instructions"] = [raw_instructions[:300]]
            else:
                data_dict["instructions"] = [raw_instructions[:300]]

            return RecipeSchema(**data_dict)
            
        except Exception as e:
            print(f" [!] 정제 실패 ({raw_menu}): {e}") 
            return None