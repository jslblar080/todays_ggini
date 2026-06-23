"""
FILE: check_variants.py
ROLE: Neo4j에 저장된 재료 노드들 중 중복/변종 가능성이 높은 항목들을 리포트로 출력.
"""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def get_variants():
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"), 
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )
    
    # 앞 글자 2개가 같은 재료들을 모으는 쿼리
    query = """
    MATCH (i:Ingredient)
    WITH left(i.name, 2) AS prefix, i.name AS full_name
    WITH prefix, collect(full_name) AS names, count(*) AS cnt
    WHERE cnt > 1
    RETURN prefix, names, cnt
    ORDER BY cnt DESC
    """
    
    with driver.session() as session:
        result = session.run(query)
        print(f"{'키워드':<10} | {'변종 개수':<10} | {'변종 리스트'}")
        print("-" * 80)
        
        for record in result:
            print(f"{record['prefix']:<10} | {record['cnt']:<10} | {', '.join(record['names'])}")
            
    driver.close()

if __name__ == "__main__":
    get_variants()