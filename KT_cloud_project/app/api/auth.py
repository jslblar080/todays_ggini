from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any

from app.core import security
from app.core.config import settings
from app.api.deps import get_db
from app.schemas.user import Token, LoginRequest
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

# @router.post("/social-login/{provider}")
# def social_login(provider: SocialProvider, token: str, db: Session = Depends(get_db)):
#     """
#     프론트에서 받은 소셜 토큰으로 로그인/회원가입 처리
#     """
#     # 1. 각 provider(카카오, 구글 등) API를 호출해 유저 정보 획득 (가상 로직)
#     user_info = get_social_user_info(provider, token) 
    
#     # 2. DB에서 social_id로 기존 유저 확인
#     user = crud_user.get_by_social_id(db, social_id=user_info["id"])
    
#     if not user:
#         # 첫 접속이면 회원가입 처리 (와이어프레임 3번 페르소나 선택으로 유도)
#         user = crud_user.create_social_user(db, user_info, provider)
        
#     # 3. 우리 서비스 전용 JWT 토큰 발급
#     access_token = create_access_token(data={"sub": user.email})
#     return {"access_token": access_token, "token_type": "bearer", "is_new_user": not user.persona_id}

# @router.post("/login/social", response_model=Token)
# def social_auth(request: SocialLoginRequest, db: Session = Depends(get_db)):
#     # 1. 소셜 토큰 검증 (카카오/구글 서버에 확인 - 실제 구현은 라이브러리 활용)
#     social_data = verify_social_token(request.provider, request.token)
    
#     # 2. 기존 유저인지 확인
#     user = db.query(User).filter(User.social_id == social_data["id"]).first()
    
#     is_new_user = False
#     if not user:
#         # 가입된 적 없으면 즉시 생성 (회원가입 절차 자동화)
#         user = User(
#             email=social_data.get("email"),
#             provider=request.provider,
#             social_id=social_data["id"],
#             is_onboarded=False
#         )
#         db.add(user)
#         db.commit()
#         db.refresh(user)
#         is_new_user = True
    
#     # 3. 우리 서비스 전용 JWT 토큰 발급
#     access_token = create_access_token(data={"sub": str(user.id)})
#     return {"access_token": access_token, "token_type": "bearer", "is_new_user": is_new_user}

# @router.post("/login/guest", response_model=Token)
# def guest_auth(db: Session = Depends(get_db)):
#     # 게스트 유저 즉시 생성
#     user = User(provider=SocialProvider.GUEST, is_guest=True, is_onboarded=False)
#     db.add(user)
#     db.commit()
#     db.refresh(user)
    
#     access_token = create_access_token(data={"sub": str(user.id)})
#     return {"access_token": access_token, "token_type": "bearer", "is_new_user": True}