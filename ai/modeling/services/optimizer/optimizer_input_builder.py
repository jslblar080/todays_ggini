import json
import os

def safe_float(value, default=0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def calculate_fallback_difficulty_score(menu: dict, profile: dict) -> float:
    """
    scores.difficulty_score가 없는 경우 menu difficulty와 cooking_skill로 보조 계산한다.
    """

    menu_difficulty = safe_float(menu.get("difficulty"), 3)
    cooking_skill = safe_float(profile.get("cooking_skill"), 3)

    if menu_difficulty <= cooking_skill:
        return 100

    score = 100 - ((menu_difficulty - cooking_skill) * 30)
    return max(0, score)


def get_menu_difficulty_score(menu: dict, profile: dict) -> float:
    """
    optimizer에서 사용할 조리 난이도 적합 점수를 가져온다.

    추천/검증 단계에서는 scores.difficulty를
    "사용자 조리 실력 대비 쉬운 정도" 점수로 사용한다.
    따라서 optimizer도 동일한 기준을 우선 사용해야 한다.
    """

    scores = menu.get("scores") if isinstance(menu.get("scores"), dict) else {}

    if scores.get("difficulty") is not None:
        return safe_float(scores.get("difficulty"))

    if scores.get("difficulty_score") is not None:
        return safe_float(scores.get("difficulty_score"))

    if menu.get("difficulty_score") is not None:
        return safe_float(menu.get("difficulty_score"))

    return calculate_fallback_difficulty_score(
        menu=menu,
        profile=profile,
    )


DIVERSITY_OPTIMIZER_CONFIG = {
    "낮음": {
        "repeat_penalty_weight": 1500,
        "repeat_penalty_growth": "quadratic",
        "max_repeat_per_menu": 3,
        "optimizer_candidate_multiplier": 1.2,
        "solver_time_limit_seconds": 3,
    },
    "보통": {
        "repeat_penalty_weight": 3500,
        "repeat_penalty_growth": "quadratic",
        "max_repeat_per_menu": 2,
        "optimizer_candidate_multiplier": 1.2,
        "solver_time_limit_seconds": 3,
    },
    "높음": {
        "repeat_penalty_weight": 6000,
        "repeat_penalty_growth": "quadratic",
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
    "enable_nutrition_outlier_penalty": False,
    "nutrition_outlier_penalty_weight": 1,
    "enable_protein_bonus": False,
    "protein_bonus_weight": 0,
    "protein_bonus_cap_grams": 35,
    "enable_difficulty_bonus": False,
    "difficulty_bonus_weight": 0,
}



def load_optimizer_tuning_override() -> dict:
    """
    실험 자동화를 위해 환경변수 기반 optimizer override를 읽는다.

    사용 이유:
    - Grid Search / Optuna에서 코드 수정 없이 가중치 조합을 바꿔가며 검증하기 위함
    - 서비스 기본 동작에는 영향을 주지 않고, 실험 실행 시에만 설정을 주입하기 위함

    환경변수:
    - OPTIMIZER_TUNING_OVERRIDE_JSON
    """

    raw_override = os.environ.get("OPTIMIZER_TUNING_OVERRIDE_JSON")

    if not raw_override:
        return {}

    try:
        override = json.loads(raw_override)
    except json.JSONDecodeError:
        return {}

    if not isinstance(override, dict):
        return {}

    return override


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

    goals = profile.get("goals", []) or []

    if "고단백" in goals:
        config["enable_protein_bonus"] = True
        config["protein_bonus_weight"] = 180
        config["protein_bonus_cap_grams"] = 35
        config["repeat_penalty_weight"] = max(
            int(config.get("repeat_penalty_weight", 0) or 0),
            4500,
        )

    cooking_skill = safe_float(profile.get("cooking_skill"), 3)

    if "간편식" in goals:
        config["enable_difficulty_bonus"] = True
        config["difficulty_bonus_weight"] = 120

    elif cooking_skill <= 2:
        config["enable_difficulty_bonus"] = True
        config["difficulty_bonus_weight"] = 50

    if "고단백" in goals and config.get("enable_difficulty_bonus"):
        config["protein_bonus_weight"] = max(
            int(config.get("protein_bonus_weight", 0) or 0),
            220,
        )

    override_keys = [
        "score_weight",
        "cost_penalty_weight",
        "cost_penalty_divisor",
        "repeat_penalty_weight",
        "repeat_penalty_growth",
        "max_repeat_per_menu",
        "solver_time_limit_seconds",
        "optimizer_candidate_multiplier",
        "enable_nutrition_outlier_penalty",
        "nutrition_outlier_penalty_weight",
        "enable_protein_bonus",
        "protein_bonus_weight",
        "protein_bonus_cap_grams",
        "enable_difficulty_bonus",
        "difficulty_bonus_weight",
    ]

    for key in override_keys:
        if profile.get(key) is not None:
            config[key] = profile[key]

    tuning_override = load_optimizer_tuning_override()

    for key in override_keys:
        if tuning_override.get(key) is not None:
            config[key] = tuning_override[key]

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
            "nutrition_outlier_penalty": float(
                menu.get("nutrition_outlier_penalty", 0) or 0
            ),
            "is_extreme_nutrition_outlier": bool(
                menu.get("is_extreme_nutrition_outlier", False)
            ),
            "preference_score": float(
                menu.get("scores", {}).get("preference_score", 0)
                if isinstance(menu.get("scores"), dict)
                else 0
            ),
            "difficulty_score": get_menu_difficulty_score(
                menu=menu,
                profile=profile,
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
        "repeat_penalty_growth": optimizer_config["repeat_penalty_growth"],
        "enable_nutrition_outlier_penalty": optimizer_config[
            "enable_nutrition_outlier_penalty"
        ],
        "nutrition_outlier_penalty_weight": optimizer_config[
            "nutrition_outlier_penalty_weight"
        ],
        "enable_protein_bonus": optimizer_config["enable_protein_bonus"],
        "protein_bonus_weight": optimizer_config["protein_bonus_weight"],
        "protein_bonus_cap_grams": optimizer_config["protein_bonus_cap_grams"],
        "enable_difficulty_bonus": optimizer_config["enable_difficulty_bonus"],
        "difficulty_bonus_weight": optimizer_config["difficulty_bonus_weight"],
        "optimizer_config": optimizer_config,
    }
