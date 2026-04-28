from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas.user import UserCreate, UserResponse
from app.crud import crud_user
from app.models.user import User

router = APIRouter()

# DB 세션을 가져오는 의존성 주입 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup", response_model=UserResponse)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    # 1. 이미 존재하는 유저인지 확인
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="이미 존재하는 아이디입니다."
        )
    # 2. 유저 생성 로직 호출
    try:
        new_user = crud_user.create_user(db=db, user=user_in)
        return new_user
    except Exception as e:
        # DB 에러 등 예상치 못한 오류 발생 시 500 에러 반환
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다."
        )