from copy import deepcopy
from datetime import datetime, timezone

from services.recommendation.recommendation_service import recommend_menus
from services.plan.menu_similarity_service import are_menus_similar


GOAL_STYLE_META = {
    "식비 절약": {
        "style_id": "budget_first",
        "style_name": "가성비 최우선",
        "description": "예산을 가장 우선으로 고려한 식단",
        "summary_comment": "예산 부담을 줄이고 간편하게 구성한 식단입니다.",
        "focus_key": "budget"
    },
    "영양 균형": {
        "style_id": "nutrition_balance",
        "style_name": "영양 균형식",
        "description": "칼로리와 단백질 균형을 함께 고려한 식단",
        "summary_comment": "영양 균형을 고려해 건강하게 구성한 식단입니다.",
        "focus_key": "nutrition"
    },
    "다이어트": {
        "style_id": "diet_light",
        "style_name": "가벼운 관리식",
        "description": "칼로리 부담을 줄이고 가볍게 구성한 식단",
        "summary_comment": "부담이 적은 메뉴를 중심으로 구성한 식단입니다.",
        "focus_key": "nutrition"
    },
    "고단백": {
        "style_id": "high_protein",
        "style_name": "고단백 관리식",
        "description": "단백질 섭취를 우선으로 고려한 식단",
        "summary_comment": "단백질 섭취를 늘리고 싶은 사용자에게 적합한 식단입니다.",
        "focus_key": "nutrition"
    },
    "간편식": {
        "style_id": "easy_cooking",
        "style_name": "간편 조리식",
        "description": "조리 난이도와 시간을 낮게 유지한 식단",
        "summary_comment": "조리 부담을 줄이고 빠르게 준비할 수 있는 식단입니다.",
        "focus_key": "difficulty"
    },
    "맛 중심": {
        "style_id": "taste_first",
        "style_name": "취향 맞춤식",
        "description": "선호 카테고리와 재료 취향을 더 많이 반영한 식단",
        "summary_comment": "사용자의 취향과 선호 재료를 중심으로 구성한 식단입니다.",
        "focus_key": "preference"
    }
}


DISPLAY_LABELS = {
    "health": "건강",
    "cost_efficiency": "가성비",
    "taste": "맛",
    "cooking_ease": "조리"
}


FOCUS_TO_DISPLAY_SCORE_KEY = {
    "budget": "cost_efficiency",
    "nutrition": "health",
    "preference": "taste",
    "difficulty": "cooking_ease"
}


def normalize_weights(weights: dict) -> dict:
    """
    가중치 합이 1이 되도록 정규화한다.
    """

    total = sum(weights.values())

    if total == 0:
        raise ValueError("가중치 합이 0입니다.")

    return {
        key: round(value / total, 4)
        for key, value in weights.items()
    }


def boost_style_weights(
    base_weights: dict,
    focus_key: str,
    boost_amount: float = 0.45
) -> dict:
    """
    사용자의 기본 가중치를 유지하되,
    스타일 카드에서는 각 스타일의 차이가 더 잘 보이도록 핵심 항목을 강하게 보정한다.

    스타일 후보 단계는 사용자가 '어떤 방향의 식단을 선호하는지' 선택하는 구간이므로
    월간 식단보다 스타일별 특징이 더 분명해야 한다.
    """

    style_weights = deepcopy(base_weights)

    if focus_key not in style_weights:
        raise ValueError(f"지원하지 않는 focus_key입니다: {focus_key}")

    style_weights[focus_key] += boost_amount

    # 스타일 샘플은 사용자에게 다양한 선택지를 보여주는 것이 중요하므로
    # 다양성도 함께 강화한다.
    if "diversity" in style_weights:
        style_weights["diversity"] += 0.25

    # focus별 보조 조정
    if focus_key == "budget":
        style_weights["nutrition"] = max(style_weights.get("nutrition", 0) - 0.05, 0)

    if focus_key == "nutrition":
        style_weights["budget"] = max(style_weights.get("budget", 0) - 0.05, 0)

    if focus_key == "difficulty":
        style_weights["preference"] = max(style_weights.get("preference", 0) - 0.05, 0)

    if focus_key == "preference":
        style_weights["difficulty"] = max(style_weights.get("difficulty", 0) - 0.05, 0)

    return normalize_weights(style_weights)


def build_profile_with_style_weights(
    profile: dict,
    style_weights: dict,
    style_goal: str
) -> dict:
    """
    기존 profile은 유지하되,
    스타일 샘플 추천 단계에서는 해당 스타일의 목표가 더 잘 드러나도록 goals와 weights를 함께 조정한다.

    예:
    - 영양 균형식 -> goals: ["영양 균형"]
    - 고단백 관리식 -> goals: ["고단백"]
    - 가벼운 관리식 -> goals: ["다이어트"]
    """

    style_profile = deepcopy(profile)

    style_profile["goals"] = [style_goal]
    style_profile["weights"] = style_weights

    # 스타일 샘플은 사용자의 다양성 설정과 무관하게
    # 사용자가 비교할 수 있는 선택지를 보여주는 단계이므로 다양성을 높게 고정한다.
    style_profile["diversity_penalty_strength"] = 0.65

    return style_profile


def get_candidate_style_metas(profile: dict) -> list[dict]:
    """
    사용자가 선택한 goals를 기반으로 스타일 후보 3개를 만든다.

    사용자가 선택한 목표가 3개면 해당 목표 3개를 사용한다.
    사용자가 선택한 목표가 1~2개면, 나머지는 기본 스타일로 채운다.
    """

    selected_goals = profile["goals"]
    style_metas = []

    for goal in selected_goals:
        if goal in GOAL_STYLE_META:
            style_metas.append({
                **GOAL_STYLE_META[goal],
                "source_goal": goal,
                "is_support_style": False
            })

    if len(style_metas) < 3:
        for goal, meta in GOAL_STYLE_META.items():
            if goal in selected_goals:
                continue

            style_metas.append({
                **meta,
                "source_goal": goal,
                "is_support_style": True
            })

            if len(style_metas) == 3:
                break

    return style_metas[:3]


def score_to_display_scale(score: float) -> int:
    """
    0~100 점수를 사용자 표시용 1~10 점수로 변환한다.
    """

    converted_score = round(score / 10)

    if converted_score < 1:
        return 1

    if converted_score > 10:
        return 10

    return converted_score


def calculate_average_scores(recommendations: list[dict]) -> dict:
    """
    추천 메뉴들의 내부 scores 평균을 계산한다.
    """

    if not recommendations:
        return {
            "budget": 0,
            "nutrition": 0,
            "preference": 0,
            "difficulty": 0,
            "diversity": 0
        }

    score_sums = {
        "budget": 0,
        "nutrition": 0,
        "preference": 0,
        "difficulty": 0,
        "diversity": 0
    }

    for recommendation in recommendations:
        scores = recommendation.get("scores", {})

        for key in score_sums:
            score_sums[key] += scores.get(key, 0)

    count = len(recommendations)

    return {
        key: score_sums[key] / count
        for key in score_sums
    }


def build_display_scores(
    recommendations: list[dict],
    focus_key: str
) -> dict:
    """
    스타일 카드에 보여줄 건강/가성비/맛/조리 점수를 만든다.

    내부 점수 매핑:
    nutrition  -> health
    budget     -> cost_efficiency
    preference -> taste
    difficulty -> cooking_ease

    단, 스타일의 핵심 focus_key는 사용자에게 의도가 잘 보이도록
    최소 8점 이상으로 보정한다.
    """

    average_scores = calculate_average_scores(recommendations)

    display_scores = {
        "health": score_to_display_scale(average_scores["nutrition"]),
        "cost_efficiency": score_to_display_scale(average_scores["budget"]),
        "taste": score_to_display_scale(average_scores["preference"]),
        "cooking_ease": score_to_display_scale(average_scores["difficulty"])
    }

    focus_display_key = FOCUS_TO_DISPLAY_SCORE_KEY.get(focus_key)

    if focus_display_key:
        display_scores[focus_display_key] = max(
            display_scores[focus_display_key],
            8
        )

    return display_scores


def simplify_meal_for_sample(meal: dict) -> dict:
    """
    3일치 샘플 카드에 필요한 메뉴 정보만 남긴다.
    """

    return {
        "meal_order": meal["meal_order"],
        "menu_id": meal["menu_id"],
        "name": meal["name"],
        "category": meal.get("category"),
        "estimated_cost": meal.get("estimated_cost"),
        "calories": meal.get("calories"),
        "protein": meal.get("protein")
    }


def build_sample_plan_from_recommendations(
    recommendations: list[dict],
    meal_count_per_day: int,
    sample_period_days: int
) -> dict:
    """
    3일치 샘플 카드용 식단을 구성한다.

    월간 식단과 다르게, 샘플 카드에서는 같은 메뉴가 반복되면 좋지 않으므로
    추천 결과 리스트를 순서대로 배치한다.

    예:
    3일 × 2끼 = 6끼
    recommendations 상위 6개를 순서대로 배치
    """

    sample_plan = {
        "period_days": sample_period_days,
        "meal_count_per_day": meal_count_per_day,
        "days": []
    }

    if not recommendations:
        return sample_plan

    recommendation_index = 0

    for day in range(1, sample_period_days + 1):
        day_plan = {
            "day": day,
            "meals": []
        }

        for meal_order in range(1, meal_count_per_day + 1):
            recommendation = recommendations[
                recommendation_index % len(recommendations)
            ]

            meal = simplify_meal_for_sample({
                **recommendation,
                "meal_order": meal_order
            })

            day_plan["meals"].append(meal)
            recommendation_index += 1

        sample_plan["days"].append(day_plan)

    return sample_plan


def get_generated_at() -> str:
    """
    UTC 기준 생성 시각을 ISO 형식 문자열로 반환한다.
    """

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_meal_style_candidates(
    user_id: str,
    candidate_menus: list[dict],
    profile: dict,
    meal_count_per_day: int,
    sample_period_days: int = 3
) -> dict:
    """
    사용자 목표 기반으로 식단 스타일 후보 3개를 생성한다.
    """

    style_metas = get_candidate_style_metas(profile)
    meal_style_candidates = []

    warnings = []

    required_sample_meal_count = sample_period_days * meal_count_per_day

    # 스타일 후보 간 메뉴 중복 방지용
    used_menus = []

    for style_meta in style_metas:
        focus_key = style_meta["focus_key"]

        style_weights = boost_style_weights(
            base_weights=profile["weights"],
            focus_key=focus_key,
            boost_amount=0.45
        )

        style_profile = build_profile_with_style_weights(
            profile=profile,
            style_weights=style_weights,
            style_goal=style_meta["source_goal"]
        )

        raw_recommendations = recommend_menus(
            menus=candidate_menus,
            profile=style_profile,
            top_n=len(candidate_menus)
        )

        recommendations = select_diverse_recommendations_for_style(
            recommendations=raw_recommendations,
            used_menus=used_menus,
            required_count=required_sample_meal_count
        )

        update_used_menus(
            recommendations=recommendations,
            used_menus=used_menus
        )

        if len(recommendations) < required_sample_meal_count:
            warnings.append(
                f"{style_meta['style_name']} 스타일의 샘플 식단에 필요한 "
                f"{required_sample_meal_count}개 메뉴 중 "
                f"{len(recommendations)}개만 추천되었습니다. 부족한 메뉴는 반복될 수 있습니다."
            )

        sample_plan = build_sample_plan_from_recommendations(
            recommendations=recommendations,
            meal_count_per_day=meal_count_per_day,
            sample_period_days=sample_period_days
        )

        meal_style_candidates.append({
            "style_id": style_meta["style_id"],
            "style_name": style_meta["style_name"],
            "description": style_meta["description"],
            "summary_comment": style_meta["summary_comment"],
            "source_goal": style_meta.get("source_goal"),
            "focus_key": focus_key,
            "display_scores": build_display_scores(
                recommendations=recommendations,
                focus_key=focus_key
            ),
            "display_labels": DISPLAY_LABELS,
            "sample_plan": sample_plan
        })

    return {
        "id": user_id,
        "request_type": "meal_style_candidates",
        "meta": {
            "sample_period_days": sample_period_days,
            "meal_count_per_day": meal_count_per_day,
            "total_style_count": len(meal_style_candidates),
            "generated_at": get_generated_at(),
            "warnings": warnings
        },
        "meal_style_candidates": meal_style_candidates
    }

def is_same_menu_id(
    recommendation: dict,
    used_menus: list[dict]
) -> bool:
    """
    이미 다른 스타일 샘플에서 같은 menu_id가 사용되었는지 확인한다.
    """

    menu_id = recommendation.get("menu_id")

    for used_menu in used_menus:
        if menu_id == used_menu.get("menu_id"):
            return True

    return False


def is_duplicate_or_similar_menu(
    recommendation: dict,
    used_menus: list[dict]
) -> bool:
    """
    이미 다른 스타일 샘플에서 사용한 메뉴이거나,
    그 메뉴와 유사한 메뉴인지 확인한다.

    menu_id, similar_menu_ids, 정규화된 메뉴명, 재료 유사도까지 함께 본다.
    """

    for used_menu in used_menus:
        if are_menus_similar(recommendation, used_menu):
            return True

    return False


def select_diverse_recommendations_for_style(
    recommendations: list[dict],
    used_menus: list[dict],
    required_count: int
) -> list[dict]:
    """
    3개 스타일 후보 간 메뉴 중복을 최대한 줄인다.

    선택 우선순위:
    1. 다른 스타일과 menu_id도 다르고 유사하지 않으며, 현재 스타일 내부에서도 유사하지 않은 메뉴
    2. 다른 스타일과 유사할 수는 있지만, menu_id는 겹치지 않고 현재 스타일 내부에서도 유사하지 않은 메뉴
    3. 그래도 부족하면 menu_id만 중복되지 않는 메뉴
    4. 정말 부족할 때만 최후 fallback으로 기존 추천 순서에서 채움
    """

    selected_recommendations = []

    # 1차: 다른 스타일과도 안 겹치고, 현재 스타일 내부에서도 안 겹치는 메뉴
    for recommendation in recommendations:
        if len(selected_recommendations) >= required_count:
            break

        if is_same_menu_id(
            recommendation=recommendation,
            used_menus=used_menus
        ):
            continue

        if is_duplicate_or_similar_menu(
            recommendation=recommendation,
            used_menus=used_menus
        ):
            continue

        if is_duplicate_or_similar_menu(
            recommendation=recommendation,
            used_menus=selected_recommendations
        ):
            continue

        selected_recommendations.append(recommendation)

    # 2차: 다른 스타일과 유사 메뉴는 허용하지만,
    # 같은 menu_id는 계속 금지하고, 현재 스타일 내부 유사도는 계속 막는다.
    if len(selected_recommendations) < required_count:
        for recommendation in recommendations:
            if len(selected_recommendations) >= required_count:
                break

            if is_same_menu_id(
                recommendation=recommendation,
                used_menus=used_menus
            ):
                continue

            if is_same_menu_id(
                recommendation=recommendation,
                used_menus=selected_recommendations
            ):
                continue

            if is_duplicate_or_similar_menu(
                recommendation=recommendation,
                used_menus=selected_recommendations
            ):
                continue

            selected_recommendations.append(recommendation)

    # 3차: 그래도 부족하면 현재 스타일 내부에서 menu_id만 안 겹치게 채운다.
    if len(selected_recommendations) < required_count:
        for recommendation in recommendations:
            if len(selected_recommendations) >= required_count:
                break

            if is_same_menu_id(
                recommendation=recommendation,
                used_menus=selected_recommendations
            ):
                continue

            selected_recommendations.append(recommendation)

    # 4차: 정말 후보가 부족한 경우에만 fallback
    if len(selected_recommendations) < required_count:
        for recommendation in recommendations:
            if len(selected_recommendations) >= required_count:
                break

            if recommendation in selected_recommendations:
                continue

            selected_recommendations.append(recommendation)

    return selected_recommendations


def update_used_menus(
    recommendations: list[dict],
    used_menus: list[dict]
) -> None:
    """
    선택된 샘플 메뉴를 전역 사용 목록에 기록한다.

    다음 스타일 후보를 만들 때 같은 메뉴 또는 유사 메뉴가
    반복되지 않도록 하기 위한 처리이다.
    """

    for recommendation in recommendations:
        used_menus.append(recommendation)