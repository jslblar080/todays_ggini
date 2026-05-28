from app.db.session import engine
from app.db.base_class import Base

# 테이블이 생성되려면 Base가 모델들을 알고 있어야 하므로 모두 임포트해 줍니다.
# (경로는 현재 프로젝트 구조에 맞게 살짝 수정해 주세요)
from app.models.user import User
from app.models.meal import MealPlan
from app.models.shopping import ShoppingList, ShoppingItem

def reset_database():
    print("🧹 기존 테이블을 모두 삭제하는 중...")
    Base.metadata.drop_all(bind=engine)
    
    print("✨ 변경된 모델을 바탕으로 테이블을 새로 생성하는 중...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ 데이터베이스 갱신이 완벽하게 완료되었습니다!")

if __name__ == "__main__":
    reset_database()