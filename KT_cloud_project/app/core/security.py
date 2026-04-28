from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "your-secret-key-very-important" # 나중에 .env로 분리
ALGORITHM = "HS256" # HMAC SHA-256 알고리즘
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # 토큰 유효 시간 (30분)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """JWT 토큰을 생성합니다."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# bcrypt 알고리즘을 사용한 암호화 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# bcrypt 사용한 이유
# 강력한 해싱: bcrypt는 비밀번호 해싱을 위해 설계된 알고리즘으로, 보안성이 높음.
# 비용 인자: bcrypt는 "비용 인자"라는 설정을 통해 해시 생성에 소요되는 시간을 조절할 수 있음. 이 값을 조정함으로써, 시스템의 성능이나 보안 요구 사항에 맞게 해시 생성의 난이도를 높이거나 낮출 수 있음.
# 고유한 해시 생성: bcrypt는 각 비밀번호 해시에 고유한 소금(salt)을 추가하여 동일한 비밀번호라도 매번 다른 해시를 생성.
# 다양한 플랫폼에서의 사용: bcrypt는 여러 프로그래밍 언어와 플랫폼에서 널리 사용되며, 많은 라이브러리와 프레임워크에서 기본적으로 지원됨.

def get_password_hash(password: str) -> str:
    """비밀번호를 해시화하여 반환"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """입력된 비밀번호와 해시된 비밀번호가 일치하는지 확인"""
    return pwd_context.verify(plain_password, hashed_password)