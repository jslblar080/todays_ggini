def build_style_validation(
    selected_style: dict,
    summary: dict,
    profile: dict
) -> dict:
    """
    선택한 스타일이 월간 식단 결과에 잘 반영되었는지 검증한다.
    """

    source_goal = selected_style.get("source_goal")
    focus_key = selected_style.get("focus_key")
    style_name = selected_style.get("style_name")

    if source_goal == "고단백":
        return validate_high_protein_style(
            style_name=style_name,
            summary=summary,
        )

    if source_goal == "다이어트":
        return validate_diet_style(
            style_name=style_name,
            summary=summary,
        )

    if source_goal == "영양 균형":
        return validate_balance_style(
            style_name=style_name,
            summary=summary,
        )

    if source_goal == "식비 절약":
        return validate_budget_style(
            style_name=style_name,
            summary=summary,
            profile=profile,
        )

    if source_goal == "간편식":
        return validate_easy_cooking_style(
            style_name=style_name,
            summary=summary,
        )

    if source_goal == "맛 중심":
        return validate_preference_style(
            style_name=style_name,
            summary=summary,
            focus_key=focus_key,
        )

    return {
        "target_style": source_goal,
        "status": "unknown",
        "message": "지원하지 않는 스타일이므로 검증 기준을 적용하지 못했습니다.",
        "checked_metrics": {},
    }


def validate_high_protein_style(
    style_name: str,
    summary: dict
) -> dict:
    """
    고단백 스타일 검증.

    월간 식단은 여러 메뉴를 섞어 구성되므로,
    모든 끼니가 30g 이상 단백질을 가지기는 어렵다.
    따라서 평균 28g 이상이면 고단백 스타일이 충분히 반영된 것으로 본다.
    """

    average_protein = summary.get("average_protein", 0)

    if average_protein >= 28:
        status = "pass"
        message = "고단백 스타일에 맞게 평균 단백질이 충분히 높게 구성되었습니다."
    elif average_protein >= 25:
        status = "warning"
        message = "고단백 스타일이 어느 정도 반영되었지만, 평균 단백질을 조금 더 높일 여지가 있습니다."
    else:
        status = "fail"
        message = "고단백 스타일에 비해 평균 단백질이 낮아 보완이 필요합니다."

    return {
        "target_style": style_name,
        "status": status,
        "message": message,
        "checked_metrics": {
            "average_protein": average_protein,
            "recommended_minimum_protein": 28,
        },
    }


def validate_diet_style(
    style_name: str,
    summary: dict
) -> dict:
    """
    다이어트 스타일 검증.
    """

    average_calories = summary.get("average_calories", 0)
    average_fat = summary.get("average_fat", 0)

    if average_calories <= 650 and average_fat <= 23:
        status = "pass"
        message = "다이어트 스타일에 맞게 평균 칼로리와 지방이 낮게 구성되었습니다."
    elif average_calories <= 750 and average_fat <= 28:
        status = "warning"
        message = "다이어트 스타일이 어느 정도 반영되었지만, 일부 메뉴의 칼로리나 지방을 더 낮출 수 있습니다."
    else:
        status = "fail"
        message = "다이어트 스타일에 비해 평균 칼로리 또는 지방이 높아 보완이 필요합니다."

    return {
        "target_style": style_name,
        "status": status,
        "message": message,
        "checked_metrics": {
            "average_calories": average_calories,
            "average_fat": average_fat,
            "recommended_max_calories": 650,
            "recommended_max_fat": 23,
        },
    }


def validate_balance_style(
    style_name: str,
    summary: dict
) -> dict:
    """
    영양 균형 스타일 검증.
    """

    average_carbohydrate = summary.get("average_carbohydrate", 0)
    average_protein = summary.get("average_protein", 0)
    average_fat = summary.get("average_fat", 0)

    total_macro = average_carbohydrate + average_protein + average_fat

    if total_macro <= 0:
        return {
            "target_style": style_name,
            "status": "unknown",
            "message": "탄수화물, 단백질, 지방 정보가 부족해 영양 균형을 검증할 수 없습니다.",
            "checked_metrics": {},
        }

    carbohydrate_ratio = average_carbohydrate / total_macro
    protein_ratio = average_protein / total_macro
    fat_ratio = average_fat / total_macro

    is_strict_balance = (
        0.45 <= carbohydrate_ratio <= 0.65
        and 0.15 <= protein_ratio <= 0.35
        and 0.15 <= fat_ratio <= 0.35
    )

    is_loose_balance = (
        0.35 <= carbohydrate_ratio <= 0.70
        and 0.10 <= protein_ratio <= 0.40
        and 0.10 <= fat_ratio <= 0.45
    )

    if is_strict_balance:
        status = "pass"
        message = "탄수화물, 단백질, 지방 비율이 안정적이어서 영양 균형 스타일이 잘 반영되었습니다."
    elif is_loose_balance:
        status = "warning"
        message = "영양 균형이 대체로 무난하지만, 일부 영양 비율은 조정할 여지가 있습니다."
    else:
        status = "fail"
        message = "영양 균형 스타일에 비해 탄수화물, 단백질, 지방 비율 조정이 필요합니다."

    return {
        "target_style": style_name,
        "status": status,
        "message": message,
        "checked_metrics": {
            "carbohydrate_ratio": round(carbohydrate_ratio, 4),
            "protein_ratio": round(protein_ratio, 4),
            "fat_ratio": round(fat_ratio, 4),
            "average_carbohydrate": average_carbohydrate,
            "average_protein": average_protein,
            "average_fat": average_fat,
        },
    }


def validate_budget_style(
    style_name: str,
    summary: dict,
    profile: dict
) -> dict:
    """
    가성비 스타일 검증.
    """

    total_estimated_cost = summary.get("total_estimated_cost", 0)
    average_daily_cost = summary.get("average_daily_cost", 0)

    monthly_budget = profile.get("monthly_budget", 0)
    period_days = profile.get("period_days", 30)
    meal_count_per_day = profile.get("meal_count_per_day", 1)
    meal_budget = profile.get("meal_budget", 0)

    if monthly_budget <= 0:
        monthly_budget = meal_budget * period_days * meal_count_per_day

    if monthly_budget <= 0:
        return {
            "target_style": style_name,
            "status": "unknown",
            "message": "예산 정보가 부족해 가성비 스타일을 검증할 수 없습니다.",
            "checked_metrics": {},
        }

    budget_usage_rate = total_estimated_cost / monthly_budget

    if budget_usage_rate <= 0.85:
        status = "pass"
        message = "월 예산 안에서 여유 있게 식단이 구성되어 가성비 스타일이 잘 반영되었습니다."
    elif budget_usage_rate <= 1.0:
        status = "warning"
        message = "월 예산 안에는 들어오지만, 예산 여유가 크지는 않습니다."
    else:
        status = "fail"
        message = "월 예산을 초과하여 가성비 스타일 보완이 필요합니다."

    return {
        "target_style": style_name,
        "status": status,
        "message": message,
        "checked_metrics": {
            "total_estimated_cost": total_estimated_cost,
            "monthly_budget": monthly_budget,
            "budget_usage_rate": round(budget_usage_rate, 4),
            "average_daily_cost": average_daily_cost,
        },
    }


def validate_easy_cooking_style(
    style_name: str,
    summary: dict
) -> dict:
    """
    간편식 스타일 검증.

    현재 난이도는 재료 수, 조리 단계 수, 조리 시간, 조리 동작 키워드를 기반으로 계산된다.
    월간 식단 전체 평균 기준에서는 75점 이상이면 간편식 스타일이 잘 반영된 것으로 본다.
    """

    average_difficulty_score = summary.get("average_difficulty_score", 0)

    if average_difficulty_score >= 75:
        status = "pass"
        message = "조리 난이도 점수가 충분히 높아 간편식 스타일이 잘 반영되었습니다."
    elif average_difficulty_score >= 65:
        status = "warning"
        message = "간편식 스타일이 어느 정도 반영되었지만, 더 쉬운 메뉴를 늘릴 수 있습니다."
    else:
        status = "fail"
        message = "간편식 스타일에 비해 조리 난이도 부담이 있어 보완이 필요합니다."

    return {
        "target_style": style_name,
        "status": status,
        "message": message,
        "checked_metrics": {
            "average_difficulty_score": average_difficulty_score,
            "recommended_minimum_difficulty_score": 75,
        },
    }


def validate_preference_style(
    style_name: str,
    summary: dict,
    focus_key: str
) -> dict:
    """
    취향 맞춤 스타일 검증.
    """

    average_preference_score = summary.get("average_preference_score", 0)

    if average_preference_score >= 85:
        status = "pass"
        message = "선호도 점수가 높아 취향 맞춤식 스타일이 잘 반영되었습니다."
    elif average_preference_score >= 70:
        status = "warning"
        message = "취향 맞춤식이 어느 정도 반영되었지만, 선호 카테고리나 재료 반영을 더 강화할 수 있습니다."
    else:
        status = "fail"
        message = "취향 맞춤식에 비해 선호도 점수가 낮아 보완이 필요합니다."

    return {
        "target_style": style_name,
        "status": status,
        "message": message,
        "checked_metrics": {
            "average_preference_score": average_preference_score,
            "applied_focus_key": focus_key,
            "recommended_minimum_preference_score": 85,
        },
    }



def calculate_percentile(values: list[float], percentile: float) -> float | None:
    """
    정렬된 값 분포에서 percentile 값을 계산한다.
    """

    if not values:
        return None

    sorted_values = sorted(values)
    position = (len(sorted_values) - 1) * percentile
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)

    if lower_index == upper_index:
        return sorted_values[lower_index]

    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]

    return lower_value + (upper_value - lower_value) * (
        position - lower_index
    )


def calculate_average(values: list[float]) -> float | None:
    """
    숫자 리스트의 평균을 계산한다.
    """

    if not values:
        return None

    return round(sum(values) / len(values), 2)


def build_difficulty_feasibility_diagnostics(
    optimizer_snapshot: dict | None,
    pass_threshold: float = 75,
    warning_threshold: float = 65,
) -> dict | None:
    """
    후보풀의 난이도 점수 분포를 기반으로 간편식 기준 달성 가능성을 진단한다.

    이 진단은 validation status를 직접 바꾸지 않고,
    실패 원인이 optimizer 선택 문제인지 후보풀 한계인지 분리하기 위한 보조 정보다.
    """

    if not optimizer_snapshot:
        return None

    menus = optimizer_snapshot.get("menus") or []

    if not menus:
        return {
            "status": "unavailable",
            "reason": "candidate_menus_unavailable",
            "candidate_count": 0,
            "pass_threshold": pass_threshold,
            "warning_threshold": warning_threshold,
        }

    scores = [
        float(menu.get("difficulty_score", 0) or 0)
        for menu in menus
    ]

    candidate_p75 = calculate_percentile(scores, 0.75)
    candidate_p90 = calculate_percentile(scores, 0.90)

    candidate_ge_pass_count = sum(
        1 for score in scores
        if score >= pass_threshold
    )
    candidate_ge_warning_count = sum(
        1 for score in scores
        if score >= warning_threshold
    )
    candidate_ge40_count = sum(
        1 for score in scores
        if score >= 40
    )
    candidate_eq0_count = sum(
        1 for score in scores
        if score == 0
    )

    if candidate_ge_pass_count == 0:
        status = "absolute_pass_unreachable"
        reason = "candidate_difficulty_shortage"
    elif candidate_p90 is not None and candidate_p90 < pass_threshold:
        status = "pass_threshold_very_sparse"
        reason = "candidate_difficulty_sparse"
    else:
        status = "candidate_pool_has_pass_options"
        reason = "candidate_pool_feasible"

    return {
        "status": status,
        "reason": reason,
        "candidate_count": len(scores),
        "candidate_avg_difficulty": calculate_average(scores),
        "candidate_p75_difficulty": (
            round(candidate_p75, 2)
            if candidate_p75 is not None
            else None
        ),
        "candidate_p90_difficulty": (
            round(candidate_p90, 2)
            if candidate_p90 is not None
            else None
        ),
        "candidate_max_difficulty": max(scores) if scores else None,
        "candidate_ge75_count": sum(1 for score in scores if score >= 75),
        "candidate_ge65_count": sum(1 for score in scores if score >= 65),
        "candidate_ge40_count": candidate_ge40_count,
        "candidate_eq0_count": candidate_eq0_count,
        "candidate_ge_pass_threshold_count": candidate_ge_pass_count,
        "candidate_ge_warning_threshold_count": candidate_ge_warning_count,
        "pass_threshold": pass_threshold,
        "warning_threshold": warning_threshold,
    }

def build_secondary_warnings(summary: dict) -> list[dict]:
    """
    월간 식단 결과의 보조 경고 목록을 만든다.

    style_validation은 선택한 스타일이 잘 반영되었는지 보는 1차 검증이고,
    secondary_warnings는 그 외에 사용자 경험상 아쉬울 수 있는 부분을 알려준다.
    """

    warnings = []

    average_difficulty_score = summary.get("average_difficulty_score", 0)
    average_preference_score = summary.get("average_preference_score", 0)
    average_diversity_score = summary.get("average_diversity_score", 0)
    duplicate_menu_count = summary.get("duplicate_menu_count", 0)
    selected_menu_count = summary.get("selected_menu_count", 0)

    if selected_menu_count > 0:
        duplicate_rate = duplicate_menu_count / selected_menu_count
    else:
        duplicate_rate = 0

    if average_difficulty_score < 60:
        warnings.append({
            "type": "difficulty",
            "level": "warning",
            "message": "평균 조리 난이도 점수가 낮아 사용자에게 조리 부담이 있을 수 있습니다.",
            "value": average_difficulty_score,
            "recommended_minimum": 60
        })

    if average_preference_score < 60:
        warnings.append({
            "type": "preference",
            "level": "warning",
            "message": "선호도 점수가 낮아 사용자 취향 반영이 약할 수 있습니다.",
            "value": average_preference_score,
            "recommended_minimum": 60
        })

    if average_diversity_score < 75:
        warnings.append({
            "type": "diversity",
            "level": "warning",
            "message": "다양성 점수가 낮아 유사 메뉴 반복 가능성이 있습니다.",
            "value": average_diversity_score,
            "recommended_minimum": 75
        })

    if duplicate_rate >= 0.30:
        warnings.append({
            "type": "duplicate_menu",
            "level": "warning",
            "message": "월간 식단 내 동일 메뉴 반복 비율이 높아 다양성 보완이 필요합니다.",
            "value": duplicate_menu_count,
            "rate": round(duplicate_rate, 3),
            "recommended_maximum_rate": 0.30,
        })
    elif duplicate_rate >= 0.15:
        warnings.append({
            "type": "duplicate_menu",
            "level": "info",
            "message": "월간 식단 내 동일 메뉴가 일부 반복되었지만 허용 가능한 수준입니다.",
            "value": duplicate_menu_count,
            "rate": round(duplicate_rate, 3),
            "recommended_maximum_rate": 0.30,
        })

    return warnings


def build_recommendation_hint(
    selected_style: dict,
    validation_status: str
) -> str:
    """
    스타일 검증 결과에 따른 다음 개선 방향 힌트를 만든다.
    """

    source_goal = selected_style.get("source_goal")

    if validation_status == "pass":
        return "현재 선택한 스타일이 월간 식단에 안정적으로 반영되었습니다."

    if source_goal == "고단백":
        return "고단백 스타일에서는 단백질 25g 이상 메뉴를 우선 배치하거나, protein 기준 soft constraint를 강화할 수 있습니다."

    if source_goal == "다이어트":
        return "다이어트 스타일에서는 지방 25g 이상 메뉴의 감점을 강화하고, 평균 칼로리 기준을 더 엄격하게 적용할 수 있습니다."

    if source_goal == "영양 균형":
        return "영양 균형 스타일에서는 탄수화물, 단백질, 지방 비율이 안정적인 메뉴를 더 우선하도록 balance 점수 가중치를 조정할 수 있습니다."

    if source_goal == "식비 절약":
        return "가성비 스타일에서는 월 예산 사용률과 한 끼 예산 초과율을 기준으로 예산 soft constraint를 강화할 수 있습니다."

    if source_goal == "간편식":
        return "간편식 스타일에서는 조리 시간, 재료 수, 조리 단계 수를 함께 반영해 난이도 점수를 더 세분화할 수 있습니다."

    if source_goal == "맛 중심":
        return "취향 맞춤식에서는 선호 카테고리와 선호 재료군 일치도를 더 강하게 반영할 수 있습니다."

    return "선택한 스타일의 검증 기준을 추가로 정의할 수 있습니다."


def enrich_style_validation(
    style_validation: dict,
    selected_style: dict,
    summary: dict,
    difficulty_feasibility_diagnostics: dict | None = None,
) -> dict:
    """
    기본 style_validation 결과에 보조 경고와 개선 힌트를 추가한다.

    스타일 자체 기준은 통과해도,
    동일 메뉴 반복이 많으면 사용자 경험상 완전한 pass로 보기 어렵다.
    """

    secondary_warnings = build_secondary_warnings(summary)

    duplicate_menu_count = summary.get("duplicate_menu_count", 0)
    selected_menu_count = summary.get("selected_menu_count", 0)

    validation_status = style_validation.get("status", "unknown")

    if selected_menu_count > 0:
        duplicate_rate = duplicate_menu_count / selected_menu_count
    else:
        duplicate_rate = 0

    adjusted_style_validation = dict(style_validation)

    if validation_status == "pass" and duplicate_rate >= 0.30:
        adjusted_style_validation["status"] = "warning"
        adjusted_style_validation["message"] = (
            adjusted_style_validation.get("message", "")
            + " 다만 동일 메뉴 반복 비율이 높아 월간 식단 다양성 보완이 필요합니다."
        )

    recommendation_hint = build_recommendation_hint(
        selected_style=selected_style,
        validation_status=adjusted_style_validation.get("status", "unknown")
    )

    if difficulty_feasibility_diagnostics:
        diagnostics = dict(adjusted_style_validation.get("diagnostics", {}))
        diagnostics["difficulty_feasibility"] = difficulty_feasibility_diagnostics
        adjusted_style_validation["diagnostics"] = diagnostics

    return {
        **adjusted_style_validation,
        "secondary_warnings": secondary_warnings,
        "recommendation_hint": recommendation_hint
    }