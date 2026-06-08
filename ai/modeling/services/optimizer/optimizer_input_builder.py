DIVERSITY_OPTIMIZER_CONFIG = {
    "낮음": {
        "repeat_penalty_weight": 500,
        "max_repeat_per_menu": 3,
        "optimizer_candidate_multiplier": 1.2,
        "solver_time_limit_seconds": 3,
    },
    "보통": {
        "repeat_penalty_weight": 800,
        "max_repeat_per_menu": 2,
        "optimizer_candidate_multiplier": 1.2,
        "solver_time_limit_seconds": 3,
    },
    "높음": {
        "repeat_penalty_weight": 1000,
        "max_repeat_per_menu": 2,
        "optimizer_candidate_multiplier": 1.5,
        "solver_time_limit_seconds": 5,
    },
}


DEFAULT_OPTIMIZER_CONFIG = {
    "score_weight": 100,
    "cost_penalty_weight": 3,
    "cost_penalty_divisor": 100,
    "solver_time_limit_seconds": 3,
    "optimizer_candidate_multiplier": 1.2,
}


def build_optimizer_config(profile: dict) -> dict:
    """
    사용자 profile과 실험용 override 값을 바탕으로
    월간 식단 optimizer 공통 설정을 만든다.

    diversity_level은 메뉴 반복 제어 강도를 결정한다.
    profile에 명시된 optimizer 값이 있으면 해당 값을 우선 적용한다.
    """

    diversity_level = profile.get("diversity_level", "보통")
    diversity_config = DIVERSITY_OPTIMIZER_CONFIG.get(
        diversity_level,
        DIVERSITY_OPTIMIZER_CONFIG["보통"],
    )

    config = {
        **DEFAULT_OPTIMIZER_CONFIG,
        **diversity_config,
    }

    override_keys = [
        "score_weight",
        "cost_penalty_weight",
        "cost_penalty_divisor",
        "repeat_penalty_weight",
        "max_repeat_per_menu",
        "solver_time_limit_seconds",
        "optimizer_candidate_multiplier",
    ]

    for key in override_keys:
        if profile.get(key) is not None:
            config[key] = profile[key]

    return config


def build_optimizer_input(
    recommendations: list[dict],
    profile: dict,
    period_days: int,
    meal_count_per_day: int,
) -> dict:
    """
    월간 식단 solver 구현체에서 사용할 공통 입력 데이터를 만든다.

    recommendations:
    - 기존 scoring + re-ranking이 끝난 후보 메뉴 목록이다.
    - 각 solver 구현체는 이 후보를 바탕으로 월간 식단 슬롯에 메뉴를 배치한다.

    profile:
    - 사용자 예산, 영양 목표, 선호 조건 등이 들어 있는 모델링 profile이다.

    period_days:
    - 생성할 식단 기간이다.

    meal_count_per_day:
    - 하루 식사 개수이다.
    """

    slots = []

    for day in range(1, period_days + 1):
        for meal_order in range(1, meal_count_per_day + 1):
            slots.append({
                "day": day,
                "meal_order": meal_order,
            })

    optimizer_config = build_optimizer_config(profile)

    required_meal_count = period_days * meal_count_per_day
    optimizer_candidate_multiplier = optimizer_config.get(
        "optimizer_candidate_multiplier"
    )

    if optimizer_candidate_multiplier and optimizer_candidate_multiplier > 0:
        optimizer_candidate_limit = int(
            required_meal_count * optimizer_candidate_multiplier
        )

        # 너무 적은 후보만 남으면 품질이 급격히 떨어질 수 있으므로
        # 최소한 월간 식단 슬롯 수만큼은 후보를 유지한다.
        optimizer_candidate_limit = max(
            optimizer_candidate_limit,
            required_meal_count,
        )

        optimizer_recommendations = sorted(
            recommendations,
            key=lambda menu: float(menu.get("final_score", 0) or 0),
            reverse=True,
        )[:optimizer_candidate_limit]
    else:
        optimizer_candidate_limit = None
        optimizer_recommendations = recommendations

    menus = []

    for index, menu in enumerate(optimizer_recommendations):
        menus.append({
            "index": index,
            "menu_id": menu.get("menu_id"),
            "name": menu.get("name"),
            "estimated_cost": int(menu.get("estimated_cost", 0) or 0),
            "calories": float(menu.get("calories", 0) or 0),
            "protein": float(menu.get("protein", 0) or 0),
            "final_score": float(menu.get("final_score", 0) or 0),
            "preference_score": float(
                menu.get("scores", {}).get("preference_score", 0)
                if isinstance(menu.get("scores"), dict)
                else 0
            ),
            "raw_menu": menu,
        })

    return {
        "profile": profile,
        "period_days": period_days,
        "meal_count_per_day": meal_count_per_day,
        "slots": slots,
        "menus": menus,
        "monthly_budget": profile.get("monthly_budget"),
        "required_meal_count": required_meal_count,
        "original_recommendation_count": len(recommendations),
        "used_optimizer_candidate_count": len(optimizer_recommendations),
        "optimizer_candidate_multiplier": optimizer_candidate_multiplier,
        "optimizer_candidate_limit": optimizer_candidate_limit,
        "max_repeat_per_menu": optimizer_config["max_repeat_per_menu"],
        "solver_time_limit_seconds": optimizer_config["solver_time_limit_seconds"],
        "score_weight": optimizer_config["score_weight"],
        "cost_penalty_weight": optimizer_config["cost_penalty_weight"],
        "cost_penalty_divisor": optimizer_config["cost_penalty_divisor"],
        "repeat_penalty_weight": optimizer_config["repeat_penalty_weight"],
        "optimizer_config": optimizer_config,
    }
