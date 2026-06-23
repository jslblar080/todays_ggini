import json
import random


def load_sample_users(file_path: str = "data/sample_users.json") -> list[dict]:
    """
    sample_users.json에서 사용자 입력 mock 데이터를 불러온다.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        users = json.load(file)

    return users


def select_random_user_input(file_path: str = "data/sample_users.json") -> dict:
    """
    여러 사용자 입력 mock 데이터 중 하나를 랜덤으로 선택한다.
    """

    users = load_sample_users(file_path)

    if not users:
        raise ValueError("사용자 mock 데이터가 비어 있습니다.")

    return random.choice(users)