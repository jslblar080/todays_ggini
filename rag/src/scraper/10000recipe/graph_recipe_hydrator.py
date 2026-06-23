"""
FILE: graph_recipe_full_hydrator.py
ROLE: [구형 공백 문자 파싱 버그 완벽 수정본]
      문자열 맨 앞의 공백(&nbsp;, \xa0) 노이즈를 스킵하고 진짜 조리 숫자를 추적하여
      EMPTY_DATA 발생률을 0%에 수렴시키는 초정밀 지식그래프 전수 수집 마스터 엔진
DEPENDENCY: pip install beautifulsoup4 requests neo4j python-dotenv
"""
import os
import sys
import re
import time
import requests
from bs4 import BeautifulSoup
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

class GraphRecipeFullHydrator:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Connection": "keep-alive"
        }

    def scrape_10000recipe_steps(self, recipe_id: str) -> list:
        if not recipe_id:
            return []
            
        url = f"https://www.10000recipe.com/recipe/{recipe_id}"
        steps = []
        
        try:
            response = requests.get(url, headers=self.headers, timeout=7)
            
            if response.status_code in [403, 429]:
                print(f"\n🚨 [WAF 차단 감지] 상태 코드 {response.status_code}. 엔진을 세이프 엔드합니다.")
                sys.exit(1)
                
            if response.status_code != 200:
                return []
                
            response_text = response.text
            
            if "recipe_id" not in response.url and "공모전" in response_text and "랭킹" in response_text:
                print(f"\n🚨 [리다이렉트 차단 감지] 메인 페이지 반환 감지.")
                sys.exit(1)
                
            if any(k in response_text for k in ["Access Denied", "보안 대책", "차단되었습니다", "ip block", "Cloudflare", "로봇이 아닙니다"]):
                print(f"\n🚨 [보안 키워드 차단 감지] 프로세스를 종료합니다.")
                sys.exit(1)
                
            soup = BeautifulSoup(response_text, "html.parser")
            
            # 레이어 1. 현대 표준형 순서 구조 파싱
            step_divs = soup.select(".view_step_cont .media-body")
            if not step_divs:
                step_divs = soup.select("div[id^='stepDiv']")
            if not step_divs:
                step_divs = soup.select(".step_cont")

            for div in step_divs:
                text = div.get_text(" ", strip=True)
                if text and len(text) > 2:
                    steps.append(text)
                    
            # 레이어 2. 💡 [전면 교정 레이어] 구형 통짜 에디터형(#oldContArea) 정밀 공백 우회 수집
            if not steps:
                old_cont = soup.select_one("#oldContArea")
                if old_cont:
                    paragraphs = old_cont.find_all(["p", "span", "div", "td"])
                    for p in paragraphs:
                        # 유니코드 공백 노이즈(\xa0)를 일반 공백으로 리플레이스 치환 후 정제
                        txt = p.get_text().replace('\xa0', ' ').strip()
                        
                        # 💡 [핵심 패치]: 문장 맨 처음에 공백문자(^\s*)가 선행하더라도 
                        # 그 뒤에 진짜 숫자가 시작된다면 조리과정 행으로 인정합니다.
                        if txt and re.search(r'^\s*\d+[\.\s\-번\]\)]', txt):
                            refined_txt = txt.strip()
                            if refined_txt not in steps:
                                steps.append(refined_txt)
                                
            # 레이어 3. 공백 응답 차단 유효성 정밀 검증
            if not steps and len(response_text) < 5000:
                print(f"\n🚨 [공백 HTML 차단 감지] 빈 껍데기 세션 차단 상태입니다.")
                sys.exit(1)
                    
            return steps
        except requests.exceptions.RequestException as e:
            print(f" ➔ ❌ 네트워크 지연 에러 (ID: {recipe_id}): {e}")
            return []
        except SystemExit:
            raise
        except Exception as e:
            print(f" ➔ ❌ 예기치 못한 파싱 오류 (ID: {recipe_id}): {e}")
            return []

    def execute_batch_chunk(self, chunk_size: int = 50) -> int:
        # 💡 [전수 재검수 쿼리]: 기존에 오인 격리되어 박혀버린 EMPTY_DATA까지 
        # 풀 안으로 완벽히 재소환하여 정밀 롤링을 시도하도록 Cypher 타겟 범위를 전면 해제합니다.
        find_query = """
        MATCH (r:Recipe)
        WHERE r.origin_url IS NULL OR r.steps IS NULL OR r.hydration_status = 'EMPTY_DATA'
        RETURN elementId(r) as node_id, r.title as title, r.id as recipe_id
        LIMIT $limit
        """
        
        success_query = """
        MATCH (r:Recipe)
        WHERE elementId(r) = $node_id
        SET r.origin_url = $origin_url,
            r.steps = $steps,
            r.hydrated_at = datetime(),
            r.hydration_status = 'SUCCESS'
        """
        
        empty_data_query = """
        MATCH (r:Recipe)
        WHERE elementId(r) = $node_id
        SET r.origin_url = $origin_url,
            r.steps = ['동영상 및 외부 블로그 링크 전용 레시피입니다. 원문 링크를 참조해 주세요.'],
            r.hydrated_at = datetime(),
            r.hydration_status = 'EMPTY_DATA'
        """

        with self.driver.session() as session:
            records = list(session.run(find_query, limit=chunk_size))
            if not records:
                return 0

            for rec in records:
                node_id = rec["node_id"]
                title = rec["title"]
                recipe_id = str(rec["recipe_id"] or "").strip()
                
                if not recipe_id or not recipe_id.isdigit():
                    session.run(empty_data_query, node_id=node_id, origin_url="https://www.10000recipe.com")
                    print(f" ➔ ⚠️ 격리: '{title}' 노드의 id 속성이 비표준 규격입니다.")
                    continue
                
                print(f" ➔ 🔍 스캔 중: '{title}' (ID: {recipe_id})")
                steps = self.scrape_10000recipe_steps(recipe_id)
                
                origin_url = f"https://www.10000recipe.com/recipe/{recipe_id}"
                
                if not steps:
                    session.run(empty_data_query, node_id=node_id, origin_url=origin_url)
                    print(f"   🟡 [링크 보존 격리] 원문 텍스트가 없는 동영상/아웃링크형 노드입니다. (EMPTY_DATA)")
                    time.sleep(1.0)
                    continue
                
                session.run(success_query, node_id=node_id, origin_url=origin_url, steps=steps)
                print(f"   ➔ 🟢 [적재 완수] {len(steps)}개의 조리 순서 및 출처 링크 주입 완료")
                
                time.sleep(1.5)
                
        return len(records)

    def run_total_hydration(self):
        print("============================================================")
        print("🚀 [지식그래프 코어 전체 데이터 전수 마이그레이션 파이프라인 가동]")
        print("============================================================")
        
        chunk_index = 1
        total_attempted = 0
        
        while True:
            print(f"\n📦 [정제 릴레이 - {chunk_index}번째 배치 청크 가동 (크기: 50)]")
            print("-" * 60)
            
            start_time = time.time()
            attempted_count = self.execute_batch_chunk(chunk_size=50)
            
            if attempted_count == 0:
                print("\n============================================================")
                print("🟢 [전수 조사 최종 완수] 지식그래프 내 모든 레시피 노드의 고도화 정제가 완벽히 종료되었습니다!")
                print("============================================================")
                break
                
            total_attempted += attempted_count
            elapsed = round(time.time() - start_time, 2)
            
            print(f"➔ 🎉 {chunk_index}번째 청크 완료: {attempted_count}건 조사 완수 (소요시간: {elapsed}초)")
            print(f"➔ 📊 현재까지 전수 마이그레이션 누적 진행 건수: {total_attempted} 건")
            
            print(" 💤 [세션 보호] 상대 웹서버 방화벽 우회를 위해 5초간 휴식합니다...")
            time.sleep(5.0)
            
            chunk_index += 1

    def close(self):
        if self.driver:
            self.driver.close()

if __name__ == "__main__":
    hydrator = GraphRecipeFullHydrator()
    try:
        hydrator.run_total_hydration()
    finally:
        hydrator.close()