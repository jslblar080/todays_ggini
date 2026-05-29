from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from redis.asyncio.client import Redis

from app.core.redis import get_redis
from app.db.session import get_db
from app.models.user import User
from app.core.security import SECRET_KEY, ALGORITHM
from app.schemas.user import TokenPayload

security_scheme = HTTPBearer()

async def get_current_user(
    db: Session = Depends(get_db), 
    redis: Redis = Depends(get_redis),
    token: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        actual_token = token.credentials
        # 블랙리스트 검증 로직
        is_blacklisted = await redis.get(f"blacklist:{actual_token}")
        if is_blacklisted:
            print(f"DEBUG: Blacklisted token approach detected")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="로그아웃되거나 파기된 토큰입니다. 다시 로그인 해주세요.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        payload = jwt.decode(actual_token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)

        # [방어 로직] Access Token이 아닌 Refresh Token을 들고 일반 API를 호출한 경우 차단
        if getattr(token_data, "type", None) == "refresh":
            print("DEBUG: Refresh token cannot be used for general APIs")
            raise credentials_exception
        
        if token_data.sub is None:
            print("DEBUG: Token sub is None")
            raise credentials_exception
            
        # ID를 int로 변환하여 조회
        user_id = int(token_data.sub)
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            print(f"DEBUG: User with ID {user_id} not found in DB")
            raise credentials_exception

        if not user.is_active:
            raise HTTPException(status_code=400, detail="비활성화된 계정입니다.")
            
        return user
        
    except JWTError as e:
        print(f"DEBUG: JWT Decode Error - {e}")
        raise credentials_exception
    except Exception as e:
        print(f"DEBUG: Unexpected Error - {e}")
        raise credentials_exception