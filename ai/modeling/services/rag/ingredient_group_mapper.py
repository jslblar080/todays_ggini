"""
RAG 후보 메뉴의 재료명을 Modeling 재료군으로 정규화한다.

주의:
- 이 모듈은 임의 추정이 아니라 명시적 alias 사전 기반 매핑만 수행한다.
- 매핑할 수 없는 재료명은 unknown으로 남긴다.
- RAG/Back 연동 payload schema는 변경하지 않는다.
"""

from __future__ import annotations


SUPPORTED_INGREDIENT_GROUPS = {
    "육류",
    "해산물류",
    "채소류",
    "식물성 단백질류",
    "계란 및 유제품류",
    "곡류",
    "양념류",
    "기타",
}


INGREDIENT_GROUP_ALIAS_MAP: dict[str, str] = {
    # 육류
    "소고기": "육류",
    "쇠고기": "육류",
    "돼지고기": "육류",
    "닭고기": "육류",
    "닭가슴살": "육류",
    "베이컨": "육류",
    "햄": "육류",
    "스팸": "육류",
    "소시지": "육류",
    "불고기": "육류",

    # 해산물류
    "새우": "해산물류",
    "오징어": "해산물류",
    "문어": "해산물류",
    "연어": "해산물류",
    "참치": "해산물류",
    "멸치": "해산물류",
    "굴": "해산물류",
    "조개": "해산물류",
    "홍합": "해산물류",

    # 채소류
    "양파": "채소류",
    "대파": "채소류",
    "쪽파": "채소류",
    "마늘": "채소류",
    "다진마늘": "채소류",
    "고추": "채소류",
    "청양고추": "채소류",
    "풋고추": "채소류",
    "당근": "채소류",
    "감자": "채소류",
    "고구마": "채소류",
    "시금치": "채소류",
    "버섯": "채소류",
    "표고버섯": "채소류",
    "새송이버섯": "채소류",
    "양배추": "채소류",
    "상추": "채소류",
    "깻잎": "채소류",
    "오이": "채소류",
    "토마토": "채소류",
    "파프리카": "채소류",
    "브로콜리": "채소류",
    "가지": "채소류",
    "무": "채소류",
    "배추": "채소류",
    "김치": "채소류",

    # 식물성 단백질류
    "두부": "식물성 단백질류",
    "순두부": "식물성 단백질류",
    "콩": "식물성 단백질류",
    "병아리콩": "식물성 단백질류",
    "렌틸콩": "식물성 단백질류",
    "유부": "식물성 단백질류",

    # 계란 및 유제품류
    "계란": "계란 및 유제품류",
    "달걀": "계란 및 유제품류",
    "계란후라이": "계란 및 유제품류",
    "치즈": "계란 및 유제품류",
    "피자치즈": "계란 및 유제품류",
    "우유": "계란 및 유제품류",
    "버터": "계란 및 유제품류",
    "요거트": "계란 및 유제품류",
    "생크림": "계란 및 유제품류",

    # 곡류
    "밥": "곡류",
    "쌀": "곡류",
    "현미": "곡류",
    "잡곡": "곡류",
    "면": "곡류",
    "라면": "곡류",
    "우동": "곡류",
    "파스타": "곡류",
    "스파게티면": "곡류",
    "또띠아": "곡류",
    "식빵": "곡류",
    "빵": "곡류",
    "밀가루": "곡류",
    "떡": "곡류",
    "고명밥": "곡류",

    # 양념류
    "소금": "양념류",
    "후추": "양념류",
    "설탕": "양념류",
    "올리고당": "양념류",
    "꿀": "양념류",
    "간장": "양념류",
    "굴소스": "양념류",
    "고추장": "양념류",
    "된장": "양념류",
    "맛술": "양념류",
    "식초": "양념류",
    "참기름": "양념류",
    "식용유": "양념류",
    "올리브오일": "양념류",
    "마요네즈": "양념류",
    "케첩": "양념류",
    "통깨": "양념류",
    "참깨": "양념류",
    "연겨자": "양념류",
}


def normalize_ingredient_name(name: str | None) -> str:
    """
    재료명 매핑을 위한 최소 정규화만 수행한다.
    """

    if name is None:
        return ""

    normalized = str(name).strip()
    normalized = normalized.replace(" ", "")

    # RAG 응답에서 "소고기(소고기 대체)"처럼 들어오는 경우 원 재료명만 사용한다.
    if "(" in normalized:
        normalized = normalized.split("(", 1)[0]

    return normalized


def map_ingredient_name_to_group(name: str | None) -> str | None:
    """
    단일 재료명을 명시적 alias 사전에 기반해 재료군으로 변환한다.
    """

    normalized = normalize_ingredient_name(name)

    if not normalized:
        return None

    if normalized in INGREDIENT_GROUP_ALIAS_MAP:
        return INGREDIENT_GROUP_ALIAS_MAP[normalized]

    return None


def infer_ingredient_groups_from_names(
    ingredient_names: list[str],
) -> tuple[list[str], dict]:
    """
    재료명 목록에서 재료군 목록을 생성한다.

    반환:
    - mapped_groups: 중복 제거된 재료군 목록
    - diagnostics: 매핑 성공/실패 진단 정보
    """

    mapped_groups: list[str] = []
    mapped_ingredients: list[dict] = []
    unknown_ingredients: list[str] = []

    for ingredient_name in ingredient_names:
        group = map_ingredient_name_to_group(ingredient_name)

        if group:
            if group not in mapped_groups:
                mapped_groups.append(group)

            mapped_ingredients.append({
                "ingredient_name": ingredient_name,
                "ingredient_group": group,
            })
        else:
            unknown_ingredients.append(ingredient_name)

    total_count = len(ingredient_names)
    mapped_count = len(mapped_ingredients)
    unknown_count = len(unknown_ingredients)

    coverage_rate = (
        round(mapped_count / total_count, 4)
        if total_count
        else 0
    )

    diagnostics = {
        "source": "explicit_alias_map",
        "total_ingredient_count": total_count,
        "mapped_ingredient_count": mapped_count,
        "unknown_ingredient_count": unknown_count,
        "coverage_rate": coverage_rate,
        "mapped_ingredients_preview": mapped_ingredients[:10],
        "unknown_ingredients_preview": unknown_ingredients[:10],
    }

    return mapped_groups, diagnostics


def extract_ingredient_names(candidate_menu: dict) -> list[str]:
    """
    candidate_menu에서 재료명 목록을 추출한다.

    우선순위:
    1. ingredients
    2. ingredient_usages[].ingredient_name
    """

    ingredients = candidate_menu.get("ingredients") or []

    if ingredients:
        return [
            ingredient
            for ingredient in ingredients
            if ingredient
        ]

    ingredient_usages = candidate_menu.get("ingredient_usages") or []

    return [
        usage.get("ingredient_name")
        for usage in ingredient_usages
        if usage.get("ingredient_name")
    ]


def fill_missing_ingredient_groups(candidate_menu: dict) -> tuple[list[str], dict]:
    """
    RAG 후보 메뉴에 ingredient_groups가 없을 경우 명시적 alias map 기반으로 보강한다.

    기존 ingredient_groups가 존재하면 그대로 사용한다.
    """

    existing_groups = candidate_menu.get("ingredient_groups") or []

    if existing_groups:
        return existing_groups, {
            "status": "existing_groups_used",
            "source": "rag_response",
            "group_count": len(existing_groups),
        }

    ingredient_names = extract_ingredient_names(candidate_menu)
    mapped_groups, diagnostics = infer_ingredient_groups_from_names(
        ingredient_names=ingredient_names,
    )

    return mapped_groups, {
        "status": (
            "mapped_from_ingredient_names"
            if mapped_groups
            else "mapping_unavailable"
        ),
        **diagnostics,
    }
