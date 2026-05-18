from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any
import httpx

from app.core import security
from app.core.config import settings
from app.api.deps import get_db
from app.schemas.user import Token, LoginRequest, SocialLoginResponse, SocialLoginRequest
from app.crud import crud_user

router = APIRouter()

@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)) -> Any:
    """
    [토큰 발급] 인증된 소셜 ID 또는 게스트 ID를 바탕으로 JWT 액세스 토큰을 발급합니다.
    """
    # 1. 유저가 존재하는지 확인
    user = crud_user.get_user_by_social_id(db, social_id=login_data.social_id, provider=login_data.provider)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="등록되지 않은 사용자입니다. 먼저 로그인을 진행해주세요.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 계정입니다.")
    
    # 2. 비밀번호가 일치하는지 확인 (보안 모듈의 verify_password 사용)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 3. 로그인 성공 시 토큰 생성 및 반환
    return {
        "access_token": security.create_access_token(user.id, expires_delta=access_token_expires),
        "token_type": "bearer",
    }

@router.post("/guest/init", response_model=Token)
def initialize_guest_session(db: Session = Depends(get_db)) -> Any:
    """
    [게스트 초기화] 새로운 게스트 ID를 생성하고 즉시 토큰을 발급합니다.
    """
    import uuid
    guest_uuid = str(uuid.uuid4())
    
    # 게스트 유저 생성
    user = crud_user.create_user(
        db, 
        provider="guest", 
        social_id=guest_uuid
    )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

async def verify_google_token(access_token: str) -> dict:
    """구글 서버에 찔러서 이 토큰이 진짜인지 확인하고 유저 정보를 받아옵니다."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="유효하지 않은 구글 Access Token입니다."
            )
            
        return response.json()
    
@router.post("/google", response_model=SocialLoginResponse)
async def google_login(request: SocialLoginRequest, db: Session = Depends(get_db)):
    """
    [소셜 로그인] 구글 액세스 토큰을 검증하고 가입/로그인을 동시에 처리합니다.
    """
    # 1. 구글 서버 검증 및 유저 정보 추출
    google_user_info = await verify_google_token(request.accessToken)
    
    # 구글 고유 ID(sub)와 이메일 추출
    social_id = google_user_info.get("sub")
    email = google_user_info.get("email")
    google_nickname = google_user_info.get("name", "구글유저") # 구글에서 받아온 이름

    if not social_id:
        raise HTTPException(status_code=400, detail="구글 토큰에서 유저 정보를 찾을 수 없습니다.")

    # 2. DB에서 기존 유저 확인 (없으면 새로 생성 = Upsert)
    user = crud_user.get_user_by_social_id(db, social_id=social_id, provider="google")
    
    if not user:
        user = crud_user.create_user(
            db, 
            provider="google", 
            social_id=social_id, 
            email=email
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 계정입니다.")

    # 3. 백엔드 자체 JWT 발급
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    
    # MVP 단계: Refresh Token 로직이 아직 없다면 더미 값으로 뚫어둡니다.
    # 추후 security.create_refresh_token() 등으로 교체해야 합니다.
    refresh_token = "dummy_refresh_token_for_mvp"

    # 4. 프론트엔드가 요구한 JSON 구조로 응답
    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "user": {
            "id": user.id,
            "nickname": google_nickname
        }
    }