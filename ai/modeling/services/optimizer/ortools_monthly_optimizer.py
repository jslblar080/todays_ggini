from ortools.sat.python import cp_model


def calculate_cost_penalty(
    estimated_cost: int,
    cost_penalty_divisor: int,
) -> int:
    """
    메뉴 비용 penalty를 계산한다.

    CP-SAT 목적 함수는 정수 기반이므로,
    estimated_cost를 일정 단위로 나누어 penalty로 사용한다.

    예:
    - estimated_cost = 5,000
    - cost_penalty_divisor = 100
    - cost_penalty = 50
    """

    if estimated_cost <= 0:
        return 0

    if cost_penalty_divisor <= 0:
        return 0

    return int(round(estimated_cost / cost_penalty_divisor))


def solve_monthly_plan_with_ortools(optimizer_input: dict) -> dict:
    """
    OR-Tools CP-SAT을 이용해 월간 식단 메뉴 배치를 수행한다.

    1차 개선 범위:
    - 각 슬롯에 메뉴 1개 선택
    - 동일 메뉴 반복 횟수 제한
    - final_score 합계 최대화
    - estimated_cost 기반 비용 penalty 적용
    - 같은 메뉴 2회 선택 시 반복 penalty 적용
    """

    slots = optimizer_input["slots"]
    menus = optimizer_input["menus"]

    max_repeat_per_menu = optimizer_input.get("max_repeat_per_menu", 2)
    time_limit = optimizer_input.get("solver_time_limit_seconds", 10)

    # 목적 함수 weight
    score_weight = optimizer_input.get("score_weight", 100)
    cost_penalty_weight = optimizer_input.get("cost_penalty_weight", 1)
    cost_penalty_divisor = optimizer_input.get("cost_penalty_divisor", 100)
    repeat_penalty_weight = optimizer_input.get("repeat_penalty_weight", 300)
    monthly_budget = int(optimizer_input.get("monthly_budget") or 0)

    if not slots:
        return {
            "success": False,
            "solver_status": "NO_SLOTS",
            "selected_items": [],
            "message": "식단 슬롯이 없습니다.",
        }

    if not menus:
        return {
            "success": False,
            "solver_status": "NO_CANDIDATE_MENUS",
            "selected_items": [],
            "message": "OR-Tools에 입력할 후보 메뉴가 없습니다.",
        }

    model = cp_model.CpModel()

    decision_vars = {}

    for slot_index, _slot in enumerate(slots):
        for menu in menus:
            menu_index = menu["index"]
            decision_vars[(slot_index, menu_index)] = model.NewBoolVar(
                f"x_s{slot_index}_m{menu_index}"
            )

    # 제약 1: 각 슬롯에는 메뉴가 정확히 1개 선택되어야 한다.
    for slot_index, _slot in enumerate(slots):
        model.Add(
            sum(
                decision_vars[(slot_index, menu["index"])]
                for menu in menus
            ) == 1
        )

    # 제약 2: 같은 메뉴가 월간 식단에 과도하게 반복되지 않도록 제한한다.
    menu_usage_vars = {}

    for menu in menus:
        menu_index = menu["index"]

        usage_count = sum(
            decision_vars[(slot_index, menu_index)]
            for slot_index, _slot in enumerate(slots)
        )

        menu_usage_vars[menu_index] = usage_count

        model.Add(usage_count <= max_repeat_per_menu)

    # 제약 3: 월간 총 예상 비용이 사용자 예산을 넘지 않도록 제한한다.
    if monthly_budget > 0:
        total_estimated_cost_expr = sum(
            decision_vars[(slot_index, menu["index"])]
            * int(menu.get("estimated_cost", 0) or 0)
            for slot_index, _slot in enumerate(slots)
            for menu in menus
        )

        model.Add(total_estimated_cost_expr <= monthly_budget)

    # 목적 함수:
    # final_score는 높일수록 좋고,
    # estimated_cost와 같은 메뉴 반복은 낮출수록 좋다.
    objective_terms = []

    for slot_index, _slot in enumerate(slots):
        for menu in menus:
            menu_index = menu["index"]

            score = int(round(menu.get("final_score", 0) * score_weight))
            cost_penalty = calculate_cost_penalty(
                estimated_cost=int(menu.get("estimated_cost", 0) or 0),
                cost_penalty_divisor=cost_penalty_divisor,
            )

            objective_terms.append(
                decision_vars[(slot_index, menu_index)]
                * (
                    score
                    - (cost_penalty * cost_penalty_weight)
                )
            )

    # 반복 penalty:
    # max_repeat_per_menu=2인 상황에서 같은 메뉴가 2회 선택되면 penalty를 준다.
    # usage_count가 2 이상인지 여부를 BoolVar로 표현한다.
    repeat_penalty_terms = []

    if max_repeat_per_menu >= 2 and repeat_penalty_weight > 0:
        for menu in menus:
            menu_index = menu["index"]
            usage_count = menu_usage_vars[menu_index]

            repeated_var = model.NewBoolVar(f"repeated_m{menu_index}")

            # repeated_var = 1이면 usage_count >= 2
            model.Add(usage_count >= 2).OnlyEnforceIf(repeated_var)
            model.Add(usage_count <= 1).OnlyEnforceIf(repeated_var.Not())

            repeat_penalty_terms.append(
                repeated_var * repeat_penalty_weight
            )

    model.Maximize(
        sum(objective_terms)
        - sum(repeat_penalty_terms)
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit)
    solver.parameters.num_workers = 8

    status = solver.Solve(model)

    status_name = solver.StatusName(status)

    if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        return {
            "success": False,
            "solver_status": status_name,
            "selected_items": [],
            "objective_value": None,
            "message": "OR-Tools가 가능한 식단 조합을 찾지 못했습니다.",
            "optimizer_config": {
                "score_weight": score_weight,
                "cost_penalty_weight": cost_penalty_weight,
                "cost_penalty_divisor": cost_penalty_divisor,
                "repeat_penalty_weight": repeat_penalty_weight,
                "max_repeat_per_menu": max_repeat_per_menu,
                "solver_time_limit_seconds": time_limit,
                "monthly_budget": monthly_budget,
            },
        }

    selected_items = []

    for slot_index, slot in enumerate(slots):
        for menu in menus:
            menu_index = menu["index"]
            variable = decision_vars[(slot_index, menu_index)]

            if solver.Value(variable) == 1:
                selected_items.append({
                    "day": slot["day"],
                    "meal_order": slot["meal_order"],
                    "menu_index": menu_index,
                    "menu_id": menu.get("menu_id"),
                    "selected_menu": menu["raw_menu"],
                })
                break

    return {
        "success": True,
        "solver_status": status_name,
        "selected_items": selected_items,
        "objective_value": solver.ObjectiveValue(),
        "message": "OR-Tools 월간 식단 최적화가 완료되었습니다.",
        "optimizer_config": {
            "score_weight": score_weight,
            "cost_penalty_weight": cost_penalty_weight,
            "cost_penalty_divisor": cost_penalty_divisor,
            "repeat_penalty_weight": repeat_penalty_weight,
            "max_repeat_per_menu": max_repeat_per_menu,
            "solver_time_limit_seconds": time_limit,
            "monthly_budget": monthly_budget,
        },
    }
