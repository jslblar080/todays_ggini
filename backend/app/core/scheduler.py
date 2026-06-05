from datetime import datetime, timedelta
from sqlalchemy import delete
from app.db.session import SessionLocal
from app.models.meal import MealPlan
from app.models.shopping import ShoppingList, ShoppingItem

# 휴지통(soft delete) 항목 보관 기간 — 이 기간이 지난 삭제 항목은 영구 삭제(hard delete).
TRASH_RETENTION_DAYS = 30

def purge_expired_data():
    """
    [배치 작업] 만료된 과거 식단과 장바구니 데이터를 DB에서 일괄 삭제합니다.
    """
    db = SessionLocal()
    try:
        current_time = datetime.utcnow()

        # 1. 과거 식단 계획: 32일이 지난 데이터 삭제
        meal_plan_cutoff = current_time - timedelta(days=32)
        # 💡 (참고) DB 모델에서 meal_details에 ON DELETE CASCADE가 설정되어 있다면, 부모만 지워도 자식은 함께 날아갑니다.
        db.execute(delete(MealPlan).where(MealPlan.created_at < meal_plan_cutoff))

        # 2. 장바구니 및 쇼핑 아이템: 62일이 지난 데이터 삭제
        shopping_cutoff = current_time - timedelta(days=62)
        db.execute(delete(ShoppingList).where(ShoppingList.created_at < shopping_cutoff))

        # 3. 휴지통 항목: soft delete 후 TRASH_RETENTION_DAYS(30일) 경과 시 영구 삭제
        trash_cutoff = current_time - timedelta(days=TRASH_RETENTION_DAYS)
        db.execute(
            delete(ShoppingItem).where(
                ShoppingItem.deleted_at.isnot(None),
                ShoppingItem.deleted_at < trash_cutoff,
            )
        )

        # 변경사항 확정
        db.commit()
        print(
            f"[Batch] {current_time} - 오래된 식단(32일)·장바구니(62일) 및 "
            f"휴지통({TRASH_RETENTION_DAYS}일) 데이터 정리 완료"
        )
        
    except Exception as e:
        db.rollback()
        print(f"[Batch Error] 데이터 일괄 삭제 실패: {e}")
    finally:
        db.close()