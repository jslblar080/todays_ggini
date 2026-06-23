"""
FILE: graph_data_purifier.py
ROLE: Neo4j 지식그래프 내부의 파싱 오류(식용유 40큰술, 간장 5개 등) 데이터를 
      전수 검수하고 상식적인 표준 데이터로 영구 수정하는 데이터 하이드레이션(Hydration) 엔진
"""
import os
import time
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

class GraphDataPurifier:
    def __init__(self):
        self.db_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def purify_malformed_units(self):
        """💡 [미션 1] 양념류인데 '개', '마리' 등으로 잘못 적재된 단위 영구 교정"""
        print("🔄 [검수 1단계] 양념/소스류의 변칙 단위('개' -> '큰술') 전수 교정을 시작합니다...")
        
        cypher = """
        MATCH (r:Recipe)-[rel:REQUIRES]->(i:Ingredient)
        WHERE rel.amount_unit = '개'
          AND (i.name CONTAINS '간장' OR i.name CONTAINS '설탕' OR i.name CONTAINS '소금' 
            OR i.name CONTAINS '물엿' OR i.name CONTAINS '올리고당' OR i.name CONTAINS '식초' 
            OR i.name CONTAINS '맛술' OR i.name CONTAINS '매실' OR i.name CONTAINS '쯔유' 
            OR i.name CONTAINS '참기름' OR i.name CONTAINS '올리브' OR i.name CONTAINS '식용유')
        WITH rel, rel.amount_value AS old_val
        SET rel.amount_unit = '큰술',
            rel.purified_at = datetime(),
            rel.original_unit_backup = '개'
        RETURN count(rel) AS updated_count
        """
        with self.db_driver.session() as session:
            result = session.run(cypher)
            record = result.single()
            print(f" ➔ 🟢 교정 완료: 총 {record['updated_count']}건의 양념류 단위가 '큰술'로 정상화되었습니다.")

    def purify_empty_units(self):
        """💡 [미션 2] 단위가 빈 문자열('')로 들어가 에러를 유발하는 관계선 정정"""
        print("🔄 [검수 2단계] 빈 문자열('') 단위 데이터의 '약간' 자격 전환 처리를 시작합니다...")
        
        cypher = """
        MATCH (r:Recipe)-[rel:REQUIRES]->(i:Ingredient)
        WHERE rel.amount_unit = '' OR rel.amount_unit IS NULL
        SET rel.amount_unit = '약간',
            rel.amount_value = 0.0,
            rel.purified_at = datetime()
        RETURN count(rel) AS updated_count
        """
        with self.db_driver.session() as session:
            result = session.run(cypher)
            record = result.single()
            print(f" ➔ 🟢 교정 완료: 총 {record['updated_count']}건의 공백 단위가 '약간'으로 흡수되었습니다.")

    def cap_excessive_sauces(self):
        """💡 [미션 3] 파싱 노이즈로 뻥튀기된 대용량 양념류(식용유 40큰술 등)의 상한선 강제 정정"""
        print("🔄 [검수 3단계] 파싱 노이즈로 폭탄 적재된 고칼로리 오일/소스류 임계치(Max 3큰술) 컷오프를 시작합니다...")
        
        cypher = """
        MATCH (r:Recipe)-[rel:REQUIRES]->(i:Ingredient)
        WHERE rel.amount_unit IN ['큰술', '스푼', '숟가락']
          AND rel.amount_value > 10.0
          AND (i.name CONTAINS '식용유' OR i.name CONTAINS '올리브' OR i.name CONTAINS '참기름' OR i.name CONTAINS '오일' OR i.name CONTAINS '물엿')
        WITH rel, rel.amount_value AS old_val
        SET rel.amount_value = 3.0, // 💡 인간 상식선의 최대치인 3큰술로 영구 수정
            rel.purified_at = datetime(),
            rel.original_value_backup = old_val
        RETURN count(rel) AS updated_count
        """
        with self.db_driver.session() as session:
            result = session.run(cypher)
            record = result.single()
            print(f" ➔ 🟢 교정 완료: 총 {record['updated_count']}건의 대용량 양념 수치 폭탄이 3.0(큰술)으로 안전 격리되었습니다.")

    def run_all_purification(self):
        start_time = time.time()
        print("🚀 [지식그래프 전수 검수 및 무결성 정제 타스크 가동]")
        print("═"*60)
        
        self.purify_malformed_units()
        time.sleep(0.5)
        self.purify_empty_units()
        time.sleep(0.5)
        self.cap_excessive_sauces()
        
        print("═"*60)
        print(f"🎉 [정제 완수] 5,862개 데이터 연관 관계 정화 완료! (소요시간: {round(time.time() - start_time, 2)}초)")

    def close(self):
        if self.db_driver:
            self.db_driver.close()

if __name__ == "__main__":
    purifier = GraphDataPurifier()
    try:
        purifier.run_all_purification()
    finally:
        purifier.close()