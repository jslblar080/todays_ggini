from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
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

# --------------------------- 최초 user 테이블 -----------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False) # username 대신 email 권장
    social_id = Column(String, unique=True, index=True, nullable=True) # 소셜 앱의 고유 ID
    provider = Column(Enum(SocialProvider), nullable=False) # "kakao", "google", "naver"
    nickname = Column(String, nullable=True, default="자취생")
    image_url = Column(String, nullable=True)

    # 데이터베이스 상에서 해당 유저의 계정이 현재 활성화 상태인지 아니면 비활성화(휴면) 상태인지를 구분
    is_active = Column(Boolean, default=True)
    # 게스트 여부
    is_guest = Column(Boolean, default=False)
    # 온보딩 상태 체크 (이 값이 False면 페르소나 설정 화면으로 강제 이동)
    is_onboarded = Column(Boolean, default=False)

    # 마켓 정보
    markets = Column(JSONB, default=["쿠팡", "컬리", "네이버"], nullable=False)

    # 관계 설정 (유저가 생성한 식단들과 연결)
    # 유저가 삭제되면 관련 식단도 삭제되도록 cascade 설정
    meal_plans = relationship("MealPlan", back_populates="owner", cascade="all, delete-orphan")

    shopping_list = relationship("ShoppingList", back_populates="owner", uselist=False, cascade="all, delete-orphan")

    # 1:N 관계: 가구원 스펙 리스트
    family_members = relationship("UserFamilyMember", back_populates="user", cascade="all, delete-orphan")

    # 1:1 관계: 페르소나 추천 및 선택 설정
    persona_setting = relationship("UserPersonaSetting", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # 1:1 관계: 온보딩 세부 취향 설정
    onboarding_setting = relationship("UserOnboardingSetting", back_populates="user", uselist=False, cascade="all, delete-orphan")

    meal_feedbacks = relationship("MealFeedback", back_populates="user", cascade="all, delete-orphan")

# ---------------------------- 가구원 정보 테이블 ---------------------------------
class UserFamilyMember(Base):
    __tablename__ = "user_family_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # "본인", "엄마", "자녀1" 등을 구분하기 위한 필드
    nickname = Column(String, nullable=True, default="가구원1") 
    
    # 신체 스펙 파라미터 (추후 모델링 파트에서 칼로리/영양소 계산 시 원천 데이터로 사용)
    gender = Column(String, nullable=False)  # "남자" or "여자"
    age = Column(Integer, nullable=False)
    height = Column(Float, nullable=False)   # cm 단위
    weight = Column(Float, nullable=False)   # kg 단위

    # 관계 설정
    user = relationship("User", back_populates="family_members")

# ----------------------- 페르소나 정보 테이블 --------------------------------
class UserPersonaSetting(Base):
    __tablename__ = "user_persona_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # 모델링 파트 추천 요청 및 페르소나 결정을 위한 핵심 데이터
    household_type = Column(String, default="1인 가구", nullable=False)   # 가구 유형
    family_count = Column(Integer, default=1, nullable=False)   # 가구원 수
    monthly_budget = Column(Integer, default=300000)            # 한 달 예산
    meals_per_day = Column(Integer, default=3)                  # 하루 식사 수
    purpose = Column(JSONB, default=list)               # 요리 목적 (식비 절약 등)
    activity_level = Column(Integer, nullable=False, default=2)   # 활동량

    # 모델링 파트의 응답을 토대로 유저가 최종 고른 페르소나 ID 결과물
    persona_name = Column(String, nullable=True)

    # 페르소나 고유 ID 식별자 컬럼
    persona_id = Column(String, nullable=True)

    # 페르소나 추천 요청을 통해 계산된 권장 칼로리
    recommended_daily_calories = Column(Integer, nullable=True, default=1800)

    user = relationship("User", back_populates="persona_setting")

# ------------------------- 온보딩 정보 테이블 ---------------------------
class UserOnboardingSetting(Base):
    __tablename__ = "user_onboarding_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # 페르소나 설정 이후 단계에서 수집하는 유저 개인의 취향/필터 데이터
    preferred_categories = Column(JSONB, default=list)   # 선호 카테고리 (한식, 일식 등)
    preferred_ingredients = Column(JSONB, default=list, nullable=True)  # 선호 식재료
    excluded_ingredients = Column(JSONB, default=list, nullable=True)   # 제외 식재료 / 알레르기
    cooking_skill = Column(Integer, default=3)            # 요리 실력 (1~5)
    diversity_level = Column(String, default="보통")      # 다양성 선호도
    selected_style_id = Column(String, nullable=True)     # 최종 선택 식단 스타일

    user = relationship("User", back_populates="onboarding_setting")