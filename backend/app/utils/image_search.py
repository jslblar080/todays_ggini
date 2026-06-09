import httpx
import logging
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

# OpenAI 비동기 클라이언트 선언
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY, max_retries=1)

# 이미지 매핑용 고유 접두사와 캐시 만료 기간(30일) 설정
REDIS_CACHE_PREFIX = "food_image:"
CACHE_TTL_DAYS = 1
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(3.0, connect=1.5),
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
)

# 이미지 매핑이 완전히 실패하거나 타임아웃 시 반환할 디폴트 이미지 URL
DEFAULT_FOOD_IMAGE_URL = "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=500"

async def _get_optimized_keyword(menu_name: str) -> str:
    """
    [1단계] LLM 기반 검색 쿼리 전처리 최적화
    한국어 메뉴명을 Pixabay에서 검색이 잘되는 영문 핵심 키워드로 변환합니다.
    """
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a professional image search query optimizer for a stock photo API. "
                        "Convert the given Korean food/meal name into 1 or 2 high-quality, generic English keywords. "
                        "CRITICAL RULES:\n"
                        "1. Output ONLY 1 or 2 raw keywords separated by a space, nothing else.\n"
                        "2. NEVER use special characters, accents, or non-English alphabets (e.g., use 'Fricassee' instead of 'Fricassée').\n"
                        "3. If the dish is too specific or rare, simplify it into a widely available broad concept (e.g., European chicken stews -> 'Chicken Stew').\n"
                        "4. Never use prepositions like 'with', 'of', or 'and'.\n"
                    )
                },
                {"role": "user", "content": menu_name}
            ],
            temperature=0.1,  # 값이 낮을수록 AI가 헛소리를 안 하고 일관된 답변을 냅니다.
            max_tokens=10     # 토큰 제한을 걸어 비용을 아낍니다.
        )
        
        # AI가 뱉은 결과물에서 앞뒤 공백을 제거
        keyword = response.choices[0].message.content.strip()
        print(f"🔮 [Query Optimization] {menu_name} -> {keyword}")
        return keyword

    except Exception as e:
        logger.error(f"LLM 쿼리 최적화 실패 (기본 메뉴명 Fallback 사용): {e}")
        return menu_name  # 에러 발생 시 시스템이 멈추지 않게 원래 이름을 그대로 반환

async def _search_pixabay_images(keyword: str, category: str = "food") -> Optional[str]:
    """
    [2단계] Pixabay API 호출 (후보군 3개 확보)
    정제된 영문 키워드를 가지고 스톡 이미지 URL 최대 3개를 긁어옵니다.
    """
    url = "https://pixabay.com/api/"

    if not keyword or len(keyword.strip()) < 2:
        return []

    params = {
        "key": settings.PIXABAY_API_KEY,
        "q": keyword.strip(),        # 1단계에서 얻은 영문 키워드
        "image_type": "photo",
        "category": category,        # 정확도를 위해 food 카테고리로 제한
        "per_page": 3,               # VLM 검증용으로 상위 3개만 수집
        "safesearch": "true"
    }
    
    try:
        # 1차 시도: 음식 카테고리 내에서 정석 검색
        response = await http_client.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            hits = data.get("hits")
            if hits:
                return hits[0]["webformatURL"]
            
            # 💡 [진짜 원인 저격 고속 Fallback]
            # 1차 음식 카테고리에서 결과가 0개라면, 카테고리 딱지 필터('food')를 아예 제거하고 
            # 브라우저 주소창과 똑같은 '전체 카테고리 범위'로 초고속 재요청을 날립니다!
            if "category" in params:
                del params["category"]  # 👈 카테고리 제한 원천 해제!
                
                fallback_res = await http_client.get(url, params=params)
                if fallback_res.status_code == 200:
                    fb_data = fallback_res.json()
                    fb_hits = fb_data.get("hits")
                    if fb_hits:
                        logger.info(f"🔄 [Category Fallback Hit] '{keyword.strip()}' 카테고리 제한 해제로 구제 성공!")
                        return fb_hits[0]["webformatURL"]
        else:
            # 200이 아닐 경우 뱉은 쌩 텍스트 로그 확인용
            logger.error(f"❌ Pixabay 서버 에러 발생 (Status: {response.status_code}): {response.text[:100]}")
                
    except Exception as e:
        print(f"Pixabay API 연동 실패: {e}")
            
    return [] # 결과가 없거나 에러 시 빈 리스트 반환


async def get_food_image_url(menu_name: str, category: str = "food") -> str:
    """
    [Main Pipeline] AI 이미지 파이프라인 + 기존 Pixabay Fallback + Redis 캐싱 통합형 함수
    """
    cache_key = f"{REDIS_CACHE_PREFIX}{menu_name}_{category}"
    
    # 1. Redis 분산 캐시 확인 (Cache Hit)
    try:
        cached_url = await redis_client.get(cache_key)
        if cached_url:
            print(f"[Cache Hit] Redis에서 이미 캐싱된 이미지를 즉시 반환합니다: {menu_name}")
            return cached_url
    except Exception as e:
        print(f"Redis 조회 중 일시적 에러 발생: {e}")

    print(f"[Cache Miss] Redis에 데이터가 없어 AI 고도화 파이프라인을 가동합니다")

    # AI 기반 전처리 및 후보군 수집
    optimized_keyword = await _get_optimized_keyword(menu_name)
    final_img_url = await _search_pixabay_images(optimized_keyword, category)

    # 2. [Fallback 레이어] 최종 매핑 실패 시 디폴트 이미지 반환
    if not final_img_url:
        logger.warning(f"❌ 매핑 실패(결과 없음): {menu_name}")
        return DEFAULT_FOOD_IMAGE_URL  # 검색 자체가 완전 실패한 경우

    # 3. 원본을 썼든, AI 검증을 통과했든 최종 확정된 URL을 Redis에 캐싱하여 다음 요청부턴 돈이 안 들게 방어합니다.
    try:
        ttl_seconds = CACHE_TTL_DAYS * 24 * 60 * 60
        await redis_client.setex(name=cache_key, time=ttl_seconds, value=final_img_url)
        print(f"[Cache Write] {menu_name}의 결과 이미지 주소를 Redis에 30일간 캐싱 완료!")
    except Exception as e:
        print(f"Redis 캐시 쓰기 실패: {e}")

    return final_img_url