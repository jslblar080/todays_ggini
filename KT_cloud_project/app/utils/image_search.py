import httpx
from app.core.config import settings

async def get_food_image_url(menu_name: str, category: str) -> str:
    """
    메뉴 이름을 검색어로 Pixabay에서 음식 사진 URL을 가져옵니다.
    """
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
                return data["hits"][0]["webformatURL"]
        except Exception as e:
            print(f"이미지 검색 에러: {e}")
            
    # 검색 결과가 없거나 에러 발생 시 None 반환
    return None