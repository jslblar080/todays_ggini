"""
FILE: price_collector_kurly.py
ROLE: 검색어 중첩 현상을 물리적으로 차단하고, 
      마켓컬리 검색 결과 카드 내부의 돔 구조 변경에 완벽히 대응하는 유저 모사형 크롤링 엔진
"""
import os
import re
import time
import random
from neo4j import GraphDatabase
from dotenv import load_dotenv

# 셀레니움 최신 가이드 규격 준수
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

class KurlyPriceCollector:
    def __init__(self):
        self.driver_driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"), 
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "your_password"))
        )
        self.browser = self._init_real_browser()

    def _init_real_browser(self):
        """💡 GUI 크롬 창을 띄우고 일반 유저 세션으로 완벽 위장"""
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1400,900")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # 자동화 로봇 탐지 방지 플래그
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        return driver

    def extract_weight(self, title: str) -> float:
        """상품명에서 중량(g, kg, ml)을 추출하여 g 단위로 표준화 변환"""
        kg_match = re.search(r'(\d+\.?\d*)\s*kg', title, re.I)
        if kg_match:
            return float(kg_match.group(1)) * 1000
        
        g_match = re.search(r'(\d+)\s*(g|ml)', title, re.I)
        if g_match:
            return float(g_match.group(1))
        return 0.0

    def scrape_kurly_lowest_product(self, query: str):
        """💡 글자 뭉침 원천 차단 및 상품 정보 유연 파싱 레이어가 적용된 핵심 스크래핑 시나리오"""
        try:
            if "kurly.com" not in self.browser.current_url:
                self.browser.get("https://www.kurly.com")
                time.sleep(random.uniform(1.5, 2.5))

            # 1. 상단 검색창 유연 추적 후보군 순회
            search_input_xpaths = [
                "//input[@id='search']",
                "//input[contains(@id, 'search')]",
                "//input[@type='search']",
                "//input[contains(@placeholder, '검색')]",
                "//header//input"
            ]
            
            search_input = None
            for xpath in search_input_xpaths:
                try:
                    search_input = WebDriverWait(self.browser, 1.5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    if search_input:
                        break
                except:
                    continue

            if not search_input:
                print(" ➔ ❌ [에러] 개편된 검색창 엘리먼트를 찾을 수 없습니다.", end="")
                return None
                
            # 2. 💡 [글자 뭉침 결함 완전 교정] 강제 포커싱 후 하드웨어 레벨 백스페이스 연타
            search_input.click()
            time.sleep(0.3)
            search_input.clear() # 1차 기본 클리어
            time.sleep(0.2)
            
            # 단축키 오작동 방지용 백스페이스 30회 수동 연타 루프 (기존 검색어 잔재 완전 소멸)
            for _ in range(30):
                search_input.send_keys(Keys.BACKSPACE)
            time.sleep(0.3)
            
            # 인간적인 속도로 검색어 입력 후 엔터
            search_input.send_keys(query)
            time.sleep(random.uniform(0.3, 0.6))
            search_input.send_keys(Keys.ENTER)
            
            # 3. 검색 결과 로딩 대기 (전체 상품 그리드 영역 또는 개별 카드 렌더링 확인)
            product_card_xpath = "//a[contains(@href, '/goods/')]"
            WebDriverWait(self.browser, 7).until(
                EC.presence_of_element_located((By.XPATH, product_card_xpath))
            )
            
            # 동적 이미지 및 가격 레이아웃 활성화를 위한 자연스러운 휠 다운
            self.browser.execute_script("window.scrollTo(0, 500);")
            time.sleep(random.uniform(1.0, 1.8))
            
            # 4. 💡 [정보 파싱 결함 완전 교정] 상품 카드 엘리먼트 전수 수집 및 내부 구조 완화 추적
            product_elements = self.browser.find_elements(By.XPATH, product_card_xpath)
            valid_items = []

            for elem in product_elements:
                try:
                    # 특정 태그(.//p, .//span) 맵핑 조건이 터지는 문제를 막기 위해,
                    # 하위 자식 노드 전체의 텍스트 줄바꿈 구조(\n)를 통째로 분석합니다.
                    raw_text = elem.text.strip()
                    if not raw_text:
                        continue
                        
                    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                    
                    # 마켓컬리 상품 카드는 일반적으로 [혜택/배송타입, 상품명, 가격, 후기] 순으로 줄바꿈 렌더링됩니다.
                    title = ""
                    price_str = ""
                    
                    # '원'이라는 글자가 포함된 행을 가격행으로 인식하고, 그 바로 직전 행을 상품명으로 동적 추론
                    for idx, line in enumerate(lines):
                        if "원" in line:
                            price_str = re.sub(r'[^\d]', '', line)
                            if idx > 0:
                                # 보통 가격 위에 상품명이 위치함
                                title = lines[idx - 1]
                            break
                    
                    # 텍스트 라인 추론이 빗나갔을 때를 대비한 2차 렐러티브 XPATH 백업 레이어
                    if not title or not price_str:
                        title_elem = elem.find_element(By.XPATH, ".//*[contains(@class, 'name') or self::p or self::span]")
                        price_elem = elem.find_element(By.XPATH, "//*[contains(text(), '원')]")
                        title = title_elem.text.strip()
                        price_str = re.sub(r'[^\d]', '', price_elem.text)

                    if not price_str or not title:
                        continue
                        
                    price = int(price_str)
                    href = elem.get_attribute('href')
                    
                    weight = self.extract_weight(title)
                    
                    if weight > 0 and price > 0:
                        unit_price = round((price / weight) * 100, 2)
                        valid_items.append({
                            "price": price,
                            "unit_price": unit_price,
                            "name": title,
                            "link": href
                        })
                except Exception:
                    continue

            if valid_items:
                return min(valid_items, key=lambda x: x['unit_price'])
                
        except Exception as e:
            print(f" ➔ ⚠️ 스캔 범위 아웃 또는 검색 지연 패스", end="")
            return None
        return None

    def update_db(self):
        with self.driver_driver.session() as session:
            ingredients = session.run("MATCH (i:Ingredient) RETURN i.name AS name")
            ingredient_names = [record['name'] for record in ingredients]
            
            print(f"🚀 총 {len(ingredient_names)}개의 식재료 대상 마켓컬리 '실물 브라우저 시뮬레이션(입력/파싱 교정형)' 최저가 수집을 시작합니다.")
            
            for name in ingredient_names:
                print(f"🔄 컬리 실시간 추적 중: {name}...", end="", flush=True)
                
                time.sleep(random.uniform(1.8, 3.0))
                
                data = self.scrape_kurly_lowest_product(name)
                
                if data:
                    cypher = """
                    MATCH (i:Ingredient {name: $ingredient_name})
                    MERGE (p:Product {name: $product_name})
                    SET p.price = $price,
                        p.unit_price = $unit_price,
                        p.link = $link,
                        p.platform = "MarketKurly",
                        p.delivery_type = "샛별배송",
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
                    print(f" ➔ 🟢 [샛별배송 매핑 완료]: {data['name']} (100g당 {data['unit_price']}원)")
                else:
                    print(" ➔ ⏭️ 일치 상품 부재 패스")

    def close(self):
        if self.browser: 
            self.browser.quit()
        if self.driver_driver: 
            self.driver_driver.close()

if __name__ == "__main__":
    collector = KurlyPriceCollector()
    try:
        collector.update_db()
    finally:
        collector.close()