"""
FILE: src/processor/models.py
ROLE: 정제된 재료 구조(Base+State)를 지원하는 데이터 모델.
"""
from pydantic import BaseModel, Field
from typing import List, Optional

class IngredientDetail(BaseModel):
    raw_name: str         # 원문: "다진 마늘", "minced garlic"
    mapped_name: str      # LLM이 1차 정제했던 명칭
    base_name: str        # 사후 정제 핵심: "마늘" (노드가 될 이름)
    state: Optional[str]  # 사후 정제 핵심: "다진", "말린" (관계 속성이 될 값)
    numeric_value: float
    unit: str
    substitute: Optional[str] = None
    confidence_score: float = 1.0
    manual_review_required: bool = False

class RecipeSchema(BaseModel):
    menu_name: str
    category: str
    ingredients: List[IngredientDetail]
    instructions: List[str]
    servings: int = 1