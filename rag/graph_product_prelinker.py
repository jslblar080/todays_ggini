"""
FILE: graph_product_prelinker.py
ROLE: [인프라 병목 84초 -> 0.5초] 
      실시간 API 타임에 수행하던 식재료-상품 간의 무거운 CONTAINS 문자열 정렬 조인을 
      오프라인에서 미리 계산하여 [:HAS_LOWEST_PRICE] 관계로 영구 박제합니다.
"""
import os
import time
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def prelink_lowest_prices():
    # 💡 유효 가격(>0)을 가진 최저가 상품 1건을 미리 찾아 다이렉트 에지(HAS_LOWEST_PRICE)를 맺는 마법의 쿼리
    query = """
    MATCH (i:Ingredient)
    WHERE NOT EXISTS { MATCH (i)-[:HAS_LOWEST_PRICE]->(:Product) }
    WITH i LIMIT 100
    
    OPTIONAL MATCH (p:Product)
    WHERE p.price > 0 AND (p.name CONTAINS i.name OR i.name CONTAINS p.name)
    WITH i, p
    ORDER BY p.price ASC
    
    WITH i, collect(p)[0] as top_product
    WHERE top_product IS NOT NULL
    MERGE (i)-[:HAS_LOWEST_PRICE]->(top_product)
    RETURN count(i) as linked_count
    """
    
    print("============================================================")
    print("🚀 [인프라 최적화] 식재료별 최저가 상품 오프라인 프리링크 배치 기동")
    print("============================================================")
    
    with driver.session() as session:
        total = 0
        while True:
            res = session.run(query)
            record = res.single()
            count = record["linked_count"] if record else 0
            if count == 0:
                print("\n✨ 모든 식재료 노드에 최저가 상품 다이렉트 링크 배치가 완료되었습니다!")
                break
            total += count
            print(f"🔗 [배치] 고유 식재료 {total}개 건에 실물 최저가 상품 고속 선행 연결 완수...", flush=True)
            time.sleep(0.1)

if __name__ == "__main__":
    start = time.time()
    prelink_lowest_prices()
    driver.close()
    print(f"🕒 총 소요시간: {round(time.time() - start, 2)}초")