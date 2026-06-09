import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import Any

from app.api.deps import get_db, get_current_user
from app.schemas.user import (
 UserPersonaSettingUpdate, 
UserOnboardingSettingUpdate, 
UserInfo, 
NicknameUpdateRequest, 
UserPersonaSettingInfo
)
from app.crud import crud_user
from app.models.user import User

router = APIRouter()

# --------------------------- 페르소나 추천 요청 API ---------------------------------
# @router.post(
#     "/recommend-personas", 
#     response_model=PersonaRecommendResponse,
#     status_code=status.HTTP_200_OK,
#     summary="[온보딩 1단계] 가구/스펙 기반 페르소나 4종 추천"
# )
# async def recommend_personas(
#     payload: UserPersonaSettingInfo,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ) -> Any:
#     """
#     유저가 입력한 가구 형태, 신체 스펙 배열, 생활 조건을 기반으로\n
#     AI 모델링 파트(또는 추천 엔진)와 연동하여 최적의 **페르소나 후보 4개**를 계산해 반환합니다.\n
#     *이 단계에서는 유저가 선택하기 전이므로 DB 설정을 변경(Write)하지 않습니다.*
#     """
#     try:
#         # TODO: 모델링 담당 파트가 작성해 줄 코어 매칭 알고리즘 함수 연동 구간
#         # recommended = crud_user.get_persona_recommendations(db, payload=payload)
        
#         # 임시 Mock 데이터 구조 (프론트엔드 연동 테스트용 프로토타입)
#         mock_response = {
#             "recommended_personas": [
#                 {
#                     "persona_id": 1,
#                     "title": "알뜰살뜰 식비 절약가",
#                     "tags": ["#식비절약", f"#다인가구"],
#                     "description": f"한 달 500000원 예산에 맞춰 가성비 위주의 식재료로 영양소를 알차게 채우는 알뜰 식단 스타일입니다.",
#                 },
#                 {
#                     "persona_id": 2,
#                     "title": "영양 만점 밸런서",
#                     "tags": ["#영양균형", "#단백질업"],
#                     "description": "기초대사량과 활동량을 고려하여 탄단지 비율을 황금 밸런스로 유지해 주는 정석 건강 건강식 스타일입니다.",
#                 }
#             ]
#         }
#         return mock_response
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"페르소나 추천 연산 중 내부 에러 발생: {str(e)}"
#         )
    
# --------------------------- 페르소나 설정 및 가구원 정보 업데이트 API ---------------------------------
@router.put("/persona-setting", response_model=UserInfo)
async def update_persona_setting(
    obj_in: UserPersonaSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    유저의 가구 형태, 예산, 목적, 하루 식사 수, 최종 고른 페르소나 ID 및 가구원 신체 스펙을 저장/수정합니다.\n
    피그마의 **[페르소나 설정/재설정]** 컴포넌트와 1:1로 매핑되는 API입니다.
    """
    # crud_user 단에서 유저의 가구원(1:N) 테이블과 페르소나 설정(1:1) 테이블만 트랜잭션으로 수정합니다.
    updated_user = crud_user.update_user_persona_setting(db, user_id=current_user.id, obj_in=obj_in)
    return updated_user

# --------------------------- 온보딩 설정 업데이트 API ---------------------------------
@router.put("/onboarding-setting", response_model=UserInfo)
async def update_onboarding_setting(
    obj_in: UserOnboardingSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    유저 개인의 선호 카테고리, 선호/제외 식재료, 요리 실력, 다양성 지표를 저장/수정합니다.\n
    피그마의 **[온보딩 취향 설정/재설정]** 컴포넌트와 1:1로 매핑되는 API입니다.
    """
    # crud_user 단에서 온보딩 취향(1:1) 테이블 정보만 깔끔하게 수정합니다.
    updated_user = crud_user.update_user_onboarding_setting(db, user_id=current_user.id, obj_in=obj_in)
    return updated_user

# ----------------- 개인 프로필 조회 API -------------------------

@router.get("/me", response_model=UserInfo)
async def get_my_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    [내 정보] 현재 로그인된 유저의 정보와 함께, 분리된 테이블 데이터들(가구원, 페르소나 설정, 취향)을 한 번에 조회합니다.
    """
    # 3개 분리 테이블 관계를 한 번에 긁어오는 joinedload 쿼리 사용
    user_info = db.query(User).options(
        joinedload(User.family_members),
        joinedload(User.persona_setting),
        joinedload(User.onboarding_setting)
    ).filter(User.id == current_user.id).first()

    if not user_info:
        raise HTTPException(status_code=404, detail="유저 정보를 찾을 수 없습니다.")

    return user_info

# -------------- 닉네임 변경 API ---------------------
@router.patch("/profile")
async def update_nickname(
    request: NicknameUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.nickname = request.nickname
    db.commit()
    db.refresh(current_user)
    
    return {"id": current_user.id, "nickname": current_user.nickname}

# ----------------- 프로필 이미지 변경 API ---------------------------
@router.post("/profile/image")
async def update_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [프로필 이미지 변경] 원본 파일명 앞에 유저 ID를 붙여서 충돌을 방지하고 로컬에 저장합니다.
    """
    UPLOAD_DIR = "app/static/images"
    
    # 1. 유저 ID와 원본 파일명 결합 (예: 유저ID 4, 파일명 abc123.jpg -> "4_abc123.jpg")
    filename = f"{current_user.id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # 2. 로컬 하드디스크에 파일 저장
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 저장 실패: {str(e)}")
    
    # 3. 저장된 고유 파일명으로 URL 조립
    image_url = f"http://localhost:8000/images/{filename}"
    
    # 4. DB에 이미지 URL 업데이트
    current_user.image_url = image_url
    db.commit()
    db.refresh(current_user)
    
    return {
        "imageUrl": current_user.image_url
    }