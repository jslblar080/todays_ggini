from sqlalchemy import Column, Integer, String, JSON, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from app.db.base_class import Base

class SocialProvider(str, enum.Enum):
    KAKAO = "kakao"
    NAVER = "naver"
    GOOGLE = "google"
    GUEST = "guest"

# 식단 목적 열거형 정의
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
    social_id = Column(String, unique=True, index=True, nullable=True) # 소셜 앱의 고유 ID
    provider = Column(Enum(SocialProvider), nullable=False) # "kakao", "google", "naver"
    nickname = Column(String, nullable=True, default="자취생")

    # 데이터베이스 상에서 해당 유저의 계정이 현재 활성화 상태인지 아니면 비활성화(휴면) 상태인지를 구분
    is_active = Column(Boolean, default=True)

    # 게스트 여부
    is_guest = Column(Boolean, default=False)
    
    # 온보딩 상태 체크 (이 값이 False면 페르소나 설정 화면으로 강제 이동)
    is_onboarded = Column(Boolean, default=False)

    # [목적 설정] AI 가중치 계산의 핵심
    purpose = Column(JSON, default=list)

    # [생활 조건 설정]
    monthly_budget = Column(Integer, default=300000)  # 월 예산
    meals_per_day = Column(Integer, default=3)        # 하루 식사 수
    cooking_skill = Column(Integer, default=3)        # 요리 실력 (1~5단계)

    # [취향 설정]
    preferred_style = Column(JSON, default=list) # 한식, 중식 등
    diversity_level = Column(String, default="낮음") # 다양성 (1:낮음, 2:보통, 3:높음)

    # 재료 관련 설정
    # 선호 재료군: ["식물성 단백질류", "채소류"]
    preferred_ingredients = Column(JSON, default=list, nullable=True)

    # [알레르기 / 제외 재료]
    # 리스트 형태의 데이터를 저장하기 위해 JSON 타입을 사용하거나 별도 테이블 운영
    excluded_ingredients = Column(JSON, default=list, nullable=True)  # ["견과류", "우유"] 등
    
    # 페르소나 (화면 1 관련)
    persona_id = Column(Integer, nullable=True) # nullable=True : 비어있을 수 있음

    # 관계 설정 (유저가 생성한 식단들과 연결)
    # 유저가 삭제되면 관련 식단도 삭제되도록 cascade 설정
    meal_plans = relationship("MealPlan", back_populates="owner", cascade="all, delete-orphan")

    shopping_list = relationship("ShoppingList", back_populates="owner", uselist=False, cascade="all, delete-orphan")