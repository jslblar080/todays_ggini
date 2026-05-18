import httpx
from app.core.config import settings

# 1. 메모리 캐시 딕셔너리 생성 (서버가 켜져 있는 동안 데이터를 기억합니다)
_IMAGE_CACHE = {}

async def get_food_image_url(menu_name: str, category: str) -> str:
    """
    메뉴 이름을 검색어로 Pixabay에서 음식 사진 URL을 가져옵니다.
    """
    cache_key = f"{menu_name}_{category}"
    
    # 💡 3. 캐시에 이미 해당 이미지 URL이 존재하면 즉시 반환 (API 호출 패스!)
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]
    
    url = "https://pixabay.com/api/"
    params = {
        "key": settings.PIXABAY_API_KEY,
        "q": menu_name,
        "image_type": "photo",
        "category": category,  # 음식 카테고리로 제한하여 정확도 향상
        "per_page": 3,
        "safesearch": "true"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data["hits"]:
                # 가장 연관성이 높은 첫 번째 이미지의 URL 반환
                img_url = data["hits"][0]["webformatURL"]
                # 💡 4. 다음에 똑같은 검색어가 들어올 때를 대비해 캐시에 저장
                _IMAGE_CACHE[cache_key] = img_url
                return img_url
            
        except Exception as e:
            print(f"이미지 검색 에러: {e}")
            
    # 검색 결과가 없거나 에러 발생 시 None 반환
    return None