from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
from app.core.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

def create_token(subject: Union[str, Any], token_type: str, expires_delta: timedelta) -> str:
    """JWT 토큰(Access/Refresh 공통)을 생성합니다."""
    expire = datetime.now(timezone.utc) + expires_delta
    
    # "sub" (Subject) 클레임에 유저의 고유 ID를 담고,
    # "type" 클레임에 토큰의 목적(access 또는 refresh)을 명시합니다.
    to_encode = {
        "exp": expire, 
        "sub": str(subject),
        "type": token_type
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """Access Token을 생성합니다."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return create_token(subject, "access", expires_delta)

def create_refresh_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """Refresh Token을 생성합니다."""
    if expires_delta is None:
        # 새로 추가한 REFRESH_TOKEN_EXPIRE_MINUTES 설정을 사용합니다.
        expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        
    return create_token(subject, "refresh", expires_delta)