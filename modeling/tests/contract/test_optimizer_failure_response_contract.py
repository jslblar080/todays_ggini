from services import modeling_service


def build_common_kwargs(
    solver_status: str,
) -> dict:
    return {
        "user_id": "test-user",
        "selected_style": {
            "style_id": "test-style",
            "style_name": "테스트 스타일",
            "source_goal": "영양 균형",
            "focus_key": "nutrition",
        },
        "base_profile": {},
        "monthly_profile": {},
        "period_days": 30,
        "meal_count_per_day": 3,
        "available_recommendation_count": 120,
        "optimizer_result": {
            "success": False,
            "solver_status": solver_status,
            "objective_value": None,
            "message": "solver test result",
        },
        "optimizer_input": {
            "monthly_budget": 300000,
            "max_repeat_per_menu": 3,
            "solver_time_limit_seconds": 20,
            "required_meal_count": 90,
            "optimizer_config": {},
        },
        "fallback_info": {
            "warnings": [],
            "fallback_used": False,
            "fallback_steps": [],
        },
        "profiling": {
            "ortools_solver_time_ms": 20000,
        },
    }


def test_unknown_response_has_distinct_failure_reason() -> None:
    response = modeling_service.build_optimizer_unknown_monthly_response(
        **build_common_kwargs("UNKNOWN")
    )

    assert response["id"] == "test-user"
    assert response["request_type"] == "monthly_plan"
    assert response["success"] is False
    assert response["failure_reason"] == "optimizer_unknown"

    optimizer = response["monthly_plan"]["optimizer"]

    assert optimizer["solver_status"] == "UNKNOWN"
    assert response["monthly_plan"]["days"] == []


def test_dispatcher_routes_unknown_to_unknown_builder(
    monkeypatch,
) -> None:
    captured = {}

    def fake_unknown_builder(**kwargs) -> dict:
        captured.update(kwargs)
        return {
            "failure_reason": "optimizer_unknown",
        }

    def fail_if_infeasible_builder_called(**kwargs) -> dict:
        raise AssertionError(
            "UNKNOWN 상태에서 infeasible builder가 호출되었습니다."
        )

    monkeypatch.setattr(
        modeling_service,
        "build_optimizer_unknown_monthly_response",
        fake_unknown_builder,
    )
    monkeypatch.setattr(
        modeling_service,
        "build_optimizer_infeasible_monthly_response",
        fail_if_infeasible_builder_called,
    )

    response = modeling_service.build_optimizer_failure_monthly_response(
        **build_common_kwargs("UNKNOWN")
    )

    assert response["failure_reason"] == "optimizer_unknown"
    assert captured["optimizer_result"]["solver_status"] == "UNKNOWN"


def test_dispatcher_routes_infeasible_to_infeasible_builder(
    monkeypatch,
) -> None:
    captured = {}

    def fail_if_unknown_builder_called(**kwargs) -> dict:
        raise AssertionError(
            "INFEASIBLE 상태에서 unknown builder가 호출되었습니다."
        )

    def fake_infeasible_builder(**kwargs) -> dict:
        captured.update(kwargs)
        return {
            "failure_reason": "optimizer_infeasible",
        }

    monkeypatch.setattr(
        modeling_service,
        "build_optimizer_unknown_monthly_response",
        fail_if_unknown_builder_called,
    )
    monkeypatch.setattr(
        modeling_service,
        "build_optimizer_infeasible_monthly_response",
        fake_infeasible_builder,
    )

    response = modeling_service.build_optimizer_failure_monthly_response(
        **build_common_kwargs("INFEASIBLE")
    )

    assert response["failure_reason"] == "optimizer_infeasible"
    assert captured["optimizer_result"]["solver_status"] == "INFEASIBLE"


def test_monthly_success_response_has_explicit_contract_fields() -> None:
    from services.plan.plan_payload_service import (
        build_modeling_to_back_monthly_response,
    )

    response = build_modeling_to_back_monthly_response(
        user_id=1,
        selected_style={
            "style_id": "balanced",
            "style_name": "균형형",
            "source_goal": "영양 균형",
            "focus_key": "nutrition",
        },
        base_profile={},
        monthly_profile={},
        monthly_plan={
            "period_days": 1,
            "meal_count_per_day": 1,
            "required_meal_count": 1,
            "warnings": [],
            "fallback": {},
            "summary": {},
            "style_validation": {},
            "days": [],
        },
        actual_recommendation_count=1,
    )

    assert response["id"] == 1
    assert response["request_type"] == "monthly_plan"
    assert response["success"] is True
    assert response["failure_reason"] is None
