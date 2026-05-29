import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from app.api.deps import get_db, get_current_user
from app.schemas.user import UserResponse, UserOnboardingUpdate, UserInfo, NicknameUpdateRequest
from app.crud import crud_user
from app.models.user import User

router = APIRouter()

# --------------------------- 온보딩 업데이트 API ---------------------------------    
@router.patch("/onboarding", response_model=UserResponse)
async def update_onboarding(
    obj_in: UserOnboardingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)) -> Any:
    """
    [온보딩] 유저의 온보딩 정보(페르소나, 예산 등 8개 항목)를 업데이트합니다.\
    최초 입력 시에는 is_onboarded를 True로 바꾸고, 이후에는 정보만 갱신합니다.
    """
    
    return crud_user.update_user_onboarding(db, user_id=current_user.id, obj_in=obj_in)

# ----------------- 개인 프로필 조회 API -------------------------

@router.get("/me", response_model=UserInfo)
async def get_my_info(current_user: User = Depends(get_current_user)) -> Any:
    """
    [내 정보] 현재 로그인된 유저의 정보를 가져옵니다.
    """
    return current_user

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