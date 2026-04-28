from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.db.base_class import Base

# 1. 식단 목적 열거형 정의
class MealPurpose(str, enum.Enum):
    SAVE = "식비 절약"
    BALANCE = "영양 균형"
    DIET = "다이어트"
    PROTEIN = "고단백"
    EASY = "간편식"
    TASTE = "맛 중심"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False) # username 대신 email 권장
    hashed_password = Column(String, nullable=True) # 소셜 로그인은 비번이 없음
    social_id = Column(String, unique=True, nullable=True) # 소셜 앱의 고유 ID
    provider = Column(String, nullable=True) # "kakao", "google", "naver" 등

    # [목적 설정] AI 가중치 계산의 핵심
    purpose = Column(Enum(MealPurpose), default=MealPurpose.BALANCE)

    # [생활 조건 설정]
    monthly_budget = Column(Integer, default=300000)  # 월 예산
    meals_per_day = Column(Integer, default=3)        # 하루 식사 수
    cooking_skill = Column(Integer, default=3)        # 요리 실력 (1~5단계)

    # [취향 설정]
    preferred_style = Column(String, default="상관없음") # 한식, 중식 등
    variety_level = Column(Integer, default=2)          # 다양성 (1:낮음, 2:보통, 3:높음)
    
    # [알레르기 / 제외 재료]
    # 리스트 형태의 데이터를 저장하기 위해 JSON 타입을 사용하거나 별도 테이블 운영
    excluded_ingredients = Column(JSON, nullable=True)  # ["견과류", "우유"] 등

    # 관계 설정 (유저가 생성한 식단들과 연결)
    # meal_plans = relationship("MealPlan", back_populates="owner")
    
    # 페르소나 (화면 1 관련)
    persona_id = Column(Integer, nullable=True) # nullable=True : 비어있을 수 있음