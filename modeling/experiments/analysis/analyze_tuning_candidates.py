import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def safe_float(value, default=0.0):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default


def classify_tuning_candidate(row: dict) -> list[dict]:
    """
    validation summary row를 기반으로 튜닝 필요 영역을 분류한다.
    """

    candidates = []

    scenario_id = row.get("scenario_id")
    description = row.get("description") or ""
    validation_status = row.get("validation_status")
    validation_message = row.get("validation_message") or ""

    average_protein = safe_float(row.get("average_protein"))
    average_difficulty_score = safe_float(row.get("average_difficulty_score"))
    average_preference_score = safe_float(row.get("average_preference_score"))
    duplicate_rate = safe_float(row.get("duplicate_rate"))
    unique_menu_ratio = safe_float(row.get("unique_menu_ratio"))
    fallback_used = bool(row.get("fallback_used"))
    fallback_reasons = row.get("fallback_reasons") or ""

    # 1. 조리 난이도 / 간편식
    if (
        validation_status == "fail"
        and "조리 난이도" in validation_message
    ) or average_difficulty_score < 60:
        candidates.append({
            "type": "difficulty",
            "priority": "P1" if validation_status == "fail" else "P2",
            "reason": "조리 난이도 점수가 낮아 간편식/낮은 조리 실력 사용자 경험이 떨어질 수 있음",
            "metric": {
                "average_difficulty_score": average_difficulty_score,
            },
            "suggested_action": "OR-Tools objective에 difficulty penalty 또는 easy cooking bonus 추가",
        })

    # 2. 고단백
    if "고단백" in validation_message or "고단백" in description:
        if average_protein < 25:
            priority = "P1"
        elif average_protein < 28:
            priority = "P2"
        else:
            priority = "P3"

        if average_protein < 28:
            candidates.append({
                "type": "high_protein",
                "priority": priority,
                "reason": "고단백 목표 대비 평균 단백질이 목표 기준에 부족하거나 여유가 작음",
                "metric": {
                    "average_protein": average_protein,
                    "recommended_minimum_protein": 28,
                },
                "suggested_action": "protein bonus weight 또는 고단백 후보 필터링/확장 정책 점검",
            })

    # 3. 반복 메뉴 / 다양성
    if duplicate_rate >= 0.30:
        candidates.append({
            "type": "diversity_duplicate",
            "priority": "P1" if duplicate_rate >= 0.40 else "P2",
            "reason": "동일 메뉴 반복 비율이 높아 월간 식단 다양성이 낮음",
            "metric": {
                "duplicate_rate": duplicate_rate,
                "unique_menu_ratio": unique_menu_ratio,
            },
            "suggested_action": "repeat penalty 추가 강화, 후보 pool 확대, max_repeat_per_menu 정책 점검",
        })
    elif duplicate_rate >= 0.15:
        candidates.append({
            "type": "diversity_duplicate",
            "priority": "P3",
            "reason": "동일 메뉴 반복이 일부 존재하지만 치명적 수준은 아님",
            "metric": {
                "duplicate_rate": duplicate_rate,
                "unique_menu_ratio": unique_menu_ratio,
            },
            "suggested_action": "현재는 모니터링 우선, 다른 목표 튜닝 후 재확인",
        })

    # 4. 선호도
    if (
        "취향" in validation_message
        or "선호" in validation_message
        or average_preference_score < 60
    ):
        candidates.append({
            "type": "preference",
            "priority": "P2" if average_preference_score < 60 else "P3",
            "reason": "선호 카테고리/재료 반영이 약하거나 fallback으로 선호 조건이 완화됨",
            "metric": {
                "average_preference_score": average_preference_score,
                "fallback_used": fallback_used,
                "fallback_reasons": fallback_reasons,
            },
            "suggested_action": "preference score weight, 선호 카테고리 relaxation 단계, fallback 메시지 개선",
        })

    # 5. 예산
    if "예산" in validation_message or "식비" in description:
        if validation_status in ["fail", "warning"]:
            candidates.append({
                "type": "budget",
                "priority": "P2" if "여유가 크지는" in validation_message else "P3",
                "reason": "예산 조건은 만족하지만 예산 여유 또는 반복 메뉴와 trade-off가 있음",
                "metric": {
                    "validation_status": validation_status,
                    "validation_message": validation_message,
                    "duplicate_rate": duplicate_rate,
                },
                "suggested_action": "예산 objective와 다양성 penalty 사이 균형 점검",
            })

    # 6. 영양 균형
    if "영양 균형" in validation_message or "영양 균형" in description:
        if validation_status in ["warning", "fail"]:
            candidates.append({
                "type": "nutrition_balance",
                "priority": "P3" if validation_status == "warning" else "P2",
                "reason": "탄단지 비율이 기준에는 걸리지만 치명적 실패는 아님",
                "metric": {
                    "average_protein": average_protein,
                    "average_calories": safe_float(row.get("average_calories")),
                    "average_fat": safe_float(row.get("average_fat")),
                },
                "suggested_action": "balance validation threshold 또는 macro ratio scoring 점검",
            })

    return candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    path = Path(args.input)
    data = json.loads(path.read_text(encoding="utf-8"))

    rows = data.get("rows", [])
    summary = data.get("summary", {})

    grouped = defaultdict(list)
    priority_counter = Counter()
    type_counter = Counter()

    for row in rows:
        candidates = classify_tuning_candidate(row)

        for candidate in candidates:
            item = {
                "scenario_id": row.get("scenario_id"),
                "description": row.get("description"),
                "validation_status": row.get("validation_status"),
                "validation_message": row.get("validation_message"),
                **candidate,
            }

            grouped[candidate["type"]].append(item)
            priority_counter[candidate["priority"]] += 1
            type_counter[candidate["type"]] += 1

    print("=" * 100)
    print("[TUNING CANDIDATE SUMMARY]")
    print("=" * 100)
    print("source:", path)
    print("scenario_count:", summary.get("scenario_count"))
    print("success_rate:", summary.get("success_rate"))
    print("solver_success_rate:", summary.get("solver_success_rate"))
    print("meal_coverage_rate:", summary.get("meal_coverage_rate"))
    print("validation_status_count:", summary.get("validation_status_count"))
    print("duplicate_rate:", summary.get("duplicate_rate"))
    print("unique_menu_ratio:", summary.get("unique_menu_ratio"))
    print()
    print("priority_count:", dict(priority_counter))
    print("type_count:", dict(type_counter))

    for tuning_type, items in grouped.items():
        print()
        print("=" * 100)
        print(f"[{tuning_type}]")
        print("=" * 100)

        for item in sorted(items, key=lambda x: x["priority"]):
            print()
            print("-" * 100)
            print("priority:", item["priority"])
            print("scenario_id:", item["scenario_id"])
            print("description:", item["description"])
            print("validation_status:", item["validation_status"])
            print("validation_message:", item["validation_message"])
            print("reason:", item["reason"])
            print("metric:", item["metric"])
            print("suggested_action:", item["suggested_action"])


if __name__ == "__main__":
    main()
