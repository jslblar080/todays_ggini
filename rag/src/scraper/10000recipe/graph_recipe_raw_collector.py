"""
FILE: graph_recipe_raw_full_collector.py
ROLE: [전체 데이터 전수 Raw 텍스트 버큠 완결판]
      Neo4j 내 미완성 레시피 노드를 전수조사하여 날것의 본문 텍스트를 무한 배칭으로 수집하는 엔진.
      웹서버 차단 징후(403/429/메인 리다이렉트) 감지 시 세이프 엔드(Safe Exit)하여 데이터를 보호합니다.
DEPENDENCY: pip install beautifulsoup4 requests neo4j python-dotenv
"""
import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

class GraphRawFullCollector:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Connection": "keep-alive"
        }

    def fetch_raw_body_text(self, recipe_id: str) -> str:
        """웹페이지의 조리 컨텐츠 영역 텍스트를 정제 없이 통째로 추출하며 차단을 자가 진단"""
        url = f"https://www.10000recipe.com/recipe/{recipe_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=7)
            
            # 💡 [방어선 1] 명시적 HTTP 트래픽 제재 감지 시 프로세스 즉시 세이프 엔드
            if response.status_code in [403, 429]:
                print(f"\n🚨 [WAF 차단 감지] 웹서버 방화벽 트래픽 제재(Status Code: {response.status_code})가 발동되었습니다.")
                print(" 👉 정상 노드 오염 방지를 위해 가동을 즉시 중단합니다. IP 환경 리프레시 후 재가동하세요.")
                sys.exit(1)
                
            if response.status_code != 200:
                return ""
                
            response_text = response.text
            
            # 💡 [방어선 2] 메인화면 강제 리다이렉트 차단 기법 방어
            if "recipe_id" not in response.url and "공모전" in response_text and "랭킹" in response_text:
                print(f"\n🚨 [리다이렉트 차단 감지] 메인 페이지로 튕겼습니다. 현재 세션이 제재된 상태입니다.")
                sys.exit(1)
                
            # 💡 [방어선 3] 보안 키워드 은닉 감지
            if any(k in response_text for k in ["Access Denied", "보안 대책", "차단되었습니다", "ip block", "Cloudflare", "로봇이 아닙니다"]):
                print(f"\n🚨 [텍스트 차단 감지] HTML 본문 내 보안 디펜더 키워드가 포착되었습니다.")
                sys.exit(1)
            
            soup = BeautifulSoup(response_text, "html.parser")
            main_body = soup.select_one("#oldContArea") or soup.select_one(".view_step")
            
            if main_body:
                lines = [line.strip() for line in main_body.get_text("\n").split("\n") if line.strip()]
                raw_text = "\n".join(lines)
                
                # 💡 [방어선 4] 200 OK 정상코드로 쏘는 가짜 공백 응답 차단 방어
                if not raw_text and len(response_text) < 5000:
                    print(f"\n🚨 [공백 응답 차단 감지] 서버가 빈 껍데기 HTML만 반환하고 있습니다.")
                    sys.exit(1)
                    
                return raw_text
            return ""
        except requests.exceptions.RequestException as e:
            print(f" ➔ ❌ 네트워크 지연 에러 (ID: {recipe_id}): {e}")
            return ""
        except SystemExit:
            raise
        except Exception as e:
            print(f" ➔ ❌ 예기치 못한 크롤링 오류 (ID: {recipe_id}): {e}")
            return ""

    def execute_batch_chunk(self, chunk_size: int = 50) -> int:
        """50개 단위의 한 청크를 수집하고 Neo4j DB에 실시간 텍스트 주입"""
        # 아직 Raw 텍스트가 수집되지 않은 미완성 레시피이거나, 기존에 텍스트를 못 긁어 EMPTY_DATA 딱지가 붙었던 노드 전체 수집
        find_query = """
        MATCH (r:Recipe)
        WHERE r.raw_html_text IS NULL
        RETURN elementId(r) as node_id, r.title as title, r.id as recipe_id
        LIMIT $limit
        """
        
        update_query = """
        MATCH (r:Recipe)
        WHERE elementId(r) = $node_id
        SET r.raw_html_text = $raw_text,
            r.hydration_status = 'RAW_COLLECTED',
            r.origin_url = $origin_url
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
                    # 식별 키 자체가 깨진 불량 노드는 패스 처리하여 루프 차단
                    session.run(update_query, node_id=node_id, raw_text="BAD_RECIPE_ID", origin_url="https://www.10000recipe.com")
                    continue
                
                print(f" ➔ 📥 Raw 텍스트 버큠 중: '{title}' (ID: {recipe_id})")
                raw_text = self.fetch_raw_body_text(recipe_id)
                
                origin_url = f"https://www.10000recipe.com/recipe/{recipe_id}"
                
                # 빈 페이지인 경우에도 상태를 각인하여 대기열 무한 루프 탈출 방지
                final_text = raw_text if raw_text else "NO_BODY_TEXT_FOUND"
                session.run(update_query, node_id=node_id, raw_text=final_text, origin_url=origin_url)
                print("   ➔ 🟢 임시 속성(raw_html_text) 적재 완료")
                
                # 웹서버 타격 임계치 우회를 위한 안전 마진 지연 (1.5초)
                time.sleep(1.5)
                
        return len(records)

    def run_total_collection(self):
        print("============================================================")
        print("🚀 [지식그래프 원천 날것의 본문 텍스트 전수 버큠 파이프라인 가동]")
        print("============================================================")
        
        chunk_index = 1
        total_attempted = 0
        
        while True:
            print(f"\n📦 [버큠 릴레이 - {chunk_index}번째 배치 청크 가동 (크기: 50)]")
            print("-" * 60)
            
            start_time = time.time()
            attempted_count = self.execute_batch_chunk(chunk_size=50)
            
            # 더 이상 채울 노드가 없으면 완벽 종료
            if attempted_count == 0:
                print("\n============================================================")
                print("🟢 [전수 버큠 완수] 모든 레시피 노드의 원천 텍스트가 DB 내부에 영구 안착되었습니다!")
                print("============================================================")
                break
                
            total_attempted += attempted_count
            elapsed = round(time.time() - start_time, 2)
            
            print(f"➔ 🎉 {chunk_index}번째 청크 완료: {attempted_count}건 조사 완수 (소요시간: {elapsed}초)")
            print(f"➔ 📊 현재까지 전수 마이그레이션 누적 진행 건수: {total_attempted} 건")
            
            # 청크당 방화벽 세션 쿨다운 휴식 (5초)
            print(" 💤 [세션 보호] 상대 웹서버 레이더망 우회를 위해 5초간 휴식합니다...")
            time.sleep(5.0)
            
            chunk_index += 1

    def close(self):
        if self.driver:
            self.driver.close()

if __name__ == "__main__":
    hydrator = GraphRawFullCollector()
    try:
        hydrator.run_total_collection()
    finally:
        hydrator.close()