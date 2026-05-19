from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import httpx

from app.core import security
from app.core.config import settings
from app.api.deps import get_db
from app.schemas.user import LoginRequest, SocialLoginResponse, SocialLoginRequest
from app.crud import crud_user

router = APIRouter()

@router.post("/login", response_model=SocialLoginResponse) 
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    [토큰 재발급/일반 로그인] 인증된 소셜 ID 또는 게스트 ID를 바탕으로 자체 JWT 토큰을 발급합니다.
    (소셜/게스트 로그인과 동일한 규격의 응답을 반환합니다.)
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
    
    # 2. 자체 JWT 발급
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    
    # 공통 응답 규격에 맞춰 JSON 반환
    return {
        "accessToken": access_token,
        "refreshToken": "dummy_refresh_token_for_mvp",
        "user": {
            "id": user.id,
            # DB에 닉네임 컬럼이 없다면 가입 경로(provider)를 활용해 기본 닉네임 부여
            "nickname": f"{user.provider}유저", 
            "email": user.email,
            "is_onboarded": user.is_onboarded
        }
    }

@router.post("/guest/init", response_model=SocialLoginResponse)
def initialize_guest_session(db: Session = Depends(get_db)):
    """
    [게스트 초기화] 새로운 게스트 ID를 생성하고 즉시 토큰을 발급합니다.
    (소셜 로그인과 동일한 규격의 응답을 반환합니다.)
    """
    import uuid
    guest_uuid = str(uuid.uuid4())
    
    # 게스트 유저 생성
    user = crud_user.create_user(
        db=db, 
        provider="guest", 
        social_id=guest_uuid
    )
    
    # 자체 JWT 발급
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    # 소셜 로그인과 동일한 JSON 구조로 응답 구성
    return {
        "accessToken": access_token,
        "refreshToken": "dummy_refresh_token_for_mvp",
        "user": {
            "id": user.id,
            "nickname": "게스트", # 게스트용 기본 닉네임
            "email": user.email, # crud_user에서 자동 생성된 가상 이메일
            "is_onboarded": user.is_onboarded # 온보딩 분기용 플래그
        }
    }

# -------------------- 구글 소셜 로그인 -----------------------
async def verify_google_token(access_token: str) -> dict:
    """구글 서버에 찔러서 이 토큰이 진짜인지 확인하고 유저 정보를 받아옵니다."""
    url = f"https://oauth2.googleapis.com/tokeninfo?access_token={access_token}"
    headers= {"Authorization": f"Bearer {access_token}"}
    
    try:
        # 방어 1: timeout(5초) 설정으로 구글 서버 지연 시 무한 대기 방지
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
            
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="유효하지 않거나 만료된 구글 토큰입니다."
            )
        return response.json()
        
    except httpx.RequestError:
        # 방어 2: 네트워크 문제로 구글 서버와 통신 실패 시 503 에러 처리
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="구글 인증 서버와 통신할 수 없습니다."
        )
    
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
            "nickname": google_nickname,
            "email": email,
            "is_onboarded": user.is_onboarded
        }
    }

# ------------------ 카카오 소셜 로그인 -----------------------
async def verify_kakao_token(access_token: str) -> dict:
    """ 카카오 Access Token 검증 및 유저 정보 추출 """
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        # timeout(5초)을 설정하여 카카오 서버 장애 시 무한 대기 방지
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("https://kapi.kakao.com/v2/user/me", headers=headers)
            
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="유효하지 않은 카카오 토큰입니다."
            )
        return response.json()
    except httpx.RequestError:
        # 통신 자체에 실패했을 때의 503 에러 처리
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="카카오 인증 서버와 통신할 수 없습니다."
        )

@router.post("/kakao", response_model=SocialLoginResponse)
async def kakao_login(request: SocialLoginRequest, db: Session = Depends(get_db)):
    """ [소셜 로그인] 카카오 토큰을 검증하고 로그인/가입을 처리합니다. """
    kakao_info = await verify_kakao_token(request.accessToken)
    
    # 카카오는 고유 ID를 정수형(int)으로 주므로 문자열로 변환 필요
    social_id = str(kakao_info.get("id"))
    kakao_account = kakao_info.get("kakao_account", {})
    email = kakao_account.get("email")
    nickname = kakao_account.get("profile", {}).get("nickname", "카카오유저")

    if not social_id:
        raise HTTPException(status_code=400, detail="카카오 유저 정보를 파싱할 수 없습니다.")

    # DB 유저 조회 및 생성
    user = crud_user.get_user_by_social_id(db, social_id=social_id, provider="kakao")
    
    if not user:
        user = crud_user.create_user(
            db=db, 
            provider="kakao", 
            social_id=social_id,
            email=email
            )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 계정입니다.")

    # 자체 JWT 발급
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    
    return {
        "accessToken": access_token,
        "refreshToken": "dummy_refresh_token_for_mvp",
        "user": {
            "id": user.id,
            "nickname": nickname,
            "email": user.email,
            "is_onboarded": user.is_onboarded # 👈 프론트가 화면 분기할 때 쓸 변수
        }
    }

# ---------------------- 네이버 소셜 로그인 ---------------------------
async def verify_naver_token(access_token: str) -> dict:
    """ 네이버 Access Token 검증 및 유저 정보 추출 """
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        # timeout(5초) 방어 로직 동일 적용
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("https://openapi.naver.com/v1/nid/me", headers=headers)
            
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="유효하지 않은 네이버 토큰입니다."
            )
        return response.json()
    except httpx.RequestError:
        # 통신 실패 처리 동일 적용
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="네이버 인증 서버와 통신할 수 없습니다."
        )

@router.post("/naver", response_model=SocialLoginResponse)
async def naver_login(request: SocialLoginRequest, db: Session = Depends(get_db)):
    """ [소셜 로그인] 네이버 토큰을 검증하고 로그인/가입을 처리합니다. """
    naver_data = await verify_naver_token(request.accessToken)

    # 네이버 API 전용 성공 코드("00") 확인 로직 추가
    if naver_data.get("resultcode") != "00":
        raise HTTPException(status_code=400, detail="네이버 회원 정보 가져오기에 실패했습니다.")
    
    # 네이버는 response 라는 키 안에 실제 데이터가 들어있음
    naver_response = naver_data.get("response", {})
    social_id = naver_response.get("id") # 네이버 고유 고정 ID (문자열형태)
    email = naver_response.get("email")
    nickname = naver_response.get("name", "네이버유저")

    if not social_id:
        raise HTTPException(status_code=400, detail="네이버 유저 정보를 파싱할 수 없습니다.")

    # DB 유저 조회 및 생성
    user = crud_user.get_user_by_social_id(db, social_id=social_id, provider="naver")
    
    if not user:
        user = crud_user.create_user(
            db=db, 
            provider="naver", 
            social_id=social_id, 
            email=email
            )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 계정입니다.")

    # 자체 JWT 발급
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    
    return {
        "accessToken": access_token,
        "refreshToken": "dummy_refresh_token_for_mvp",
        "user": {
            "id": user.id,
            "nickname": nickname,
            "email": user.email,
            "is_onboarded": user.is_onboarded
        }
    }