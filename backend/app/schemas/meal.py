from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from typing import List, Dict, Any, Optional

# ----------- 스타일 확정 전용 스키마 ---------------
class StyleSelectRequest(BaseModel):
    selected_style_id: str  # 예: "budget_first", "nutrition_balance" 등

# --- [AI 응답 구조 반영: Meal 레벨] ---

class Recipe(BaseModel):
    serving_size: int = Field(1, description="인분")
    cooking_time: int = Field(..., description="조리 시간(분)")
    steps: List[str] = Field(..., description="조리 단계")
    required_ingredients: List[str] = Field(..., description="필수 재료")
    optional_ingredients: List[Optional[str]] = Field(default_factory=list, description="선택 재료")
    substitution_ingredients: Dict[str, Any] = Field(default_factory=dict, description="대체 재료 정보")

class MealScores(BaseModel):
    budget: float
    nutrition: float
    preference: float
    difficulty: float
    diversity: float

class MealDetail(BaseModel):
    meal_order: int = Field(..., description="식사 순서 (1: 아침, 2: 점심...)")
    menu_id: int = Field(..., description="메뉴 고유 식별 번호")
    name: str = Field(..., description="메뉴 이름")
    category: str
    final_score: float = Field(..., description="모든 가중치를 합산한 최종 추천 점수")
    estimated_cost: int
    calories: int
    protein: float
    ingredients: List[str] = Field(..., description="전체 식재료 리스트 요약")
    ingredient_groups: List[str] = Field(..., description="포함된 식재료 군 (예: 식물성 단백질류, 채소류)")
    recipe: Recipe
    scores: MealScores = Field(..., description="항목별 세부 평가 점수")

class MealGenerateResponse(BaseModel):
    job_id: str
    estimated_seconds: int
    stages: List[str]

# ----------- 식단 확정 전용 스키마 ---------------
class MealConfirmResponse(BaseModel):
    plan_id: str
    start_date: date
    end_date: date
    duration_days: int
    total_price_per_plan: int
    average_calories_per_plan: int
    generated_at: datetime

# --- [AI 응답 구조 반영: Day 레벨] ---

class DailyMeals(BaseModel):
    day: int = Field(..., description="식단 계획 내 일차 (예: 1일차, 2일차)")
    meals: List[MealDetail]

class MealDetailItem(BaseModel):
    slot: int
    meal_id: str
    menu_name: str
    calories: int
    price: int
    image_url: Optional[str] = None

class DailyMealDetailResponse(BaseModel):
    date: date
    calories_per_day: int
    price_per_day: int
    meals: List[MealDetailItem]

# --- [AI 응답 전체 구조: Modeling -> Back] ---

class PlanSummary(BaseModel):
    goals: List[str] = Field(..., description="식단 생성 시 반영된 주요 목적")
    year: int
    month: int
    # [추가] 이번 달 남은 일 수 계산 결과
    days_remaining: int = Field(..., description="해당 월의 남은 일 수 (오늘 포함)")
    meal_budget: int = Field(..., description="한 끼 권장 예산")
    meal_count_per_day: int = Field(..., description="하루당 설정된 식사 횟수")
    required_meal_count: int = Field(..., description="총 생성해야 하는 식사 수")
    available_recommendation_count: int = Field(..., description="실제 추천 가능한 식사 수")
    diversity_level: str
    diversity_penalty_strength: float = Field(..., description="중복 메뉴에 대한 패널티 강도")
    warnings: List[str] = Field(default_factory=list, description="식단 생성 과정에서의 주의사항 또는 제한 요소")

class WeeklyPlan(BaseModel):
    period_days: int = Field(..., description="전체 식단 계획 기간 (일 단위)")
    meal_count_per_day: int
    days: List[DailyMeals] = Field(..., description="날짜별 식단 상세")

class RecommendationResult(BaseModel):
    user_id: str
    summary: PlanSummary
    weekly_plan: WeeklyPlan

# # --- [백엔드 API 응답용 스키마] ---

# 단일 식단 응답용 (상세 페이지 화면 10번용)
class MealPlanResponse(BaseModel):
    id: int
    meal_date: date
    estimated_cost: int
    total_calories: int
    # DB의 content 필드(JSON)가 이 리스트 형태로 역직렬화됩니다.
    content: List[MealDetail]

    model_config = ConfigDict(from_attributes=True)

# ------------ 캘린더 메인 화면용 경량 요약 스키마 ------------------
class CalendarMeal(BaseModel):
    slot: int
    meal_id: str
    menu_name: str

class CalendarDay(BaseModel):
    date: date
    calories_per_day: Optional[int] = None
    price_per_day: Optional[int] = None
    meals: List[CalendarMeal]

class CalendarResponse(BaseModel):
    month: str  # "2026-04"
    duration_days: int
    total_price_per_month: int
    average_calories_per_month: int
    days: List[CalendarDay]

# ------------ 스왑 스키마 ---------------
class MealSwapRequest(BaseModel):
    """
    스왑 대상 날짜를 받기 위한 요청 스키마
    """
    with_date: date

class MealSwapResponse(BaseModel):
    swapped: List[CalendarDay]

# -------------- 식단 상세 레시피 영상, 재료, 마켓 정보 조회 스키마 --------------------

class MarketPrice(BaseModel):
    market: Optional[str] = None
    price: Optional[int] = None

class ECommercePrices(BaseModel):
    coupang: Optional[Dict[str, int]] = None
    market_kurly: Optional[Dict[str, int]] = None
    naver_shopping: Optional[Dict[str, int]] = None

class IngredientDetail(BaseModel):
    ingredient_id: str
    ingredient_name: str
    standard_unit: str
    image_url: Optional[str] = None
    lowest_price_between_market: MarketPrice
    e_commerce_prices: ECommercePrices

class MealDetailFullResponse(BaseModel):
    meal_id: str
    menu_name: str
    calories: int
    price: int
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    required_ingredient_ids: List[str]
    ingredients: List[IngredientDetail]

# ------------ 매뉴 변경 전용 스키마 ----------------
class MenuUpdateRequest(BaseModel):
    """
    변경하고자 하는 새로운 메뉴의 ID를 받는 스키마
    """
    new_menu_id: str

# --------------- 대안 메뉴 추천 전용 스키마 ----------------
class AlternativeMenuItem(BaseModel):
    meal_id: str
    menu_name: str
    calories: Optional[int] = None
    price: Optional[int] = None
    image_url: Optional[str] = None

class CurrentMealInfo(BaseModel):
    meal_id: str
    menu_name: str
    calories: Optional[int] = None
    price: Optional[int] = None
    image_url: Optional[str] = None
    date: str  # "YYYY-MM-DD" 형식
    slot: int

class AlternativeMenuResponse(BaseModel):
    current_meal: CurrentMealInfo
    alternatives: List[AlternativeMenuItem]

# --------------- 프론트에 보낼 월간 식단 달력용 스키마 ------------------
class FrontMeal(BaseModel):
    slot: int           # meal_order
    meal_id: str        # menu_id
    menu_name: str      # name

class FrontDayPlan(BaseModel):
    date: str           # "YYYY-MM-DD" 형식
    calories_per_day: Optional[int] = None
    price_per_day: Optional[int] = None
    meals: List[FrontMeal] = []

class FrontMonthlyPlanResponse(BaseModel):
    month: str          # "YYYY-MM" 형식
    duration_days: int
    total_price_per_month: int
    average_calories_per_month: int
    days: List[FrontDayPlan]