from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional

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

# --- 2. 유저 정보 기본 스키마 ---
class UserBase(BaseModel):
    provider: str
    social_id: str
    email: Optional[EmailStr] = None

class UserInfo(BaseModel):
    id: int
    provider: str
    social_id: str
    email: Optional[EmailStr] = None
    nickname : str
    image_url : Optional[str] = None
    is_guest: bool
    is_onboarded: bool

    persona_id: Optional[int] = Field(None, ge=1, le=6, description="선택한 페르소나 ID")
    meals_per_day: Optional[int] = Field(None, ge=1, le=5, description="하루 식사 수")
    purpose: List[str] = Field(default_factory=list, description="이용 목적 (최대 3개)")
    monthly_budget: Optional[int] = Field(None, ge=0, description="한 달 목표 식비")
    cooking_skill: Optional[int] = Field(None, ge=1, le=5, description="요리 실력 (1~5)")
    preferred_ingredients: List[str] = Field(default_factory=list, description="선택한 선호 재료군")
    preferred_categories: List[str] = Field(default_factory=list, description="선호하는 식단 카테고리")
    diversity_level: Optional[str] = Field(None, description="식단 다양성 정도")
    excluded_ingredients: Optional[List[str]] = Field(None, description="기호/알러지 제외 식재료")

    selected_style_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# ---------- 온보딩 전용 스키마 -------------
class UserOnboardingUpdate(BaseModel):
    """
    로그인 후 진행하는 '개인화 설정(온보딩)' 전용 스키마.
    사용자가 입력한 값만 선택적으로 업데이트(PATCH)할 수 있도록 
    모든 필드를 Optional로 설정합니다.
    """
    persona_id: Optional[int] = Field(None, ge=1, le=6, description="선택한 페르소나 ID")
    meals_per_day: Optional[int] = Field(None, ge=1, le=5, description="하루 식사 수")
    purpose: Optional[List[str]] = Field(None, max_items=3, description="이용 목적 (최대 3개)")
    monthly_budget: Optional[int] = Field(None, ge=0, description="한 달 목표 식비")
    cooking_skill: Optional[int] = Field(None, ge=1, le=5, description="요리 실력 (1~5)")
    diversity_level: Optional[str] = Field(None, description="낮음, 보통, 높음")
    preferred_categories: Optional[List[str]] = Field(None, description="선호하는 식단 카테고리 (한식, 일식 등)")
    preferred_ingredients: Optional[List[str]] = Field(None, description="선택한 선호 재료군")
    excluded_ingredients: Optional[List[str]] = Field(None, description="기호/알러지 제외 식재료")

# ------ API 응답 시 유저 정보를 돌려주는 스키마 --------
class UserResponse(BaseModel):
    id: int
    is_onboarded: bool

    model_config = ConfigDict(from_attributes=True)

# ------ 로그인 요청을 위한 스키마 ----------
class LoginRequest(BaseModel):
    provider: str
    social_id: str

# ------- 소셜 로그인 전용 스키마 --------
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

# ------ 이미지 변경 전용 스키마 ---------
class ProfileImageUpdateRequest(BaseModel):
    imageUrl: str