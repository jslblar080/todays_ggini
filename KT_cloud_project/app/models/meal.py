from sqlalchemy import Column, Date, Integer, ForeignKey, JSON, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 실제 식단이 예정된 날짜 (예: 2026-04-30)
    # 인덱스를 걸어 날짜별 조회 성능을 최적화합니다.
    meal_date = Column(Date, index=True, nullable=False)
    
    # 아침/점심/저녁 상세 메뉴, 레시피, 재료 정보 등을 담는 JSON 필드
    # schemas/meal.py의 DailyMealPlan 구조가 여기에 저장됩니다.
    content = Column(JSON, nullable=False)

    # 캘린더 요약 및 통계(화면 7, 9번)를 위한 별도 컬럼
    # JSON을 매번 파싱하지 않고도 합계 데이터를 빠르게 조회할 수 있습니다.
    estimated_cost = Column(Integer, default=0, comment="해당 날짜 총 예상 비용")
    total_calories = Column(Integer, default=0, comment="해당 날짜 총 칼로리")

    # 데이터 관리용 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # User 모델과의 관계 설정
    owner = relationship("User", back_populates="meal_plans")

    # 유저당 날짜별 데이터 중복 방지 제약 조건
    __table_args__ = (
        UniqueConstraint('user_id', 'meal_date', name='_user_meal_date_uc'),
    )

    def __repr__(self):
        return f"<MealPlan(user_id={self.user_id}, date={self.meal_date})>"