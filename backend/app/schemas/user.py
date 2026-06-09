from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional, Literal
from app.models.user import MealPurpose

# --- 1. 토큰 관련 스키마 ---
class Token(BaseModel):
    """
    로그인 성공 시 프론트엔드로 전달할 토큰 정보입니다.
    """
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    """
    JWT 토큰의 내부(Payload)를 해석했을 때 담겨있을 데이터 구조입니다.
    보통 'sub' 필드에 유저의 고유 ID를 담습니다.
    """
    sub: Optional[int] = None

# ------- 토큰 재발급 전용 스키마 -------------
class TokenRefreshRequest(BaseModel):
    refreshToken: str

class TokenRefreshResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"

# --- 2. 유저 정보 기본 스키마 ---
class UserBase(BaseModel):
    provider: str
    social_id: str
    email: Optional[EmailStr] = None

# ----------- 가구원 정보 스키마 ----------------
class FamilyMemberInfo(BaseModel):
    nickname: Optional[str] = Field("가구원1", description="가구원 식별용 별칭")
    gender: Literal["남", "여"] = Field(..., description="성별 ('남' 또는 '여')")
    age: int = Field(..., ge=0, le=120, description="만 나이")
    height: float = Field(..., ge=30.0, le=250.0, description="키 (cm)")
    weight: float = Field(..., ge=2.0, le=300.0, description="몸무게 (kg)")

    model_config = ConfigDict(from_attributes=True)

# --------------- 페르소나 설정 스키마 ---------------------
class UserPersonaSettingInfo(BaseModel):
    household_type: str = Field("1인 가구", description="가구 형태 ('1인 가구' 또는 '다인 가구')")
    monthly_budget: int = Field(300000, ge=0, description="한 달 목표 식비")
    meals_per_day: int = Field(3, ge=1, le=5, description="하루 식사 수")
    purpose: List[str] = Field(default_factory=list, description="이용 목적 리스트")
    persona_id: Optional[int] = Field(None, description="최종 선택한 페르소나 ID")

    model_config = ConfigDict(from_attributes=True)

# -------------- 온보딩 설정 스키마 -------------------
class UserOnboardingSettingInfo(BaseModel):
    """온보딩 세부 취향 도메인 정보"""
    preferred_categories: List[str] = Field(default_factory=list, description="선호하는 식단 카테고리 (한식, 일식 등)")
    preferred_ingredients: Optional[List[str]] = Field(default_factory=list, description="선택한 선호 재료군")
    excluded_ingredients: Optional[List[str]] = Field(default_factory=list, description="기호/알러지 제외 식재료")
    cooking_skill: int = Field(3, ge=1, le=5, description="요리 실력 (1~5)")
    diversity_level: str = Field("보통", description="식단 다양성 선호도 ('낮음', '보통', '높음')")
    selected_style_id: Optional[str] = Field(None, description="최종 선택 식단 스타일 ID")

    model_config = ConfigDict(from_attributes=True)

# --------------- 유저 정보 조회 스키마 -------------------
class UserInfo(BaseModel):
    id: int
    provider: str
    social_id: str
    email: Optional[EmailStr] = None
    nickname: str
    image_url: Optional[str] = None
    is_guest: bool
    is_onboarded: bool
    markets: List[str] = Field(default_factory=lambda: ["쿠팡", "컬리", "네이버"])

    # 🔗 DB의 relationship 매핑 규칙 이름과 정확히 싱크를 맞춥니다.
    family_members: List[FamilyMemberInfo] = Field(default_factory=list, description="가구원 스펙 리스트")
    persona_setting: Optional[UserPersonaSettingInfo] = Field(None, description="페르소나 추천/설정 데이터")
    onboarding_setting: Optional[UserOnboardingSettingInfo] = Field(None, description="온보딩 세부 데이터")

    model_config = ConfigDict(from_attributes=True)

# ------------------- 페르소나 정보 업데이트 스키마 -------------------
class UserPersonaSettingUpdate(BaseModel):
    """[페르소나 재설정] 화면에서 넘어오는 요청 스펙"""
    household_type: str = Field(None, description="가구 형태 ('1인 가구' 또는 '다인 가구')")
    monthly_budget: int = Field(None, ge=0, description="한 달 목표 식비")
    meals_per_day: int = Field(None, ge=1, le=5, description="하루 식사 수")
    purpose: List[MealPurpose] = Field(None, description="이용 목적 리스트")
    persona_id: Optional[int] = Field(None, description="최종 선택/변경한 페르소나 ID")
    
    # 💡 다인 가구 스펙 변경 시 동적으로 들어올 가구원 리스트
    family_members: List[FamilyMemberInfo] = Field(None, description="가구원 신체 스펙 리스트")

    model_config = ConfigDict(from_attributes=True)

# -------------------- 온보딩 업데이트 스키마 ----------------------------
class UserOnboardingSettingUpdate(BaseModel):
    """[온보딩 취향 재설정] 화면에서 넘어오는 요청 스펙"""
    preferred_categories: List[str] = Field(None, description="선호하는 식단 카테고리")
    preferred_ingredients: Optional[List[str]] = Field(None, description="선택한 선호 재료군")
    excluded_ingredients: Optional[List[str]] = Field(None, description="기호/알러지 제외 식재료")
    cooking_skill: Optional[int] = Field(None, ge=1, le=5, description="요리 실력 (1~5)")
    diversity_level: Optional[str] = Field(None, description="식단 다양성 선호도 ('낮음', '보통', '높음')")
    selected_style_id: Optional[str] = Field(None, description="최종 선택 식단 스타일 ID")

    model_config = ConfigDict(from_attributes=True)

# ------ API 응답 시 유저 정보를 돌려주는 스키마 --------
class UserResponse(BaseModel):
    id: int
    is_onboarded: bool

    model_config = ConfigDict(from_attributes=True)

# ------- 로그인 전용 스키마 --------
class SocialLoginRequest(BaseModel):
    accessToken: str

class UserInformation(BaseModel):
    id: int
    nickname: Optional[str] = None
    email: str
    is_onboarded: bool

class SocialLoginResponse(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserInformation

# ------ 닉네임 변경 전용 스키마 --------
class NicknameUpdateRequest(BaseModel):
    nickname: str