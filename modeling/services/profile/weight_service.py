GOAL_WEIGHTS: dict[str, dict[str, float]] = {
    "식비 절약": {
        "budget": 0.45,
        "nutrition": 0.20,
        "preference": 0.15,
        "difficulty": 0.10,
        "diversity": 0.10,
    },
    "영양 균형": {
        "budget": 0.15,
        "nutrition": 0.45,
        "preference": 0.15,
        "difficulty": 0.10,
        "diversity": 0.15,
    },
    "다이어트": {
        "budget": 0.15,
        "nutrition": 0.40,
        "preference": 0.15,
        "difficulty": 0.10,
        "diversity": 0.20,
    },
    "고단백": {
        "budget": 0.15,
        "nutrition": 0.45,
        "preference": 0.15,
        "difficulty": 0.10,
        "diversity": 0.15,
    },
    "간편식": {
        "budget": 0.20,
        "nutrition": 0.15,
        "preference": 0.15,
        "difficulty": 0.40,
        "diversity": 0.10,
    },
    "맛 중심": {
        "budget": 0.10,
        "nutrition": 0.15,
        "preference": 0.45,
        "difficulty": 0.10,
        "diversity": 0.20,
    },
}


def get_weights_by_goals(goals: list[str]) -> dict[str, float]:
    """
    사용자가 선택한 여러 목표의 가중치를 평균 내서
    하나의 최종 가중치로 만든다.
    """

    if not goals:
        raise ValueError("최소 1개 이상의 목표를 선택해야 합니다.")

    if len(goals) > 3:
        raise ValueError("목표는 최대 3개까지만 선택할 수 있습니다.")

    weight_keys = ["budget", "nutrition", "preference", "difficulty", "diversity"]

    # 가중치 합산용 초기값
    merged_weights: dict[str, float] = {
        "budget": 0.0,
        "nutrition": 0.0,
        "preference": 0.0,
        "difficulty": 0.0,
        "diversity": 0.0,
    }

    # 선택된 목표들의 가중치를 모두 더한다.
    for goal in goals:
        if goal not in GOAL_WEIGHTS:
            raise ValueError(f"지원하지 않는 목표입니다: {goal}")

        goal_weight = GOAL_WEIGHTS[goal]

        for key in weight_keys:
            merged_weights[key] += goal_weight[key]

    # 목표 개수만큼 나눠 평균을 낸다.
    goal_count = len(goals)

    averaged_weights: dict[str, float] = {
        key: round(merged_weights[key] / goal_count, 4)
        for key in weight_keys
    }

    # 소수점 반올림으로 합이 1에서 살짝 벗어날 수 있으므로 정규화한다.
    total_weight = sum(averaged_weights.values())

    normalized_weights: dict[str, float] = {
        key: round(value / total_weight, 4)
        for key, value in averaged_weights.items()
    }

    return normalized_weights