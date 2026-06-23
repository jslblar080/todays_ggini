"""
FILE: recipe_infinite_scraper.py
ROLE: 제한 없이 만개의 레시피를 전수 수집하며, 메모리 누수 및 차단을 방어하는 무한 가동 스크랩 엔진
"""
import os
import time
import random
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

class RecipeInfiniteScraper:
    def __init__(self):
        self.output_file = "data/raw_mankae_recipes.jsonl"
        os.makedirs("data", exist_ok=True)
        
        self.options = Options()
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("window-size=1920x1080")
        self.options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.browser = None
        self._init_browser()
        self.scraped_count = 0

    def _init_browser(self):
        """메모리 청소를 위해 브라우저를 주기적으로 안전하게 재기동하는 레이어"""
        if self.browser:
            try:
                self.browser.quit()
                print("🧹 [메모리 최적화] 기존 브라우저 세션을 안전하게 종료하고 메모리를 비웁니다.")
            except: pass
            time.sleep(2)

        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        self.browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def scrape_recipe_detail(self, recipe_id: str) -> dict:
        url = f"https://www.10000recipe.com/recipe/{recipe_id}"
        try:
            self.browser.get(url)
            time.sleep(random.uniform(2.0, 3.5)) # 매너 대기 속도 버프 적용
            
            title = ""
            title_els = self.browser.find_elements(By.CSS_SELECTOR, "div.view2_summary h3, div.view_title h3")
            if title_els: title = title_els[0].text.strip()
            if not title: return None

            servings, cooking_time, difficulty = "2인분", "20분 이내", "아무나"
            info1 = self.browser.find_elements(By.CSS_SELECTOR, "span.view2_summary_info1")
            info2 = self.browser.find_elements(By.CSS_SELECTOR, "span.view2_summary_info2")
            info3 = self.browser.find_elements(By.CSS_SELECTOR, "span.view2_summary_info3")
            if info1: servings = info1[0].text.strip()
            if info2: cooking_time = info2[0].text.strip()
            if info3: difficulty = info3[0].text.strip()

            ingredients_structured = []
            confirmed_area = self.browser.find_elements(By.ID, "divConfirmedMaterialArea")
            if confirmed_area:
                li_elements = confirmed_area[0].find_elements(By.TAG_NAME, "li")
                for li in li_elements:
                    try:
                        name_el = li.find_element(By.CSS_SELECTOR, "div.ingre_list_name")
                        unit_el = li.find_element(By.CSS_SELECTOR, "span.ingre_list_ea")
                        raw_name = re.sub(r'(최저가|구매|쇼핑).*', '', name_el.text).strip()
                        if raw_name:
                            ingredients_structured.append({"name": raw_name, "amount": unit_el.text.strip()})
                    except: continue

            if not ingredients_structured:
                ing_container = self.browser.find_elements(By.ID, "divIngredientArea")
                if ing_container:
                    for li in ing_container[0].find_elements(By.TAG_NAME, "li"):
                        try:
                            name_text = li.find_element(By.CSS_SELECTOR, "div.ing_name, div.ingre_list_name").text.strip()
                            amount_text = li.find_element(By.CSS_SELECTOR, "span.ing_unit, span.ingre_list_ea").text.strip()
                            name_text = re.sub(r'(최저가|구매|쇼핑).*', '', name_text).strip()
                            if name_text: ingredients_structured.append({"name": name_text, "amount": amount_text})
                        except: continue

            coupang_products = []
            goods_section = self.browser.find_elements(By.ID, "relationGoods")
            if goods_section:
                goods_lis = goods_section[0].find_elements(By.CSS_SELECTOR, "li.common_rcp_list_li")
                for g_li in goods_lis:
                    try:
                        link_url = g_li.find_element(By.CSS_SELECTOR, "a.common_rcp_link").get_attribute("href")
                        p_title = g_li.find_element(By.CSS_SELECTOR, "div.common_rcp_caption_tit").text.strip()
                        price_text = g_li.find_element(By.CSS_SELECTOR, "strong.common_rcp_caption_price").text.strip()
                        p_price = int(re.sub(r'[^0-9]', '', price_text)) if price_text else 0
                        is_rocket = True if g_li.find_elements(By.CSS_SELECTOR, "img[alt='로켓배송']") else False
                        coupang_products.append({
                            "product_title": p_title, "purchase_link": link_url, "lowest_price": p_price, "delivery_type": "로켓배송" if is_rocket else "일반배송"
                        })
                    except: continue

            steps = []
            step_divs = self.browser.find_elements(By.CSS_SELECTOR, "div.view_step_cont, div.step_cont")
            for idx, s_div in enumerate(step_divs, 1):
                try:
                    txt = s_div.find_element(By.CSS_SELECTOR, "div.media-body").text.strip()
                    if txt: steps.append(f"Step {idx}: {txt}")
                except: continue

            return {
                "recipe_id": recipe_id, "title": title, "servings": servings, "cooking_time": cooking_time,
                "difficulty": difficulty, "ingredients": ingredients_structured, "coupang_e_commerce": coupang_products,
                "steps": steps, "source_url": url
            }
        except Exception:
            return None

    def run_infinite_batch(self, start_page: int = 1):
        """갯수 제한 없이 사이트 끝까지 파고드는 무한 루프 코어"""
        base_list_url = "https://www.10000recipe.com/recipe/list.html?order=reco&page="
        page = start_page
        
        print("🔥 [무한 전수 수집 기동] 갯수 제한 없는 폭주 모드 크롤러를 실행합니다.", flush=True)
        
        with open(self.output_file, "a", encoding="utf-8") as f:
            while True: # 💡 상한선 제거: 무한 루프 돌입
                print(f"\n📁 [PAGE {page}] 무제한 수집 엔진 전진 중...", flush=True)
                list_url = f"{base_list_url}{page}"
                
                try:
                    self.browser.get(list_url)
                    time.sleep(random.uniform(2.5, 4.0))
                    
                    # 더 이상 페이지가 없거나 빈 결과 화면이면 종료
                    if "검색결과가 없습니다" in self.browser.page_source or page > 7000:
                        print("🎉 만개의 레시피 데이터베이스의 끝에 도달했습니다. 수집을 종료합니다.")
                        break

                    links = self.browser.find_elements(By.TAG_NAME, "a")
                    recipe_ids = []
                    for l in links:
                        try:
                            href = l.get_attribute('href')
                            if href and "/recipe/" in href and not "list.html" in href:
                                match = re.search(r'/recipe/(\d+)', href)
                                if match: recipe_ids.append(match.group(1))
                        except: continue
                                
                    recipe_ids = list(set(recipe_ids))
                    
                    if not recipe_ids:
                        print("ℹ️ 더 이상 추출할 레시피 카드가 없습니다. 수집을 마무리합니다.")
                        break
                        
                    print(f"   📌 후보군 {len(recipe_ids)}개 진입 시작.", flush=True)
                    
                    for rid in recipe_ids:
                        # 💡 200건 수집할 때마다 크롬 브라우저 클린 재기동 (메모리 뻑남 원천 방어)
                        if self.scraped_count > 0 and self.scraped_count % 200 == 0:
                            self._init_browser()
                            
                        time.sleep(random.uniform(2.0, 3.5))
                        
                        data = self.scrape_recipe_detail(rid)
                        if data and data["ingredients"]:
                            f.write(json.dumps(data, ensure_ascii=False) + "\n")
                            f.flush()
                            os.fsync(f.fileno()) # 물리 디스크 실시간 각인
                            
                            self.scraped_count += 1
                            print(f"      ✅ [{self.scraped_count}] 적재 완료: {data['title'][:10]}... [쿠팡상품:{len(data['coupang_e_commerce'])}개]", flush=True)
                    
                    page += 1 # 다음 페이지로 강제 전진
                        
                except Exception as e:
                    print(f"\n   ⚠️ 루프 튕김 방지 감지 (재복구 후 계속): {e}", flush=True)
                    time.sleep(5)
                    self._init_browser() # 에러 시 브라우저 세션 클리어 후 복귀
                    continue

        print(f"\n🎉 대장정이 끝났습니다! 총 {self.scraped_count}개의 마스터 원천 소스 확보 완료.")

if __name__ == "__main__":
    scraper = RecipeInfiniteScraper()
    try:
        # 1페이지부터 멈추지 않고 끝까지 긁어모읍니다.
        scraper.run_infinite_batch(start_page=1)
    finally:
        if scraper.browser: scraper.browser.quit()