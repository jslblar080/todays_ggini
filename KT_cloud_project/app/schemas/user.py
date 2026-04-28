from pydantic import BaseModel, Field
from typing import List, Optional

class UserCreate(BaseModel):
    username: str # 사용자 이름
    password: str # 비밀번호
    persona_id: int = Field(..., ge=1, le=4)  # 1~4번 캐릭터
    monthly_budget: int = Field(default=300000, ge=0) # 예산
    cooking_skill: int = Field(default=3, ge=1, le=5) # 요리 능력
    purpose: str # 사용자의 목적
    preferred_style: str = "상관없음" # 선호하는 스타일
    variety_level: int = Field(default=2, ge=1, le=3) # 다양성 수준
    excluded_ingredients: Optional[List[str]] = [] # 제외할 재료 목록

class UserResponse(BaseModel):
    id: int # 사용자 id
    username: str # 사용자 이름
    
    class Config:
        from_attributes = True # DB 모델을 Pydantic으로 자동 변환

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"