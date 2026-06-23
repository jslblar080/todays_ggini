import json

from services.profile.user_input_service import load_sample_users
from services.profile.profile_service import build_user_profile_response

from services.rag.rag_request_service import (
    build_rag_request,
    calculate_candidate_count,
)
from services.rag.rag_client import request_candidate_menus_from_rag
from services.rag.rag_response_mapper import map_rag_response_to_candidate_menus

from services.style.meal_style_service import build_meal_style_candidates
from experiments.flows.monthly_plan_random_style_flow import (
    build_monthly_plan_by_random_style,
)


def print_json(title: str, data: dict) -> None:
    """
    제목과 함께 JSON 데이터를 보기 좋게 출력한다.
    """

    print(title)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def save_debug_result(debug_result: dict) -> None:
    """
    추천 흐름에서 오고 가는 주요 JSON 데이터를 debug_result.json으로 저장한다.

    이 파일은 최종 결과용이 아니라,
    Back / Modeling / RAG 사이에서 어떤 데이터가 오고 가는지 확인하기 위한 테스트용 파일이다.
    """

    with open("debug_result.json", "w", encoding="utf-8") as file:
        json.dump(
            debug_result,
            file,
            ensure_ascii=False,
            indent=2
        )


def build_back_to_modeling_sample_request(user_input: dict) -> dict:
    """
    Back에서 Modeling으로 3일치 샘플 식단 추천을 요청하는 JSON 구조를 만든다.

    실제 서비스에서는 Front에서 받은 사용자 입력을 Back이 저장한 뒤,
    이 구조로 Modeling에 전달한다고 가정한다.
    """

    return {
        "user_id": user_input["user_id"],
        "request_type": "meal_style_candidates",
        "profile": user_input["profile"]
    }


def build_back_to_modeling_monthly_request(
    user_input: dict,
    selected_style: dict
) -> dict:
    """
    Back에서 Modeling으로 월간 식단 생성을 요청하는 JSON 구조를 만든다.

    실제 서비스에서는 사용자가 3일치 샘플 후보 중 하나를 선택하면,
    Back이 selected_style 정보를 함께 Modeling에 전달한다고 가정한다.
    """

    return {
        "user_id": user_input["user_id"],
        "request_type": "monthly_plan",
        "selected_style": {
            "style_id": selected_style.get("style_id"),
            "style_name": selected_style.get("style_name"),
            "source_goal": selected_style.get("source_goal"),
            "focus_key": selected_style.get("focus_key")
        },
        "profile": user_input["profile"]
    }


def calculate_sample_candidate_count(
    meal_count_per_day: int,
    sample_period_days: int,
    style_count: int = 3,
    buffer_multiplier: int = 3
) -> int:
    """
    3일치 스타일 후보 생성을 위한 RAG 후보 메뉴 개수를 계산한다.

    스타일 후보는 3개가 생성되므로,
    단순히 3일치 식단 수만큼만 후보를 받으면 스타일별 메뉴가 겹칠 가능성이 높다.

    따라서 필요한 식사 수에 스타일 개수와 여유 배수를 곱해
    스타일별로 서로 다른 후보를 선택할 수 있도록 한다.
    """

    return meal_count_per_day * sample_period_days * style_count * buffer_multiplier


def main() -> None:
    """
    모델링 추천 흐름 테스트용 main 함수이다.

    현재 테스트 흐름:
    1. 샘플 사용자 중 특정 사용자 선택
    2. Back → Modeling 3일치 샘플 추천 요청 JSON 생성
    3. Modeling 내부 사용자 profile 생성
    4. Modeling → RAG 3일치 샘플 후보 요청
    5. RAG 응답을 Modeling 추천용 메뉴 구조로 변환
    6. Modeling → Back 3일치 샘플 후보 추천 결과 생성
    7. Modeling → RAG 월간 후보 요청
    8. RAG 응답을 Modeling 추천용 메뉴 구조로 변환
    9. 테스트용으로 스타일 하나를 선택해 월간 식단 생성
    10. Back → Modeling 월간 식단 요청 JSON 예시 생성
    11. 전체 데이터 흐름을 debug_result.json으로 저장
    """

    debug_result = {}

    # ============================================================
    # 0단계: 테스트 사용자 선택
    # ============================================================

    sample_users = load_sample_users()

    user_input = next(
        user for user in sample_users
        if user["user_id"] == "user_004"
    )

    print(f"랜덤 선택 사용자\n{user_input['user_id']}\n")
    print_json("사용자 입력 원본", user_input)

    # ============================================================
    # 1단계: Back → Modeling 3일치 샘플 추천 요청
    # ============================================================

    back_to_modeling_sample_request = build_back_to_modeling_sample_request(
        user_input=user_input
    )

    print_json(
        "\nBack → Modeling 3일치 샘플 추천 요청 JSON",
        back_to_modeling_sample_request
    )

    debug_result["back_to_modeling_sample_request"] = back_to_modeling_sample_request

    # ============================================================
    # 2단계: Modeling 내부 사용자 profile 생성
    # ============================================================

    modeling_profile_response = build_user_profile_response(
        request_data=back_to_modeling_sample_request
    )

    print_json(
        "\nModeling 내부 사용자 프로필 응답",
        modeling_profile_response
    )

    debug_result["modeling_profile_response"] = modeling_profile_response

    user_id = modeling_profile_response["user_id"]
    profile = modeling_profile_response["profile"]

    # 기존 함수 호환을 위해 profile만 따로 저장한다.
    debug_result["modeling_profile"] = profile

    # ============================================================
    # 3단계: Modeling → RAG 3일치 샘플 후보 요청
    # ============================================================

    sample_candidate_count = calculate_sample_candidate_count(
        meal_count_per_day=profile["meal_count_per_day"],
        sample_period_days=profile.get("sample_period_days", 3),
        style_count=3,
        buffer_multiplier=3
    )

    sample_rag_request = build_rag_request(
        user_input=user_input,
        profile=profile,
        candidate_count=sample_candidate_count
    )

    print_json(
        "\nModeling → RAG 3일 샘플 후보 요청 JSON",
        sample_rag_request
    )

    debug_result["modeling_to_rag_sample_request"] = sample_rag_request

    # ============================================================
    # 4단계: RAG → Modeling 3일치 샘플 후보 응답
    # ============================================================

    sample_rag_response = request_candidate_menus_from_rag(
        sample_rag_request
    )

    debug_result["rag_to_modeling_sample_response"] = sample_rag_response

    mapped_sample_rag_result = map_rag_response_to_candidate_menus(
        sample_rag_response
    )

    debug_result["mapped_sample_candidate_menus"] = mapped_sample_rag_result

    sample_candidate_menus = mapped_sample_rag_result["candidate_menus"]

    # ============================================================
    # 5단계: Modeling → Back 3일치 샘플 후보 추천 결과
    # ============================================================

    meal_style_response = build_meal_style_candidates(
        user_id=user_id,
        profile=profile,
        candidate_menus=sample_candidate_menus,
        sample_period_days=profile.get("sample_period_days", 3),
        meal_count_per_day=profile["meal_count_per_day"]
    )

    print_json(
        "\nModeling → Back 3일치 샘플 후보 추천 JSON",
        meal_style_response
    )

    debug_result["modeling_to_back_sample_response"] = meal_style_response

    # ============================================================
    # 6단계: Modeling → RAG 월간 후보 요청
    # ============================================================

    monthly_candidate_count = calculate_candidate_count(
        meal_count_per_day=profile["meal_count_per_day"],
        period_days=profile.get("period_days", 30),
        buffer_multiplier=3
    )

    monthly_rag_request = build_rag_request(
        user_input=user_input,
        profile=profile,
        candidate_count=monthly_candidate_count
    )

    print_json(
        "\nModeling → RAG 월간 후보 요청 JSON",
        monthly_rag_request
    )

    debug_result["modeling_to_rag_monthly_request"] = monthly_rag_request

    # ============================================================
    # 7단계: RAG → Modeling 월간 후보 응답
    # ============================================================

    monthly_rag_response = request_candidate_menus_from_rag(
        monthly_rag_request
    )

    debug_result["rag_to_modeling_monthly_response"] = monthly_rag_response

    mapped_monthly_rag_result = map_rag_response_to_candidate_menus(
        monthly_rag_response
    )

    debug_result["mapped_monthly_candidate_menus"] = mapped_monthly_rag_result

    monthly_candidate_menus = mapped_monthly_rag_result["candidate_menus"]

    # ============================================================
    # 8단계: 테스트용 월간 식단 생성
    # ============================================================

    monthly_plan_response = build_monthly_plan_by_random_style(
        user_id=user_id,
        candidate_menus=monthly_candidate_menus,
        profile=profile,
        meal_style_response=meal_style_response
    )

    selected_style_summary = monthly_plan_response["selected_style"]

    debug_result["selected_style"] = selected_style_summary

    # ============================================================
    # 9단계: Back → Modeling 월간 식단 요청 JSON 예시 생성
    # ============================================================

    back_to_modeling_monthly_request = build_back_to_modeling_monthly_request(
        user_input=user_input,
        selected_style=selected_style_summary
    )

    print_json(
        "\nBack → Modeling 월간 식단 추천 요청 JSON",
        back_to_modeling_monthly_request
    )

    debug_result["back_to_modeling_monthly_request"] = back_to_modeling_monthly_request

    # ============================================================
    # 10단계: Modeling → Back 월간 식단 추천 결과
    # ============================================================

    print_json("\nModeling → Back 월간 식단 추천 결과 JSON", monthly_plan_response)

    debug_result["modeling_to_back_monthly_response"] = monthly_plan_response

    # ============================================================
    # 11단계: 전체 데이터 흐름 저장
    # ============================================================

    save_debug_result(debug_result)


if __name__ == "__main__":
    main()