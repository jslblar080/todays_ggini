from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio.client import Redis
import httpx
from jose import jwt, JWTError

from app.core import security
from app.core.config import settings
from app.api.deps import get_db
from app.core.redis import get_redis
from app.api.deps import get_current_user
from app.core.redis import redis_client
from app.models.user import User
from app.schemas.user import SocialLoginResponse, SocialLoginRequest, TokenRefreshRequest, TokenRefreshResponse, NaverLoginRequest
from app.crud import crud_user

router = APIRouter()

# -------------------- 공통 토큰 발급 및 Redis 저장 로직 --------------------
async def generate_and_save_tokens(user_id: int, redis: Redis) -> tuple[str, str]:
    """
    Access/Refresh 토큰을 생성하고, Refresh 토큰을 Redis에 저장합니다.
    """
    # 1. 토큰 이원화 발급
    access_token = security.create_access_token(subject=user_id)
    refresh_token = security.create_refresh_token(subject=user_id)
    
    # 2. Redis에 Refresh 토큰 저장 (Key: refresh_token:유저ID, 만료시간 설정)
    redis_key = f"refresh_token:{user_id}"
    await redis.setex(
        name=redis_key,
        time=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 일 단위를 초 단위로 변환
        value=refresh_token
    )
    
    return access_token, refresh_token

# ------------------- 게스트 로그인 --------------------------
@router.post("/guest/init", response_model=SocialLoginResponse)
async def initialize_guest_session(db: Session = Depends(get_db),redis: Redis = Depends(get_redis)):
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
    
    access_token, refresh_token = await generate_and_save_tokens(user.id, redis)
    
    # 소셜 로그인과 동일한 JSON 구조로 응답 구성
    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
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
async def google_login(request: SocialLoginRequest, db: Session = Depends(get_db),redis: Redis = Depends(get_redis)):
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

    # 3. 토큰 생성 및 Redis 저장
    access_token, refresh_token = await generate_and_save_tokens(user.id, redis)

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
            response = await client.get(settings.KAKAO_USER_INFO_URL, headers=headers)
            
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
async def kakao_login(request: SocialLoginRequest, db: Session = Depends(get_db),redis: Redis = Depends(get_redis)):
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

    # 토큰 생성 및 Redis 저장
    access_token, refresh_token = await generate_and_save_tokens(user.id, redis)
    
    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
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
            response = await client.get(settings.NAVER_USER_INFO_URL, headers=headers)
            
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
async def naver_login(request: NaverLoginRequest, db: Session = Depends(get_db), redis: Redis = Depends(get_redis)):
    """ [소셜 로그인] 네이버 토큰을 검증하고 로그인/가입을 처리합니다. """
    token_url = "https://nid.naver.com/oauth2.0/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.NAVER_CLIENT_ID,         
        "client_secret": settings.NAVER_CLIENT_SECRET, 
        "code": request.code,
        "redirect_uri": request.redirectUri            
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            token_response = await client.post(token_url, data=payload)
            
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="네이버 토큰 교환에 실패했습니다."
            )
            
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            # 네이버는 에러 시 error_description을 반환하기도 합니다.
            error_msg = token_data.get("error_description", "인증 토큰을 발급받을 수 없습니다.")
            raise HTTPException(status_code=400, detail=error_msg)
            
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="네이버 토큰 교환 서버와 통신할 수 없습니다."
        )
    
    naver_data = await verify_naver_token(access_token)

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

    # 토큰 생성 및 Redis 저장
    access_token, refresh_token = await generate_and_save_tokens(user.id, redis)
    
    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "user": {
            "id": user.id,
            "nickname": nickname,
            "email": user.email,
            "is_onboarded": user.is_onboarded
        }
    }

# ------------------------- 토큰 재발급 API -----------------------------
@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_access_token(
    request: TokenRefreshRequest,
    redis: Redis = Depends(get_redis)
):
    """
    [토큰 재발급] 만료되지 않은 유효한 Refresh Token을 검증하여 새로운 Access Token을 발급합니다.
    """
    refresh_token = request.refreshToken

    try:
        # 1. JWT 토큰 구조 및 서명 검증
        payload = jwt.decode(
            refresh_token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        # 방어 로직: sub가 없거나 토큰 타입이 refresh가 아닌 경우 차단
        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰 형식입니다."
            )

    except JWTError:
        # 토큰 자체가 변조되었거나 완전히 만료된 경우
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="만료되었거나 유효하지 않은 Refresh Token입니다. 다시 로그인 해주세요."
        )

    # 2. Redis에 저장된 해당 유저의 Refresh Token과 일치하는지 검증
    redis_key = f"refresh_token:{user_id}"
    saved_refresh_token = await redis.get(redis_key)

    if not saved_refresh_token or saved_refresh_token != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰 정보가 일치하지 않거나 세션이 만료되었습니다. 다시 로그인 해주세요."
        )

    # 3. 검증 완료: 새로운 Access Token 발급
    new_access_token = security.create_access_token(subject=user_id)

    return {
        "accessToken": new_access_token,
        "tokenType": "bearer"
    }


# ---------------------- 로그아웃 API (토큰 블랙리스트 등록) --------------------------
security_scheme = HTTPBearer()

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    redis: Redis = Depends(get_redis),
    db: Session = Depends(get_db)
):
    """
    [로그아웃] 
    - 공통: 현재 Access Token의 남은 시간만큼 블랙리스트에 등록하고, Refresh Token을 파기합니다.
    - 게스트 유저 분기: 로그아웃 즉시 DB에서 계정 정보를 완전히 삭제(Hard Delete)합니다.
    """
    access_token = credentials.credentials
    
    try:
        # 1. 토큰 디코딩하여 만료 시간(exp)과 유저 ID(sub) 추출
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        exp_time: int = payload.get("exp")
        
        if not user_id or not exp_time:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
            
        # 2. 토큰의 남은 수명(초 단위) 계산
        current_time = int(datetime.now(timezone.utc).timestamp())
        remaining_seconds = exp_time - current_time
        
        # 3. 토큰이 아직 살아있다면 남은 시간만큼 Redis 블랙리스트에 등록
        if remaining_seconds > 0:
            blacklist_key = f"blacklist:{access_token}"
            # 값은 아무거나 채워도 무방합니다 ("logouted")
            await redis.setex(name=blacklist_key, time=remaining_seconds, value="true")
            
        # 4. 해당 유저의 Refresh Token 저장소에서 삭제 (세션 파기)
        redis_refresh_key = f"refresh_token:{user_id}"
        await redis.delete(redis_refresh_key)

        # 디코딩한 user_id로 DB에서 유저 정보를 조회합니다.
        db_user = db.query(User).filter(User.id == int(user_id)).first()
        if db_user and (getattr(db_user, "is_guest", False) or db_user.provider == "guest"):
            # 게스트 유저가 확실하다면 DB에서 영구 삭제
            crud_user.delete_user(db, user_id=db_user.id)
            return {"detail": "게스트 로그아웃 완료: 임시 계정 데이터가 완전 파기되었습니다."}
        
        return {"detail": "성공적으로 로그아웃 되었습니다."}
        
    except jwt.ExpiredSignatureError:
        # 이미 만료된 토큰으로 로그아웃을 요청한 경우 처리
        return {"detail": "이미 만료된 세션입니다."}
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    
# ----------------- 회원 탈퇴 API (소셜/게스트 공통 완전 삭제) -----------------
@router.delete("/unregister", status_code=status.HTTP_200_OK)
async def unregister_user(
    request: Request,                  
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """
    [회원 탈퇴] DB 완전 삭제 + Refresh 토큰 파기 + Access 토큰 블랙리스트 등록
    """
    user_id = current_user.id
    
    # Access Token 블랙리스트 추가
    # Authorization 헤더에서 "Bearer <token>" 추출
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.split(" ")[1]
        try:
            # 토큰 디코딩하여 만료 시간 추출
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            exp_time = payload.get("exp")
            if exp_time:
                current_time = int(datetime.now(timezone.utc).timestamp())
                remaining_seconds = exp_time - current_time
                # 토큰 수명이 남아있다면 로그아웃과 동일하게 Redis 블랙리스트 등록
                if remaining_seconds > 0:
                    await redis.setex(name=f"blacklist:{access_token}", time=remaining_seconds, value="true")
        except jwt.JWTError:
            pass # 탈퇴 처리가 우선이므로 토큰 파싱 에러는 부드럽게 넘깁니다.

    # Redis에서 Refresh Token 세션 삭제 (자동 로그인 차단)
    await redis.delete(f"refresh_token:{user_id}")
    
    # DB에서 유저 데이터 완전 삭제 (Hard Delete)
    success = crud_user.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
        
    return {"detail": "회원 탈퇴가 성공적으로 완료되어 모든 데이터가 삭제되었습니다."}