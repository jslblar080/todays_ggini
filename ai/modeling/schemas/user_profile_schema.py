from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class UserProfileInput(BaseModel):
    """
    사용자가 개인 맞춤 설정 페이지에서 입력한 값을 담는 구조이다.

    이 구조는 Front → Back → Modeling으로 전달되는 profile의 기본 형태이다.

    sample_period_days:
    - 3일치 샘플 식단 생성에 사용한다.
    - 기본값은 3일이다.

    period_days:
    - 월간 식단 생성 기간에 사용한다.
    - 3일치 샘플 생성 단계에서는 없어도 된다.
    - 값이 없으면 profile 생성 단계에서 기본값 30일로 처리한다.
    """

    goals: List[str] = Field(..., min_length=1, max_length=3)

    monthly_budget: int = Field(..., gt=0)
    meal_count_per_day: int = Field(..., ge=1, le=5)

    # 1차 온보딩 profile_build 단계에서 계산된 하루 권장 칼로리
    recommended_daily_calories: Optional[int] = Field(default=None, gt=0)

    cooking_skill: int = Field(..., ge=1, le=5)

    preferred_categories: List[str] = Field(..., min_length=1)
    diversity_level: str

    ingredient_preferences: List[str] = Field(default_factory=list)
    allergy_ingredients: List[str] = Field(default_factory=list)

    # 샘플 식단 생성용
    sample_period_days: int = Field(default=3, ge=1, le=7)

    # 월간 식단 생성용
    period_days: Optional[int] = Field(default=None, ge=1, le=31)

    @field_validator("goals")
    @classmethod
    def validate_goals(cls, goals: List[str]) -> List[str]:
        allowed_goals = [
            "식비 절약",
            "영양 균형",
            "다이어트",
            "고단백",
            "간편식",
            "맛 중심",
        ]

        if len(goals) != len(set(goals)):
            raise ValueError("목표는 중복 없이 선택해야 합니다.")

        for goal in goals:
            if goal not in allowed_goals:
                raise ValueError(f"지원하지 않는 목표입니다: {goal}")

        return goals

    @field_validator("preferred_categories")
    @classmethod
    def validate_preferred_categories(
        cls,
        preferred_categories: List[str]
    ) -> List[str]:
        allowed_categories = [
            "한식",
            "양식",
            "일식",
            "중식",
            "분식",
            "샐러드/건강식",
            "패스트푸드",
            "다 좋아요",
        ]

        if len(preferred_categories) != len(set(preferred_categories)):
            raise ValueError("선호 카테고리는 중복 없이 선택해야 합니다.")

        for category in preferred_categories:
            if category not in allowed_categories:
                raise ValueError(f"지원하지 않는 카테고리입니다: {category}")

        return preferred_categories

    @field_validator("diversity_level")
    @classmethod
    def validate_diversity_level(cls, diversity_level: str) -> str:
        allowed_diversity_levels = [
            "낮음",
            "보통",
            "높음",
        ]

        if diversity_level not in allowed_diversity_levels:
            raise ValueError(f"지원하지 않는 다양성 수준입니다: {diversity_level}")

        return diversity_level

    @field_validator("ingredient_preferences")
    @classmethod
    def validate_ingredient_preferences(
        cls,
        ingredient_preferences: List[str]
    ) -> List[str]:
        allowed_ingredient_groups = [
            "육류",
            "해산물류",
            "식물성 단백질류",
            "채소류",
            "계란 및 유제품류",
        ]

        if len(ingredient_preferences) != len(set(ingredient_preferences)):
            raise ValueError("선호 재료군은 중복 없이 선택해야 합니다.")

        for ingredient_group in ingredient_preferences:
            if ingredient_group not in allowed_ingredient_groups:
                raise ValueError(
                    f"지원하지 않는 재료군입니다: {ingredient_group}"
                )

        return ingredient_preferences

    @field_validator("allergy_ingredients")
    @classmethod
    def validate_allergy_ingredients(
        cls,
        allergy_ingredients: List[str]
    ) -> List[str]:
        if len(allergy_ingredients) != len(set(allergy_ingredients)):
            raise ValueError("알레르기 재료는 중복 없이 입력해야 합니다.")

        return allergy_ingredients


class UserProfileRequest(BaseModel):
    """
    Front 또는 Back에서 Modeling으로 전달하는 사용자 입력 전체 구조이다.

    id:
    - User 테이블의 id 컬럼과 매핑되는 사용자 식별값이다.

    request_type:
    - 요청 종류이다.
    - 예: meal_style_candidates, monthly_plan

    profile:
    - 사용자가 입력한 식단 설정값이다.
    """

    id: int | str
    request_type: str
    profile: UserProfileInput