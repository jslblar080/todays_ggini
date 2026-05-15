import httpx
from app.core.config import settings

async def request_ai_meal_plan(payload: dict):
    """
    모델링 파트의 AI 서버로 식단 생성 요청을 보냅니다.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(settings.AI_MODEL_SERVER_URL, json=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # 실패 시 에러 핸들링 (로그 기록 등)
            print(f"AI Server Error: {e}")
            return None