from sqlalchemy import Column, Date, Integer, ForeignKey, DateTime, UniqueConstraint, Text, String
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
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
    content = Column(JSONB, nullable=False)

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
    
class MealFeedback(Base):
    """
    유저가 일별 식단(아침/점심/저녁)에 대해 남긴 별점 평가 및 상세 피드백 데이터를 저장하는 테이블입니다.
    """
    __tablename__ = "meal_feedbacks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 유저 테이블과의 연관 관계 외래키 (유저가 탈퇴하면 피드백도 연쇄 삭제되도록 CASCADE 탑재)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 피드백 대상 날짜 및 식단 번호 (1: 아침/식단1, 2: 점심/식단2, 3: 저녁/식단3)
    date = Column(Date, nullable=False, index=True)
    meal_number = Column(Integer, nullable=False)
    meal_name = Column(String, nullable=False)
    
    # 별점 수치 (1점 ~ 5점)
    rating = Column(Integer, nullable=False)
    
    # 선택된 체크박스 텍스트 리스트를 JSONB 형태로 통째로 저장합니다
    is_checked = Column(JSONB, nullable=False, server_default='[]', comment="체크된 피드백 항목 리스트")
    
    # 데이터 생성 및 최종 수정 시간 관리
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # SQLAlchemy ORM 역참조 관계 설정 (User 모델에 feedbacks 관리가 필요할 경우 활용)
    user = relationship("User", back_populates="meal_feedbacks")

    # [데이터 정합성 핵심 장치] 
    # 한 명의 유저가 '특정 날짜'의 '특정 식단'에 중복으로 피드백 레코드를 생성하는 것을 완전히 차단합니다.
    # 이 제약 조건 덕분에 백엔드 라우터에서 안전하게 ON CONFLICT (Upsert) 로직을 구사할 수 있습니다.
    __table_args__ = (
        UniqueConstraint('user_id', 'date', 'meal_number', name='uq_user_date_meal_number'),
    )