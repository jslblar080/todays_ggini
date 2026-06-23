"""
FILE: graph_link_hydrator.py
ROLE: [비용 0원 / AI 호출 X] 기존에 적재된 Product 노드 중 
      링크가 누락된 2,045건의 데이터에 원천 딥링크를 매핑하여 실시간 수정하는 엔진
"""
import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

class GraphLinkHydrator:
    def __init__(self):
        self.db_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_file = os.path.abspath(os.path.join(base_dir, "../../data/raw_mankae_recipes.jsonl"))

    def get_missing_link_products(self):
        """💡 DB에서 link 속성이 없는 상품들의 이름(name)을 전량 추출"""
        cypher = """
        MATCH (p:Product)
        WHERE p.link IS NULL
        RETURN p.name AS name
        """
        with self.db_driver.session() as session:
            result = session.run(cypher)
            return {record["name"] for record in result if record["name"]}

    def update_product_link(self, product_name, real_link):
        """💡 특정 상품 노드를 찾아 실제 원천 purchase_link 주소를 실시간 수정/업데이트"""
        cypher = """
        MATCH (p:Product {name: $name})
        SET p.link = $link
        """
        with self.db_driver.session() as session:
            session.run(cypher, name=product_name, link=real_link)

    def run_hydration(self):
        # 1. 수정이 필요한 상품명 목록을 DB에서 가져옴
        missing_products = self.get_missing_link_products()
        if not missing_products:
            print("✨ 이미 모든 상품 노드에 상세 구매 링크가 완벽하게 반영되어 있습니다!")
            return

        print(f"🛠️ [링크 복구 가동] 총 {len(missing_products)}개의 누락된 상품 링크 수정을 시작합니다.")
        
        # 2. 원천 jsonl 파일을 스트리밍하며 매칭되는 링크 탐색 맵 빌드
        link_map = {}
        if not os.path.exists(self.input_file):
            print(f"❌ 원천 파일 경로 오류: {self.input_file}")
            return

        with open(self.input_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # 원천 데이터 내부의 쿠팡 상품 리스트 순회
                    for cp_prod in data.get("coupang_e_commerce", []):
                        title = cp_prod.get("product_title")
                        link = cp_prod.get("purchase_link")
                        if title and link and (title in missing_products):
                            link_map[title] = link
                except:
                    continue

        # 3. 매칭된 링크를 DB에 벌크 연산으로 수정 주입
        updated_count = 0
        for prod_name, real_link in link_map.items():
            self.update_product_link(prod_name, real_link)
            updated_count += 1
            if updated_count % 100 == 0 or updated_count == len(link_map):
                print(f"🟢 [링크 복구 중] 현재까지 {updated_count}개 상품 링크 주입 완료")

        print(f"\n🎉 [마이그레이션 완수] 총 {updated_count}개 상품 노드의 실시간 링크 수정 성공!")

    def close(self):
        if self.db_driver: self.db_driver.close()

if __name__ == "__main__":
    hydrator = GraphLinkHydrator()
    try:
        hydrator.run_hydration()
    finally:
        hydrator.close()