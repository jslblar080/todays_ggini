"""
FILE: main.py
ROLE: 전체 레시피 데이터(약 1,300건+)를 배치 단위로 처리하는 통합 실행 엔진.
"""
import os
from dotenv import load_dotenv
from src.scraper.collector import RecipePipeline
from src.db.graph_store import GraphStore

load_dotenv()

def main():
    # 1. 인프라 연결
    db = GraphStore(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "password123")
    )
    pipeline = RecipePipeline()
    
    # 2. 전체 데이터 처리 설정
    # 식약처 API의 실제 데이터 끝 번호는 보통 1300번대입니다. 
    # 안전하게 1500으로 설정하거나, 정확한 수치를 안다면 그 수치를 입력하세요.
    START_INDEX = 1      # API는 1부터 시작하는 경우가 많으므로 1로 설정
    TOTAL_COUNT = 1350    # 전체 데이터 예상 개수
    BATCH_SIZE = 20       # M4 Pro의 성능을 활용해 배치를 20건으로 상향

    print(f"🚀 전체 데이터 파이프라인 가동 (범위: {START_INDEX} ~ {TOTAL_COUNT})")
    print(f"[*] 모드: 배치 처리 (Batch Size: {BATCH_SIZE})")
    print("-" * 50)

    for start in range(START_INDEX, TOTAL_COUNT + 1, BATCH_SIZE):
        end = min(start + BATCH_SIZE - 1, TOTAL_COUNT)
        
        print(f"\n📦 구간 {start} ~ {end} 처리 중...")
        
        try:
            # 수집 및 정제 실행
            refined_recipes = pipeline.run_pipeline(start, end)
            
            if not refined_recipes:
                print(f" [!] 구간 {start}~{end}: 가져올 데이터가 더 이상 없습니다. 종료합니다.")
                break

            # DB 적재
            success_count = 0
            for recipe in refined_recipes:
                try:
                    db.save_recipe(recipe)
                    success_count += 1
                except Exception as e:
                    print(f"  [-] 저장 실패 ({recipe.menu_name}): {e}")
            
            print(f" ✅ 구간 처리 완료: {len(refined_recipes)}건 중 {success_count}건 저장 성공")

        except Exception as e:
            print(f" [Critical Error] 배치 처리 중 예상치 못한 오류 발생: {e}")
            continue # 다음 배치로 진행 시도

    db.close()
    print("\n" + "=" * 50)
    print("🎊 모든 데이터 파이프라인 프로세스가 완료되었습니다.")
    print("=" * 50)

if __name__ == "__main__":
    main()