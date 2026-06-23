"""
FILE: price_collector_v2.py
ROLE: 네이버 쇼핑 API 기반 단위당 가격 계산 및 지식그래프(Product 노드) 계층형 적재 엔진
"""
import os
import re
import time
import html
import requests
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class PriceCollectorV2:
    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"), 
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "your_password"))
        )

    def extract_weight(self, title: str) -> float:
        """상품명에서 중량(g, kg, ml)을 추출하여 g 단위로 변환"""
        # 1. kg -> g 변환 (예: 1.5kg -> 1500)
        kg_match = re.search(r'(\d+\.?\d*)\s*kg', title, re.I)
        if kg_match:
            return float(kg_match.group(1)) * 1000
        
        # 2. g 또는 ml 추출 (예: 500g, 500ml)
        g_match = re.search(r'(\d+)\s*(g|ml)', title, re.I)
        if g_match:
            return float(g_match.group(1))
        
        return 0.0

    def clean_title(self, raw_title: str) -> str:
        """네이버 HTML 태그 및 엔티티 노이즈 전면 제거"""
        cleaned = re.sub(r'<[^>]*>', '', raw_title) # 모든 HTML 태그 제거 (<b> 등)
        return html.unescape(cleaned).strip()       # &amp; 등을 순수 문자로 복원

    def get_naver_price_data(self, query: str):
        url = "https://openapi.naver.com/v1/search/shop.json"
        headers = {"X-Naver-Client-Id": self.client_id, "X-Naver-Client-Secret": self.client_secret}
        params = {"query": query, "display": 10, "sort": "sim"} # 유사도 순 상위 10개 분석
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code != 200: 
                return None
        except Exception:
            return None
        
        items = response.json().get('items', [])
        valid_items = []

        for item in items:
            title = self.clean_title(item['title'])
            price = int(item['lprice'])
            link = item['link']
            weight = self.extract_weight(title)

            if weight > 0:
                # 100g당 가격 계산
                unit_price = round((price / weight) * 100, 2)
                valid_items.append({
                    "price": price,
                    "unit_price": unit_price,
                    "name": title,
                    "link": link,
                    "weight": weight
                })

        # 단위당 최저가(가성비) 기준으로 정렬하여 가장 저렴한 상품 반환
        if valid_items:
            return min(valid_items, key=lambda x: x['unit_price'])
        return None

    def update_db(self):
        with self.driver.session() as session:
            # 수집 대상 식재료 추출
            ingredients = session.run("MATCH (i:Ingredient) RETURN i.name AS name")
            
            # 리스트로 변환하여 세션이 닫히거나 꼬이는 현상 방지
            ingredient_names = [record['name'] for record in ingredients]
            
            print(f"🚀 총 {len(ingredient_names)}개의 식재료 대상 네이버 쇼핑 최저가 추적을 시작합니다.")
            
            for name in ingredient_names:
                # 네이버 API Rate Limit 방어 (초당 요청수 제한 회피)
                time.sleep(0.1) 
                
                data = self.get_naver_price_data(name)
                
                if data:
                    # 💡 [구조 교정]: Ingredient 내부 속성이 아니라, 독립된 Product 노드를 만들고 관계 연결
                    cypher = """
                    MATCH (i:Ingredient {name: $ingredient_name})
                    MERGE (p:Product {name: $product_name})
                    SET p.price = $price,
                        p.unit_price = $unit_price,
                        p.link = $link,
                        p.platform = "NaverShopping",
                        p.delivery_type = "일반배송",
                        p.last_updated = datetime()
                    MERGE (i)-[:AVAILABLE_AS]->(p)
                    """
                    session.run(
                        cypher, 
                        ingredient_name=name,
                        product_name=data['name'],
                        price=data['price'],
                        unit_price=data['unit_price'],
                        link=data['link']
                    )
                    print(f"✅ {name} ➔ [네이버 통합 완료]: {data['name']} (100g당 {data['unit_price']}원)")
                else:
                    print(f"⚠️ {name} ➔ 중량 정보 포함 상품을 찾지 못해 건너뜁니다.")

if __name__ == "__main__":
    collector = PriceCollectorV2()
    try:
        collector.update_db()
    finally:
        collector.driver.close()