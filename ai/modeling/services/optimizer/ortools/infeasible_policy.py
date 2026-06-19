from __future__ import annotations

from contextvars import ContextVar
from typing import Any


SUCCESS_SOLVER_STATUSES = {"OPTIMAL", "FEASIBLE"}

_OPTIMIZER_INFEASIBLE_POLICY_EVENTS: ContextVar[list[dict] | None] = ContextVar(
    "optimizer_infeasible_policy_events",
    default=None,
)


def clear_optimizer_infeasible_policy_diagnostics() -> None:
    """
    실험 실행 단위에서 optimizer infeasible policy diagnostics를 초기화한다.

    서비스 응답 payload에는 포함하지 않고,
    experiment result artifact에만 저장한다.
    """

    _OPTIMIZER_INFEASIBLE_POLICY_EVENTS.set([])


def record_optimizer_infeasible_policy_diagnostics(policy: dict) -> None:
    """
    생성된 infeasible policy를 현재 실험 context에 기록한다.
    """

    events = _OPTIMIZER_INFEASIBLE_POLICY_EVENTS.get()

    if events is None:
        return

    events.append(policy)


def get_optimizer_infeasible_policy_diagnostics() -> dict:
    """
    현재 실험 context에 기록된 infeasible policy diagnostics를 반환한다.
    """

    events = list(_OPTIMIZER_INFEASIBLE_POLICY_EVENTS.get() or [])

    return {
        "event_count": len(events),
        "events": events,
    }


def is_solver_success(solver_status: str | None) -> bool:
    """
    서비스에 사용할 수 있는 OR-Tools solver 상태인지 판단한다.
    """

    return solver_status in SUCCESS_SOLVER_STATUSES


def build_active_constraint_contexts(
    monthly_profile: dict,
    optimizer_input: dict,
    fallback_info: dict,
    required_meal_count: int,
    available_recommendation_count: int,
) -> list[dict[str, Any]]:
    """
    INFEASIBLE 발생 시 활성화되어 있던 제약 조건 context를 구조화한다.

    이 함수는 실패 원인을 단정하지 않는다.
    실제 입력에 존재하는 제약 조건과 후보 진단 정보를 그대로 정리한다.
    """

    candidate_diagnostics = fallback_info.get("candidate_diagnostics") or {}

    contexts: list[dict[str, Any]] = [
        {
            "type": "slot_requirement",
            "active": required_meal_count > 0,
            "evidence": {
                "required_meal_count": required_meal_count,
                "period_days": monthly_profile.get("period_days"),
                "meal_count_per_day": monthly_profile.get("meal_count_per_day"),
            },
        },
        {
            "type": "candidate_pool",
            "active": available_recommendation_count > 0,
            "evidence": {
                "available_recommendation_count": available_recommendation_count,
                "candidate_pool_is_enough": candidate_diagnostics.get("is_enough"),
                "candidate_pool_shortage_reasons": candidate_diagnostics.get(
                    "shortage_reasons",
                    [],
                ),
                "recommended_next_step": candidate_diagnostics.get(
                    "recommended_next_step"
                ),
            },
        },
        {
            "type": "budget_constraint",
            "active": bool(optimizer_input.get("monthly_budget")),
            "evidence": {
                "monthly_budget": optimizer_input.get("monthly_budget"),
            },
        },
        {
            "type": "repeat_constraint",
            "active": bool(optimizer_input.get("max_repeat_per_menu")),
            "evidence": {
                "max_repeat_per_menu": optimizer_input.get("max_repeat_per_menu"),
                "repeat_penalty_weight": optimizer_input.get("repeat_penalty_weight"),
            },
        },
        {
            "type": "preference_constraint",
            "active": bool(monthly_profile.get("preferred_categories")),
            "evidence": {
                "preferred_categories": monthly_profile.get(
                    "preferred_categories",
                    [],
                ),
                "ingredient_preferences": monthly_profile.get(
                    "ingredient_preferences",
                    [],
                ),
            },
        },
        {
            "type": "allergy_constraint",
            "active": bool(monthly_profile.get("allergy_ingredients")),
            "evidence": {
                "allergy_ingredients": monthly_profile.get(
                    "allergy_ingredients",
                    [],
                ),
            },
        },
        {
            "type": "diversity_constraint",
            "active": bool(monthly_profile.get("diversity_level")),
            "evidence": {
                "diversity_level": monthly_profile.get("diversity_level"),
            },
        },
    ]

    return [context for context in contexts if context["active"]]


def build_relaxation_actions(
    active_constraint_contexts: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """
    활성 제약 조건에 대응 가능한 조정 action 목록을 만든다.

    이 함수는 실패 원인을 단정하지 않는다.
    활성화된 조건에 대해 사용자가 조정할 수 있는 선택지만 제공한다.
    """

    action_map = {
        "budget_constraint": {
            "type": "adjust_budget",
            "label": "예산 조건 조정",
            "description": "월 예산을 조정하면 가능한 식단 조합이 늘어날 수 있습니다.",
        },
        "slot_requirement": {
            "type": "adjust_meal_count",
            "label": "식사 수 조정",
            "description": "하루 식사 수를 조정하면 필요한 식단 slot 수가 줄어들 수 있습니다.",
        },
        "candidate_pool": {
            "type": "request_more_candidates",
            "label": "후보 메뉴 추가 요청",
            "description": "후보 메뉴를 추가로 확보한 뒤 다시 최적화를 시도할 수 있습니다.",
        },
        "preference_constraint": {
            "type": "expand_preferences",
            "label": "선호 조건 조정",
            "description": "선호 카테고리 또는 재료군 범위를 조정할 수 있습니다.",
        },
        "allergy_constraint": {
            "type": "review_allergy_alternatives",
            "label": "알레르기 대체 조건 확인",
            "description": "알레르기 조건과 충돌하지 않는 대체 재료를 확인할 수 있습니다.",
        },
        "diversity_constraint": {
            "type": "adjust_diversity",
            "label": "다양성 조건 조정",
            "description": "다양성 조건을 조정하면 반복 허용 범위가 달라질 수 있습니다.",
        },
        "repeat_constraint": {
            "type": "adjust_repeat_limit",
            "label": "메뉴 반복 제한 조정",
            "description": "동일 메뉴 반복 제한을 조정하면 가능한 조합이 늘어날 수 있습니다.",
        },
    }

    actions: list[dict[str, str]] = []
    used_action_types: set[str] = set()

    for context in active_constraint_contexts:
        context_type = context["type"]
        evidence = context.get("evidence") or {}

        if context_type == "candidate_pool":
            candidate_pool_is_enough = evidence.get("candidate_pool_is_enough")
            recommended_next_step = evidence.get("recommended_next_step")

            if (
                candidate_pool_is_enough is True
                and recommended_next_step == "use_current_candidates"
            ):
                continue

        action = action_map.get(context_type)

        if not action:
            continue

        if action["type"] in used_action_types:
            continue

        actions.append(action)
        used_action_types.add(action["type"])

    if not actions:
        actions.append({
            "type": "adjust_conditions",
            "label": "조건 조정",
            "description": "현재 조건을 일부 조정한 뒤 다시 생성할 수 있습니다.",
        })

    return actions


def build_optimizer_infeasible_policy(
    monthly_profile: dict,
    optimizer_result: dict,
    optimizer_input: dict,
    fallback_info: dict,
    available_recommendation_count: int,
    required_meal_count: int,
) -> dict[str, Any]:
    """
    OR-Tools INFEASIBLE 또는 non-success solver 결과에 대한 공통 policy를 만든다.

    원인을 임의로 추정하지 않고,
    실제 활성화된 조건과 조정 가능한 action만 구조화한다.
    """

    solver_status = optimizer_result.get("solver_status")
    candidate_diagnostics = fallback_info.get("candidate_diagnostics") or {}

    active_constraint_contexts = build_active_constraint_contexts(
        monthly_profile=monthly_profile,
        optimizer_input=optimizer_input,
        fallback_info=fallback_info,
        required_meal_count=required_meal_count,
        available_recommendation_count=available_recommendation_count,
    )

    relaxation_actions = build_relaxation_actions(
        active_constraint_contexts=active_constraint_contexts,
    )

    candidate_pool_is_enough = candidate_diagnostics.get("is_enough")

    policy = {
        "policy_name": "optimizer_infeasible_common_policy",
        "failure_reason": "optimizer_infeasible",
        "solver_status": solver_status,
        "is_solver_success": is_solver_success(solver_status),
        "diagnosis_principle": (
            "solver 실패 원인을 임의로 단정하지 않고, "
            "실제 입력과 candidate diagnostics에 존재하는 활성 조건만 기록한다."
        ),
        "candidate_pool_is_enough": candidate_pool_is_enough,
        "active_constraint_contexts": active_constraint_contexts,
        "relaxation_actions": relaxation_actions,
        "diagnostic_summary": {
            "required_meal_count": required_meal_count,
            "available_recommendation_count": available_recommendation_count,
            "candidate_pool_is_enough": candidate_pool_is_enough,
            "candidate_pool_shortage_reasons": candidate_diagnostics.get(
                "shortage_reasons",
                [],
            ),
            "recommended_next_step": candidate_diagnostics.get(
                "recommended_next_step"
            ),
            "monthly_budget": optimizer_input.get("monthly_budget"),
            "max_repeat_per_menu": optimizer_input.get("max_repeat_per_menu"),
            "optimizer_candidate_limit": optimizer_input.get(
                "optimizer_candidate_limit"
            ),
            "used_optimizer_candidate_count": optimizer_input.get(
                "used_optimizer_candidate_count"
            ),
            "solver_time_limit_seconds": optimizer_input.get(
                "solver_time_limit_seconds"
            ),
        },
    }

    record_optimizer_infeasible_policy_diagnostics(policy)

    return policy


def build_optimizer_infeasible_user_guidance_from_policy(
    infeasible_policy: dict,
) -> dict[str, Any]:
    """
    공통 infeasible policy를 기존 response payload와 호환되는 사용자 안내 구조로 변환한다.

    서비스 응답 payload 구조는 변경하지 않는다.
    상세 policy와 active_constraint_contexts는 experiment diagnostics에만 저장한다.
    """

    relaxation_actions = infeasible_policy.get("relaxation_actions") or []
    diagnostic_summary = infeasible_policy.get("diagnostic_summary") or {}

    active_contexts = infeasible_policy.get("active_constraint_contexts") or []

    def find_context(context_type: str) -> dict:
        for context in active_contexts:
            if context.get("type") == context_type:
                return context.get("evidence") or {}
        return {}

    preference_context = find_context("preference_constraint")
    allergy_context = find_context("allergy_constraint")
    diversity_context = find_context("diversity_constraint")

    required_meal_count = diagnostic_summary.get("required_meal_count")
    monthly_budget = diagnostic_summary.get("monthly_budget")

    budget_per_meal = None
    if monthly_budget and required_meal_count:
        budget_per_meal = round(monthly_budget / required_meal_count, 2)

    return {
        "title": "현재 조건으로는 월간 식단 조합을 찾지 못했어요.",
        "description": (
            "후보 메뉴와 입력 조건을 기준으로 OR-Tools가 가능한 조합을 찾지 못했습니다. "
            "조건을 일부 조정하면 다시 생성할 수 있습니다."
        ),
        "primary_actions": [
            {
                "type": action["type"],
                "label": action["label"],
            }
            for action in relaxation_actions[:3]
        ],
        "recommended_actions": [
            action["description"]
            for action in relaxation_actions
        ],
        "diagnostic_summary": {
            "solver_status": infeasible_policy.get("solver_status"),
            "monthly_budget": monthly_budget,
            "required_meal_count": required_meal_count,
            "budget_per_meal": budget_per_meal,
            "available_recommendation_count": diagnostic_summary.get(
                "available_recommendation_count"
            ),
            "max_repeat_per_menu": diagnostic_summary.get("max_repeat_per_menu"),
            "optimizer_candidate_limit": diagnostic_summary.get(
                "optimizer_candidate_limit"
            ),
            "used_optimizer_candidate_count": diagnostic_summary.get(
                "used_optimizer_candidate_count"
            ),
            "diversity_level": diversity_context.get("diversity_level"),
            "preferred_category_count": len(
                preference_context.get("preferred_categories") or []
            ),
            "ingredient_preference_count": len(
                preference_context.get("ingredient_preferences") or []
            ),
            "allergy_ingredient_count": len(
                allergy_context.get("allergy_ingredients") or []
            ),
        },
    }
