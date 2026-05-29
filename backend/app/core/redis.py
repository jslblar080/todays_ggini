import redis.asyncio as aioredis
from app.core.config import settings

# 비동기식 Redis 클라이언트 객체 생성
redis_client = aioredis.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    encoding="utf-8",
    decode_responses=True # 데이터를 받아올 때 bytes가 아닌 문자열(str)로 자동 변환
)

async def get_redis():
    """FastAPI Dependency Injection용 Redis 세션 주입 함수"""
    return redis_client