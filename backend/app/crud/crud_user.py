from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app.models.user import User, UserFamilyMember, UserPersonaSetting, UserOnboardingSetting
from app.schemas.user import UserPersonaSettingUpdate, UserOnboardingSettingUpdate

def get_user_by_social_id(db: Session, social_id: str, provider: str):
    return db.query(User).filter(User.social_id == social_id, User.provider == provider).first()

def create_user(db: Session, provider: str, social_id: str, email: Optional[str] = None):
    """
    4가지 방식(google, naver, kakao, guest)에 따른 유저 생성
    """
    # 이메일이 전달되지 않았을 경우 고유한 가상 이메일 생성(게스트 로그인)
    if email is None:
        email = f"{provider}_{social_id}@guest.example.com"

    db_user = User(
        provider=provider,
        social_id=social_id,
        email=email,
        is_guest=(provider == "guest"),
        markets=["쿠팡", "컬리", "네이버"]
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    """
    [Hard Delete] DB에서 유저 레코드를 완전히 삭제합니다.
    (종속된 데이터가 있다면 테이블 설계에 따라 CASCADE 삭제되거나 함께 지워져야 합니다.)
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False
        
    db.delete(db_user)
    db.commit()
    return True

def update_user_selected_style(db: Session, user_id: int, style_id: str) -> Optional[User]:
    """
    [식단 스타일 업데이트 재사용 함수]
    사용자가 최종 선택한 식단 스타일 ID를 UserOnboardingSetting(취향) 테이블에 저장/갱신합니다.
    백그라운드 태스크 및 라우터에서 공통으로 재사용하기 위해 최적화되었습니다.
    """
    # 1. 1:1 온보딩 취향 설정 테이블에서 해당 유저 레코드 조회
    onboarding_setting = db.query(UserOnboardingSetting).filter(UserOnboardingSetting.user_id == user_id).first()
    
    if not onboarding_setting:
        # 기존 레코드가 없다면 신규 생성 (Insert)
        onboarding_setting = UserOnboardingSetting(user_id=user_id, selected_style_id=style_id)
        db.add(onboarding_setting)
    else:
        # 기존 레코드가 있다면 스타일 ID만 갱신 (Update)
        onboarding_setting.selected_style_id = style_id
        
    db.commit()
    
    # 2. 변경 사항이 반영된 최신 유저 객체를 관계형 데이터와 함께 반환
    return db.query(User).options(
        joinedload(User.family_members),
        joinedload(User.persona_setting),
        joinedload(User.onboarding_setting)
    ).filter(User.id == user_id).first()

def update_user_persona_setting(db: Session, *, user_id: int, obj_in: UserPersonaSettingUpdate) -> User:
    """
    [페르소나 및 가구원 정보 업데이트]
    1. user_persona_settings 테이블 (1:1) 존재 여부 확인 후 생성 또는 수정
    2. user_family_members 테이블 (1:N) 기존 유저 데이터 전체 삭제 후 신규 데이터 Bulk 일괄 삽입 (PUT 방식 정석)
    """
    # 1. 1:1 페르소나 설정 테이블 처리
    persona_setting = db.query(UserPersonaSetting).filter(UserPersonaSetting.user_id == user_id).first()
        
    # 업데이트할 데이터 파싱 (family_members 제외한 순수 필드들)
    update_data = obj_in.model_dump(exclude={"family_members"}, exclude_unset=True)
        
    if not persona_setting:
        # 기존에 설정이 없었다면 신규 레코드 생성
        persona_setting = UserPersonaSetting(user_id=user_id, **update_data)
        db.add(persona_setting)
    else:
        # 기존 설정이 있다면 덮어쓰기
        for field, value in update_data.items():
            setattr(persona_setting, field, value)

    # 2. 1:N 가구원(신체 스펙) 테이블 처리
    if obj_in.family_members is not None:
        # [안전한 데이터 갱신 전략] 기존 등록된 가구원 데이터를 싹 밀어버립니다. (Cascade 방지 및 정합성 보장)
        db.query(UserFamilyMember).filter(UserFamilyMember.user_id == user_id).delete()
            
        # 새로 넘어온 가구원 리스트를 순회하며 Bulk 생성
        for member_in in obj_in.family_members:
            new_member = UserFamilyMember(
                user_id=user_id,
                **member_in.model_dump()
            )
            db.add(new_member)

    # DB 트랜잭션 커밋 및 동기화
    db.commit()
        
    # 3. 갱신된 유저 객체를 연관 테이블(joinedload)과 함께 리턴하여 라우터의 UserInfo 응답 규격 만족
    return db.query(User).options(
        joinedload(User.family_members),
        joinedload(User.persona_setting),
        joinedload(User.onboarding_setting)
    ).filter(User.id == user_id).first()


def update_user_onboarding_setting(db: Session, *, user_id: int, obj_in: UserOnboardingSettingUpdate) -> User:
    """
    [온보딩 세부 취향 설정 업데이트]
    1. user_onboarding_settings 테이블 (1:1) 존재 여부 확인 후 생성 또는 수정
    2. 최초 온보딩 완료 시점인 경우 users 테이블의 is_onboarded 플래그를 True로 전환
    """
    # 1. 1:1 취향 설정 테이블 처리
    taste_preference = db.query(UserOnboardingSetting).filter(UserOnboardingSetting.user_id == user_id).first()
        
    # 업데이트할 데이터 파싱 (is_onboarded는 User 테이블 필드이므로 제외)
    update_data = obj_in.model_dump(exclude={"is_onboarded"}, exclude_unset=True)
        
    if not taste_preference:
        taste_preference = UserOnboardingSetting(user_id=user_id, **update_data)
        db.add(taste_preference)
    else:
        for field, value in update_data.items():
            setattr(taste_preference, field, value)

    # 2. 메인 유저 테이블 상태 제어 (최초 온보딩 완료 여부 플래그 업데이트)
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_onboarded = True

    # DB 트랜잭션 커밋
    db.commit()
        
    # 갱신된 최신 유저 통짜 데이터 리턴 (joinedload 장착)
    return db.query(User).options(
        joinedload(User.family_members),
        joinedload(User.persona_setting),
        joinedload(User.onboarding_setting)
    ).filter(User.id == user_id).first()