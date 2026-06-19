import redis.asyncio as aioredis
from app.core.config import settings
import uuid
from fastapi import HTTPException, status

# 비동기식 Redis 클라이언트 객체 생성
redis_client = aioredis.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    encoding="utf-8",
    decode_responses=True # 데이터를 받아올 때 bytes가 아닌 문자열(str)로 자동 변환
)

async def get_redis():
    """FastAPI Dependency Injection용 Redis 세션 주입 함수"""
    return redis_client

class ShortTermDistributedLock:
    """
    비동기 작업 투척 전, 순간적인 중복 연타(Race Condition)를 
    입구에서 1~2초간 짧게 컷하기 위한 고성능 분산 락 클래스입니다.
    """
    def __init__(self, client: aioredis.Redis, key: str, expire_seconds: int = 2):
        self.redis = client
        self.key = f"lock:meal_gen:{key}"
        self.expire_seconds = expire_seconds
        self.lock_value = str(uuid.uuid4())  # 내 락을 증명할 고유 티켓

    async def __aenter__(self):   # 락 획득
        acquired = await self.redis.set(
            self.key, self.lock_value, ex=self.expire_seconds, nx=True     # nx=True: "만약 이 Key가 Redis에 없을 때만 저장해라!"
        )
        
        if not acquired:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 식단 생성 작업이 진행 중입니다. 잠시만 대기해주세요."
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb): # 락 해제
        current_value = await self.redis.get(self.key)
        # decode_responses=True가 걸려있으므로 decode() 없이 바로 문자열 비교 가능!
        if current_value and current_value == self.lock_value:
            await self.redis.delete(self.key)