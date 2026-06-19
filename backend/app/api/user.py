import os
import traceback
import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import Any
from redis import Redis

from app.api.deps import get_db, get_current_user
from app.core.redis import get_redis, ShortTermDistributedLock
from app.schemas.user import (
 UserPersonaSettingUpdate, 
UserOnboardingSettingUpdate, 
UserInfo, 
NicknameUpdateRequest, 
PersonaRecommendResponse,
)
from app.crud import crud_user
from app.models.user import User

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODELING_ROOT = PROJECT_ROOT / "ai" / "modeling"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

if str(MODELING_ROOT) not in sys.path:
    sys.path.append(str(MODELING_ROOT))

from ai.modeling.services.modeling_service import create_persona_profile

router = APIRouter()

# --------------------------- 페르소나 추천 요청 API ---------------------------------
@router.post(
    "/recommend-personas", 
    response_model=PersonaRecommendResponse, 
    status_code=status.HTTP_200_OK
)
async def recommend_personas(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> Any:
    """
    유저가 성공적으로 저장한 가구 형태, 신체 스펙, 생활 조건을 RDB에서 읽어와
    AI 모델링 파트 엔진(`create_persona_profile`)과 연동하여 최적의 **페르소나 후보 4개**를 계산해 반환합니다.
    """
    lock_key = f"recommend_user_{current_user.id}"

    # 🎯 4. async with 문으로 로직 전체 감싸기
    # AI 프로파일링 연산 시간을 고려하여 만료 시간(TTL)을 7초로 넉넉하게 설정합니다.
    async with ShortTermDistributedLock(redis, lock_key, expire_seconds=5):
        try:
            # 1. 단 한 번의 조인 쿼리로 유저 관련 설정을 싹 긁어옵니다.
            user_details = db.query(User).options(
                joinedload(User.family_members),
                joinedload(User.persona_setting),
                joinedload(User.onboarding_setting)
            ).filter(User.id == current_user.id).first()

            if not user_details:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="유저 정보를 찾을 수 없습니다."
                )

            persona = user_details.persona_setting
            members = user_details.family_members

            # 공백이나 오타가 섞여 들어오더라도, 무조건 기획 명세인 '1인 가구' 또는 '다인 가구' 둘 중 하나로 강제 치환합니다.
            raw_type = persona.household_type.strip() if (persona and persona.household_type) else "1인 가구"
            
            # '1인' 글자가 포함되어 있다면 '1인 가구', 그 외의 모든 케이스(오타 포함)는 '다인 가구'로 매핑
            normalized_household = "1인 가구" if "1인" in raw_type else "다인 가구"

            # 2. 모델링 파트가 요청한 JSON 페이로드 구조
            request_payload = {
                "id": current_user.id,                                   
                "request_type": "profile_build",                         
                "household_type":normalized_household,
                "family_count": persona.family_count,
                "monthly_budget": persona.monthly_budget,
                "meals_per_day": persona.meals_per_day,
                "purpose": persona.purpose,
                "activity_level": persona.activity_level,
                "family_members": [
                    {
                        "nickname": member.nickname,
                        "gender": member.gender,
                        "age": member.age,
                        "height": float(member.height),
                        "weight": float(member.weight)
                    }
                    for member in members[:1]  # 최초 온보딩 단계이므로 대표자 1명만 안전 슬라이싱
                ]
            }
        
            # 3. 무거운 AI 프로파일링 연산 함수는 별도 워커 스레드 풀로 격리하여 비동기 대기
            modeling_response = await asyncio.to_thread(
                create_persona_profile,
                request_payload
            )

            if not modeling_response or "persona_candidates" not in modeling_response:
                raise ValueError("모델링 인프라로부터 올바른 응답을 받지 못했습니다.")

        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"모델링 연동 데이터 규격 오류: {str(error)}"
            )
        except Exception as error:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"페르소나 추천 엔진 연산 중 서버 내부 에러 발생: {str(error)}"
            )

        # 4. 모델링 파트에서 전달받은 확정 응답 스펙을 프론트엔드가 사용할 Response 포맷으로 정제합니다.
        # (모델링 파트가 준 칼로리 수치와 후보 리스트 4개를 그대로 가공하여 내보냅니다.)
        recommended_personas = []
        for item in modeling_response.get("persona_candidates", []):
            recommended_personas.append({
                "rank": item.get("rank"),
                "persona_id": item.get("persona_id"),          # 예: "persona_single_family1_meal3..."
                "description": item.get("description"),        # 화면 노출용 타이틀 매핑 (예: "실속관리 루틴형")
                "summary": item.get("summary"),                
            })

        # 계산된 권장 칼로리 DB에 저장
        persona.recommended_daily_calories = modeling_response["recommended_daily_calories"]
        db.commit()

        return {
            "recommended_daily_calories": modeling_response.get("recommended_daily_calories", 1800),
            "recommended_personas": recommended_personas
        }
    
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