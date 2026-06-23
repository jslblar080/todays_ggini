"""
FILE: retry_failed.py
ROLE: 이전에 실패했던 특정 레시피들만 골라서 다시 수집 및 정제 수행.
"""
import os
from dotenv import load_dotenv
from src.scraper.collector import RecipePipeline
from src.db.graph_store import GraphStore

load_dotenv()

def main():
    db = GraphStore(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "password123")
    )
    pipeline = RecipePipeline()
    
    # [중요] 이전 로그에서 확인된 실패한 레시피 번호들을 여기에 입력하세요.
    # 예: 121~140 구간 중 하나, 181~200 구간 중 하나 등
    FAILED_INDICES = [121, 181, 261, 341, 441, 721, 881, 981, 1121] 

    print(f"🔄 실패했던 {len(FAILED_INDICES)}건의 데이터 재수집을 시작합니다.")
    print("-" * 50)

    for idx in FAILED_INDICES:
        print(f"[*] 인덱스 {idx} 처리 시도 중...")
        
        # 건별로 처리하기 위해 start와 end를 동일하게 idx로 설정
        refined_recipes = pipeline.run_pipeline(idx, idx)
        
        if refined_recipes:
            recipe = refined_recipes[0]
            try:
                db.save_recipe(recipe)
                print(f" ✅ 재수집 성공 및 저장 완료: {recipe.menu_name}")
            except Exception as e:
                print(f" ❌ DB 저장 실패 ({recipe.menu_name}): {e}")
        else:
            print(f" ❌ 인덱스 {idx}: 정제 단계에서 다시 실패했습니다.")

    db.close()
    print("\n[재시도 프로세스 종료]")

if __name__ == "__main__":
    main()