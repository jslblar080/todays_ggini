from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.api.deps import get_db, get_current_user
from app.schemas.user import UserResponse, UserOnboardingUpdate, UserInfo, AIUserProfileResponse
from app.crud import crud_user
from app.models.user import User

router = APIRouter()

# ------------------------- 회원가입 API ----------------------------------
@router.post("/signup", response_model=UserResponse)
def signup(provider: str, social_id: str, email: str = None, db: Session = Depends(get_db)) -> Any:
    """
    [회원가입] 새로운 유저를 생성합니다.
    """
    if provider not in ["google", "naver", "kakao", "guest"]:
        raise HTTPException(status_code=400, detail="지원하지 않는 로그인 방식입니다.")

    # 1. 기존 유저인지 확인
    user = crud_user.get_user_by_social_id(db, social_id=social_id, provider=provider)
    
    # 2. 신규 유저라면 생성
    if not user:
        user = crud_user.create_user(
            db, 
            provider=provider, 
            social_id=social_id, 
            email=email
        )
    
    return user

# --------------------------- 온보딩 업데이트 API ---------------------------------    
@router.patch("/onboarding", response_model=UserResponse)
def update_onboarding(
    obj_in: UserOnboardingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)) -> Any:
    """
    [온보딩] 유저의 온보딩 정보(페르소나, 예산 등 8개 항목)를 업데이트합니다.\
    최초 입력 시에는 is_onboarded를 True로 바꾸고, 이후에는 정보만 갱신합니다.
    """
    
    return crud_user.update_user_onboarding(db, user_id=current_user.id, obj_in=obj_in)

@router.get("/me", response_model=UserInfo)
def get_my_info(current_user: User = Depends(get_current_user)) -> Any:
    """
    [내 정보] 현재 로그인된 유저의 정보를 가져옵니다.
    """
    return current_user

# --------------------------- modeling -> back 사용자 프로필 설정 API ------------------------
@router.post("/ai-profile-sync")
async def sync_user_ai_profile(
    profile_data: AIUserProfileResponse,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [Modeling -> Back] 
    모델링 파트에서 분석/가공 완료된 사용자의 AI 맞춤형 프로필 설정값을 받아 DB에 업데이트합니다.
    """
    try:
        # 1. 현재 유저 정보 조회
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        # 2. AI가 보내준 정교한 설정값들을 DB에 업데이트 (JSON 구조를 dict로 변환하여 저장)
        user.ai_meal_budget = profile_data.meal_budget
        user.ai_max_difficulty = profile_data.max_difficulty
        user.ai_weights = profile_data.weights.dict() # pydantic 모델을 딕셔너리로 변환
        
        # 필요하다면 패널티 강도 등도 저장
        # user.ai_diversity_penalty = profile_data.diversity_penalty_strength

        db.commit()
        db.refresh(user)

        return {
            "status": "success",
            "message": "AI 맞춤형 사용자 프로필이 성공적으로 동기화되었습니다.",
            "updated_weights": user.ai_weights
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"프로필 동기화 중 오류 발생: {str(e)}")