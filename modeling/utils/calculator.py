def calculate_meal_budget(
    monthly_budget: int,
    meal_count_per_day: int,
    budget_period_days: int = 30
) -> int:
    """
    월 예산, 예산 기준 일수, 하루 식사 수를 기준으로 한 끼 예산을 계산한다.

    budget_period_days:
    - 3일치 샘플 생성 단계에서는 기본 30일 사용
    - 월간 식단 생성 단계에서는 백엔드가 넘겨준 period_days 사용 가능
    """

    return monthly_budget // budget_period_days // meal_count_per_day