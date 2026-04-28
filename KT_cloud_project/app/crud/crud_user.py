from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

def create_user(db: Session, user: UserCreate):
    # 비밀번호 암호화
    hashed_password = get_password_hash(user.password)
    
    # DB 모델 객체 생성
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        persona_id=user.persona_id,
        monthly_budget=user.monthly_budget,
        cooking_skill=user.cooking_skill,
        purpose=user.purpose,
        preferred_style=user.preferred_style,
        variety_level=user.variety_level,
        excluded_ingredients=user.excluded_ingredients
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user