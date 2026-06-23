from copy import deepcopy


def build_selected_style_summary(selected_style: dict) -> dict:
    """
    월간 식단 결과에 포함할 선택 스타일 요약 정보를 만든다.
    """

    return {
        "style_id": selected_style.get("style_id"),
        "style_name": selected_style.get("style_name"),
        "description": selected_style.get("description"),
        "summary_comment": selected_style.get("summary_comment"),
        "source_goal": selected_style.get("source_goal"),
        "focus_key": selected_style.get("focus_key"),
        "display_scores": selected_style.get("display_scores", {}),
        "display_labels": selected_style.get("display_labels", {}),
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


def get_nutrition_detail_weights_by_style(selected_style: dict) -> dict:
    """
    사용자가 선택한 스타일에 따라 nutrition 내부 세부 가중치를 만든다.

    nutrition 점수는 하나의 점수처럼 보이지만,
    내부적으로는 다음 세부 기준으로 나뉜다.

    - diet: 칼로리와 지방 중심
    - high_protein: 단백질 중심
    - balance: 탄수화물/단백질/지방 비율 중심
    """

    source_goal = selected_style.get("source_goal")

    if source_goal == "다이어트":
        return {
            "diet": 0.75,
            "high_protein": 0.10,
            "balance": 0.15,
        }

    if source_goal == "고단백":
        return {
            "diet": 0.15,
            "high_protein": 0.65,
            "balance": 0.20,
        }

    if source_goal == "영양 균형":
        return {
            "diet": 0.20,
            "high_protein": 0.20,
            "balance": 0.60,
        }

    return {
        "diet": 0.33,
        "high_protein": 0.34,
        "balance": 0.33,
    }


def apply_selected_style_to_profile(
    profile: dict,
    selected_style: dict
) -> dict:
    """
    사용자가 선택한 3일 샘플 스타일을 월간 식단 생성용 profile에 반영한다.
    """

    monthly_profile = deepcopy(profile)

    monthly_profile["selected_style_goal"] = selected_style.get("source_goal")
    monthly_profile["selected_style_id"] = selected_style.get("style_id")
    monthly_profile["selected_style_focus_key"] = selected_style.get("focus_key")

    focus_key = selected_style.get("focus_key")

    if not focus_key:
        monthly_profile["nutrition_detail_weights"] = get_nutrition_detail_weights_by_style(
            selected_style=selected_style
        )
        return monthly_profile

    weights = deepcopy(monthly_profile.get("weights", {}))

    if focus_key not in weights:
        monthly_profile["nutrition_detail_weights"] = get_nutrition_detail_weights_by_style(
            selected_style=selected_style
        )
        return monthly_profile

    weights[focus_key] += 0.2

    if focus_key == "budget":
        weights["nutrition"] = max(weights.get("nutrition", 0) - 0.05, 0)
        weights["preference"] = max(weights.get("preference", 0) - 0.03, 0)

    if focus_key == "nutrition":
        weights["budget"] = max(weights.get("budget", 0) - 0.05, 0)

    if focus_key == "difficulty":
        weights["preference"] = max(weights.get("preference", 0) - 0.03, 0)

    if focus_key == "preference":
        weights["difficulty"] = max(weights.get("difficulty", 0) - 0.03, 0)

    if "diversity" in weights:
        weights["diversity"] += 0.05

    monthly_profile["weights"] = normalize_weights(weights)

    monthly_profile["nutrition_detail_weights"] = get_nutrition_detail_weights_by_style(
        selected_style=selected_style
    )

    return monthly_profile