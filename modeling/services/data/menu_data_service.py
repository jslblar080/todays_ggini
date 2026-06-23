import json
from pathlib import Path

from services.rag.rag_response_mapper import map_rag_response_to_candidate_menus


def load_sample_menus() -> list[dict]:
    """
    sample_rag_response_200.json 파일에서 RAG 응답 형식의 샘플 데이터를 읽어온다.

    기존에는 sample_menus.json의 메뉴 리스트를 바로 반환했지만,
    이제는 RAG 응답 구조를 먼저 Modeling 추천 로직용 메뉴 구조로 변환한 뒤 반환한다.
    """

    file_path = Path("data/sample_rag_response_200.json")

    with open(file_path, "r", encoding="utf-8") as file:
        rag_response = json.load(file)

    mapped_result = map_rag_response_to_candidate_menus(rag_response)

    return mapped_result["candidate_menus"]