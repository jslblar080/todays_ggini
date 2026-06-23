"""
FILE: coupang_collector.py
ROLE: 디버깅 모드 크롬에 접속하여 쿠팡의 배송 타입별 최저가 데이터를 차단 없이 수집
"""
import os
import time
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from neo4j import GraphDatabase
from langchain_ollama import OllamaLLM
from dotenv import load_dotenv

load_dotenv()

class CoupangCollector:
    def __init__(self):
        # Neo4j 연결
        self.driver_node = GraphDatabase.driver(
            os.getenv("NEO4J_URI"), 
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )
        # Ollama 초기화 (중량 및 가구 적합성 분석)
        self.llm = OllamaLLM(model="llama3", temperature=0)
        
        self.options = Options()
        # [핵심] 이미 실행 중인 디버깅 크롬 포트에 접속
        self.options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        self._init_browser()

    def _init_browser(self):
        try:
            # 원격 디버깅 모드에서는 Service 설정이 크게 의미 없으나 호환성을 위해 유지
            self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
            self.wait = WebDriverWait(self.browser, 15)
            print("🚀 디버깅 모드 크롬에 성공적으로 연결되었습니다.")
        except Exception as e:
            print(f"❌ 크롬 연결 실패: {e}")
            print("💡 팁: 터미널에서 --remote-debugging-port=9222 옵션으로 크롬을 먼저 실행하세요.")
            raise e

    def analyze_with_ollama(self, title: str):
        """Ollama를 사용하여 중량 추출 및 1~4인 가구 적합도 판정"""
        prompt = f"Product: {title}\n1. Total weight in grams (number only)\n2. Is it suitable for a 1-4 person household? (YES/NO)\nFormat: [weight]/[YES or NO]"
        try:
            res = self.llm.invoke(prompt).strip()
            weight_part, suitability_part = res.split('/')
            weight = float(re.sub(r'[^0-9.]', '', weight_part))
            return weight, suitability_part.strip().upper()
        except:
            return 0.0, "NO"

    def search_coupang(self, query: str):
        """실제 열려 있는 브라우저에서 쿠팡 검색 및 데이터 추출"""
        if not query or len(query.strip()) == 0: return None

        try:
            # 구글 검색 유입을 모사하거나 직접 검색 결과 페이지로 이동
            search_url = f"https://www.coupang.com/np/search?q={query}"
            self.browser.get(search_url)
            
            # 페이지 로딩 대기 (실제 브라우저이므로 조금 더 여유 있게)
            time.sleep(random.uniform(5.0, 7.0))

            # 상품 리스트 추출
            items = self.browser.find_elements(By.CSS_SELECTOR, "li.search-product")
            if not items:
                print(f"   ⚠️ [{query}] 상품 검색 결과가 없습니다.")
                return None

            categorized_results = {"로켓프레시": [], "로켓배송": [], "일반배송": []}

            for item in items[:8]: # 상위 8개 분석
                try:
                    title_el = item.find_element(By.CSS_SELECTOR, "div.name")
                    price_el = item.find_element(By.CSS_SELECTOR, "strong.price-value")
                    
                    title = title_el.text
                    price = int(re.sub(r'[^0-9]', '', price_el.text))
                    link = item.find_element(By.TAG_NAME, "a").get_attribute('href')
                    
                    # 배송 타입 확인
                    badge_text = item.text
                    if "로켓프레시" in badge_text: d_type = "로켓프레시"
                    elif "로켓배송" in badge_text or "로켓와우" in badge_text: d_type = "로켓배송"
                    else: d_type = "일반배송"

                    # Ollama 분석 (중량 및 적합성)
                    weight, is_suitable = self.analyze_with_ollama(title)

                    if is_suitable == "YES" and weight > 0:
                        unit_price = round((price / weight) * 100, 2)
                        # 상식적인 가성비 범위 내 데이터만 수집
                        if unit_price > 10:
                            categorized_results[d_type].append({
                                "price": price,
                                "unit_price": unit_price,
                                "title": title,
                                "link": link
                            })
                except: continue

            # 각 배송 타입별 최저가 상품 선정
            final_res = {}
            for d_type, products in categorized_results.items():
                final_res[d_type] = min(products, key=lambda x: x['unit_price']) if products else None
            
            return final_res

        except Exception as e:
            print(f"   ❌ [{query}] 검색/파싱 에러: {str(e)[:50]}")
            return None

    def update_coupang_prices(self):
        with self.driver_node.session() as session:
            # 전수 재수집 모드
            print("🚀 [전수 수집] 쿠팡의 실시간 배송 타입별 최저가를 수집합니다.")
            query = "MATCH (i:Ingredient) WHERE i.name IS NOT NULL AND i.name <> '물' RETURN i.name AS name"
            ingredients = session.run(query)
            
            for record in ingredients:
                name = record['name']
                print(f"🛒 쿠팡 수집 시도: {name}")
                results = self.search_coupang(name)
                
                if results:
                    session.run("""
                        MATCH (i:Ingredient {name: $name})
                        SET i.coupang_fresh_price = $fresh.price, i.coupang_fresh_link = $fresh.link,
                            i.coupang_rocket_price = $rocket.price, i.coupang_rocket_link = $rocket.link,
                            i.coupang_normal_price = $normal.price, i.coupang_normal_link = $normal.link,
                            i.coupang_updated = datetime()
                    """, 
                    name=name, 
                    fresh=results.get("로켓프레시") or {"price": None, "link": None},
                    rocket=results.get("로켓배송") or {"price": None, "link": None},
                    normal=results.get("일반배송") or {"price": None, "link": None}
                    )
                    
                    # 수집 결과 로그 출력
                    for d_type, data in results.items():
                        if data:
                            print(f"   ✅ [{d_type}] 100g당 {data['unit_price']}원 ({data['title'][:15]}...)")
                
                # 차단 방지를 위한 매너 대기
                time.sleep(random.uniform(8.0, 12.0))

    def close(self):
        # 디버깅 모드에서는 브라우저를 닫지 않는 것이 좋습니다 (사람이 계속 써야 할 수 있으므로)
        # self.browser.quit() 
        pass

if __name__ == "__main__":
    collector = CoupangCollector()
    try:
        collector.update_coupang_prices()
    finally:
        collector.close()