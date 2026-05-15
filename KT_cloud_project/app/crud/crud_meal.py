from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from sqlalchemy.dialects.sqlite import insert
from datetime import date, timedelta
from app.models.meal import MealPlan

def save_monthly_plan(db: Session, user_id: int, ai_days_list: list) -> bool:
    """
    AI가 생성한 30일치 월간 식단을 MealPlan 테이블에 날짜별로 저장합니다.
    (기존 데이터가 있을 경우 SQLite Upsert 구문으로 덮어씁니다.)
    """
    try:
        start_date = date.today()
        
        # ai_monthly_data["days"] 리스트 순회
        for day_data in ai_days_list:
            # AI가 준 day(1, 2, 3...)를 실제 날짜로 변환 (예: 1일차 = 오늘)
            target_date = start_date + timedelta(days=day_data.get("day", 1) - 1)
            
            daily_meals = day_data.get("meals", [])
            
            # 1. 해당 날짜 식단의 요약 정보 계산
            day_total_cost = 0
            day_total_kcal = 0
            
            # AI 명세서의 selected_menu 구조에서 비용과 칼로리 추출
            for meal in daily_meals:
                menu = meal.get("selected_menu", {})
                day_total_cost += menu.get("estimated_cost", 0)
                day_total_kcal += menu.get("calories", 0)

            # 2. Upsert 로직 실행 (SQLite 전용)
            # content 필드에 그 날 먹을 모든 식사(meals) 리스트를 JSON 형태로 통째로 저장합니다.
            stmt = insert(MealPlan).values(
                user_id=user_id,
                meal_date=target_date,             # 모델에 meal_date 컬럼이 있다고 가정
                content=daily_meals,               # JSON 컬럼
                estimated_cost=day_total_cost,
                total_calories=day_total_kcal,
                created_at=func.now(),
                updated_at=func.now()
            )

            # 중복 키(user_id, meal_date) 충돌 시 업데이트 설정
            stmt = stmt.on_conflict_do_update(
                index_elements=['user_id', 'meal_date'], # 이 두 개가 UniqueConstraint로 묶여 있어야 합니다.
                set_={
                    "content": stmt.excluded.content,
                    "estimated_cost": stmt.excluded.estimated_cost,
                    "total_calories": stmt.excluded.total_calories,
                    "updated_at": func.now()
                }
            )
            
            db.execute(stmt)

        # 30일치 반복문이 다 돌고 나면 한 번에 커밋
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"DB 저장 에러 발생: {e}") # 디버깅용 로그
        raise e
    
def get_monthly_plans(db: Session, user_id: int, year: int, month: int):
    """
    캘린더 화면(사진 9) 조회를 위해 특정 월의 식단 리스트를 가져옵니다.
    """
    return db.query(MealPlan).filter(
        MealPlan.user_id == user_id,
        extract('year', MealPlan.meal_date) == year,
        extract('month', MealPlan.meal_date) == month
    ).order_by(MealPlan.meal_date.asc()).all()

def get_meal_plan_by_id(db: Session, meal_plan_id: int, user_id: int):
    """
    식단 ID 기반 상세 조회 (상세 페이지용).
    """
    return db.query(MealPlan).filter(
        MealPlan.id == meal_plan_id,
        MealPlan.user_id == user_id
    ).first()