from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.attributes import flag_modified
from datetime import date, datetime
from redis.asyncio import Redis
import redis as sync_redis
import uuid
import calendar
import hashlib
import json

from app.api.deps import get_db, get_current_user
from app.core.redis import get_redis
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.user import User
from app.crud.crud_user import update_user_selected_style
from app.models.meal import MealPlan
from app.schemas.meal import (
    DailyMealDetailResponse,
    MealConfirmResponse,
    CalendarResponse,
    MealSwapResponse,
    MealSwapRequest,
    MenuUpdateRequest,
    AlternativeMenuResponse,
    StyleSelectRequest,
)
from app.crud import crud_meal
from app.utils.image_search import get_food_image_url


import asyncio
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODELING_ROOT = PROJECT_ROOT / "ai" / "modeling"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

if str(MODELING_ROOT) not in sys.path:
    sys.path.append(str(MODELING_ROOT))

from ai.modeling.services.modeling_service import (
    create_meal_style_candidates,
    create_monthly_plan,
)

router = APIRouter()

# ---------------------------  프론트엔드 호출용 API ---------------------------------
# -------------------- 월간 식단 요청(비동기 실행) ----------------------------
@celery_app.task(
    name="app.api.meal.background_monthly_plan_task",
    acks_late=True, # 작업을 완전히 '성공'했을 때만 큐에서 제거 (중간에 워커가 죽으면 재시도하도록 설정)
    max_retries=3   # 실패 시 최대 3번까지 자동 재시도)
)
def background_monthly_plan_task(
    job_id: str, user_id: int, selected_style_id: str
):
    """
    API 응답이 나간 뒤 백그라운드에서 조용히 실행될 함수
    """
    # 워커 내부에서 사용할 동기형 Redis 클라이언트 생성 (동기 컨텍스트 환경)
    redis_client = sync_redis.from_url("redis://localhost:6379/0")

    # [도우미 함수] 반복되는 Redis 상태 업데이트 코드를 깔끔하게 관리하기 위해 선언
    def update_status(job_status: str, progress: str, error: str = None):
        data = {"status": job_status, "progress": progress}
        if error:
            data["error"] = error
        redis_client.setex(
            name=f"job_status:{job_id}",
            time=86400,  # 1일(24시간) TTL
            value=json.dumps(data, ensure_ascii=False)
        )

    # 작업 시작 기록
    update_status("PROCESSING", "프로필 분석 중")

    # 💡 백그라운드 작업이므로 DB 세션을 새로 엽니다.
    db = SessionLocal()

    try:
        current_user = db.query(User).options(
            joinedload(User.family_members),
            joinedload(User.persona_setting),
            joinedload(User.onboarding_setting)
        ).filter(User.id == user_id).first()

        if not current_user:
            raise ValueError("유저를 찾을 수 없습니다.")

        update_user_selected_style(db, current_user.id, selected_style_id)

        # --- AI 요청 로직 (기존 request_monthly_plan과 동일) ---
        today = date.today()

        _, last_day = calendar.monthrange(today.year, today.month)
        days_remaining = last_day - today.day + 1

        selected_style = build_selected_style_from_style_id(
            style_id=selected_style_id,
        )

        request_type = "monthly_plan"

        user_profile = build_modeling_profile_from_user(
            current_user=current_user,
            period_days=days_remaining,
        )

        modeling_payload = {
            "id": get_modeling_user_id(current_user),
            "request_type": request_type,
            "selected_style": selected_style,
            "profile":user_profile,
        }

        # ----------------------- [AI 응답 결과 캐싱 구간 ] -----------------------
        update_status("PROCESSING", "기존 식단 캐시 확인 중")

        # 딕셔너리 내부 순서가 달라도 같은 해시가 나오도록 고정 정렬 후 JSON 문자열 덤프
        # (user_id를 제외한 user_profile과 request_type, selected_style_id만 조합하여 공유 캐시 효율 극대화)
        profile_json_string = json.dumps(user_profile, sort_keys=True, ensure_ascii=False)
        raw_cache_string = f"{request_type}:{selected_style_id}:{profile_json_string}"
        
        # MD5로 32글자 고유 해시값 생성 후 최종 Redis 캐시 키 완성
        payload_hash = hashlib.md5(raw_cache_string.encode("utf-8")).hexdigest()
        cache_key = f"ai:monthly_plan:{payload_hash}"

        # Redis에서 해당 캐시가 존재하는지 비동기 조회 (Cache Hit 확인)
        cached_response = redis_client.get(cache_key)

        if cached_response:
            # [Cache Hit] 동일한 조건의 캐시 발견 시, 외부 AI 호출을 스킵하고 즉시 파싱
            update_status("PROCESSING", "식단 캐시 매칭 성공 (AI 연산 스킵)")
            ai_response = json.loads(cached_response)
        else:
            # [Cache Miss] 일치하는 캐시가 없으므로 실제 AI 호출 진행
            update_status("PROCESSING", "새로운 식단 생성 중 (AI 연산)")
            
            # AI 호출
            ai_response = create_monthly_plan(modeling_payload)

            # 다음 중복 요청을 위해 연산 결과를 Redis에 캐싱 (TTL: 2일 = 172800초)
            redis_client.setex(
                name=cache_key,
                time=172800,
                value=json.dumps(ai_response, ensure_ascii=False)
            )
        # ------------------------------------------------------------------

        days_data = ai_response.get("monthly_plan", {}).get("days", [])

        update_status("PROCESSING", "DB에 결과 저장 중")
        # 💡 DB 저장
        crud_meal.save_monthly_plan(
            db=db, user_id=current_user.id, ai_days_list=days_data
        )

        # 모든 작업 완료 기록
        update_status("COMPLETED", "완료")

    except Exception as e:
        print(f"Background Task Error: {str(e)}")
        update_status("FAILED", "오류 발생", error=str(e))
    finally:
        db.close()  # 필수: 작업이 끝나면 DB 세션 닫기


# ---------------------- 식단 생성 트리거 --------------------------------
@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_meal_plans_trigger(
    request: StyleSelectRequest,  # 프론트에서 넘어온 스타일 ID
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    """
    [화면 6] 프로필 기반 식단 생성 트리거
    FastAPI BackgroundTasks로 백그라운드 작업을 호출하고 작업 ID를 반환합니다.
    """

    # 1. 고유한 작업 ID 생성
    job_id = f"job_{uuid.uuid4().hex[:8]}"

    # 백그라운드 태스크가 돌기 전에 상태를 먼저 PENDING으로 등록
    # 프론트가 0.1초 만에 너무 빨리 상태 조회를(Polling) 요청해서 404가 뜨는 Race Condition 방지용
    await redis.setex(
        name=f"job_status:{job_id}",
        time=86400,
        value=json.dumps({"status": "PENDING", "progress": "작업 대기 중"}, ensure_ascii=False)
    )

    # 2. BackgroundTasks 대신 Celery 비동기 큐에 작업 위임 (.delay 사용)
    # 인자는 반드시 기본 원시 타입(str, int)들만 순서대로 넘겨야 합니다.
    background_monthly_plan_task.delay(
        job_id=job_id,
        user_id=current_user.id,
        selected_style_id=request.selected_style_id
    )

    # 3. 고유 Job ID를 프론트에 즉시 반환
    return {
        "job_id": job_id,
        "estimated_seconds": 10,
        "stages": ["프로필 분석", "식단 후보 생성", "최적 조합 선정", "DB 저장"],
    }

# ------------------------ 작업 상태 폴링 API --------------------------
@router.get("/generate/status/{job_id}")
async def check_generation_status(job_id: str, redis: Redis = Depends(get_redis)):
    """
    프론트엔드가 지속적으로 호출하여 작업 완료 여부를 확인하는 API입니다.
    """
    job_info = await redis.get(f"job_status:{job_id}")
    if not job_info:
        raise HTTPException(
            status_code=404, detail="존재하지 않거나 만료된 작업입니다."
        )

    return json.loads(job_info)


# --------------------- 생성된 30일 식단 최종 확정 및 요약 정보 반환 API -----------------------
@router.post("/confirm", response_model=MealConfirmResponse)
async def confirm_meal_plan(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    [화면 9] 생성된 30일 식단을 최종 확정하고 요약 정보를 반환합니다.
    """
    # 1. 해당 유저의 가장 최근 생성된(혹은 임시 상태인) 식단 리스트 조회
    # (실제 서비스에서는 is_confirmed 등의 상태 값을 활용할 수 있습니다)
    plans = (
        db.query(MealPlan)
        .filter(MealPlan.user_id == current_user.id)
        .order_by(MealPlan.meal_date.asc())
        .all()
    )

    if not plans:
        raise HTTPException(status_code=404, detail="확정할 식단 내역이 없습니다.")

    # 2. 명세서 규격에 맞는 요약 데이터 계산
    start_date = plans[0].meal_date
    end_date = plans[-1].meal_date
    duration = (end_date - start_date).days + 1

    total_price = sum(p.estimated_cost for p in plans if p.estimated_cost)
    total_calories = sum(p.total_calories for p in plans if p.total_calories)
    avg_calories = total_calories // duration if duration > 0 else 0

    # 3. 응답 반환
    return {
        "plan_id": f"plan_{current_user.id}_{start_date.strftime('%Y%m%d')}",
        "start_date": start_date,
        "end_date": end_date,
        "duration_days": duration,
        "total_price_per_plan": total_price,
        "average_calories_per_plan": avg_calories,
        "generated_at": datetime.now(),  # 혹은 DB의 생성일시 컬럼 사용
    }


# -------------------- 월간 캘린더 조회 API ----------------------------
@router.get("/calendar", response_model=CalendarResponse)
async def get_monthly_calendar(
    month: str,  # "2026-04" 형식
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    월간 캘린더를 조회합니다.
    """
    # 1. 해당 월의 시작일과 마지막일 계산
    year, mon = map(int, month.split("-"))
    last_day = calendar.monthrange(year, mon)[1]
    start_date = date(year, mon, 1)
    end_date = date(year, mon, last_day)

    # 2. DB에서 해당 기간의 식단 조회
    plans = (
        db.query(MealPlan)
        .filter(
            MealPlan.user_id == current_user.id,
            MealPlan.meal_date >= start_date,
            MealPlan.meal_date <= end_date,
        )
        .all()
    )

    plan_dict = {p.meal_date: p for p in plans}

    # 3. 1일부터 말일까지 루프를 돌며 days 배열 생성
    days_list = []
    total_price = 0
    total_cal = 0
    meal_count = 0

    for day in range(1, last_day + 1):
        curr_date = date(year, mon, day)
        plan = plan_dict.get(curr_date)

        if plan:
            # DB의 content JSON에서 필요한 필드만 추출
            extracted_meals = []
            # plan.content는 일일 식단(meals) 리스트
            for meal in plan.content or []:
                # Mock 데이터 구조에 맞춰 selected_menu 내부를 탐색
                selected_menu = meal.get("selected_menu") or {}

                # 데이터가 None이거나 키가 없을 때를 대비한 방어 로직
                raw_menu_id = selected_menu.get("menu_id")
                raw_name = selected_menu.get("name")

                extracted_meals.append(
                    {
                        "slot": meal.get("meal_order") or 1,
                        "meal_id": str(raw_menu_id) if raw_menu_id is not None else "",
                        "menu_name": raw_name or "메뉴 정보 없음",
                    }
                )

            # 식단이 있는 날
            day_data = {
                "date": curr_date,
                "calories_per_day": int(plan.total_calories)
                if plan.total_calories is not None
                else None,
                "price_per_day": int(plan.estimated_cost)
                if plan.estimated_cost is not None
                else None,
                "meals": extracted_meals,
            }
            total_price += int(plan.estimated_cost or 0)
            total_cal += int(plan.total_calories or 0)
            meal_count += 1
        else:
            # 식단이 없는 날 (명세서 규격 준수)
            day_data = {
                "date": curr_date,
                "calories_per_day": None,
                "price_per_day": None,
                "meals": [],
            }
        days_list.append(day_data)

    return {
        "month": month,
        "duration_days": meal_count,
        "total_price_per_month": int(total_price),
        "average_calories_per_month": int(total_cal // meal_count)
        if meal_count > 0
        else 0,
        "days": days_list,
    }


# ----------------------- 일일 식단 상세 정보 조회 API ---------------------------------
@router.get("/{date}", response_model=DailyMealDetailResponse)
async def get_daily_meal_detail(
    date: date,  # YYYY-MM-DD 형식의 경로 파라미터
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    [화면 10] 일일 식단 상세 정보를 조회합니다.
    """
    # 1. 해당 유저와 날짜에 맞는 식단 조회
    plan = (
        db.query(MealPlan)
        .filter(MealPlan.user_id == current_user.id, MealPlan.meal_date == date)
        .first()
    )

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{date}에 해당하는 식단 데이터가 없습니다.",
        )
    
    # 병렬 처리를 위해 이미지 태스크 목록을 빌드
    img_tasks = []
    for item in plan.content:
        selected_menu = item.get("selected_menu") or {}
        menu_name = selected_menu.get("name", "")
        img_tasks.append(get_food_image_url(menu_name, "food"))

    # 아침, 점심, 저녁 이미지 매핑 파이프라인을 한방에 병렬 실행
    all_img_urls = await asyncio.gather(*img_tasks)

    # 결과를 매핑하여 최종 응답 스키마 조립
    detail_meals = []
    for item, img_url in zip(plan.content, all_img_urls):
        selected_menu = item.get("selected_menu") or {}
        detail_meals.append(
            {
                "slot": item.get("meal_order"),
                "meal_id": str(selected_menu.get("menu_id")),
                "menu_name": selected_menu.get("name"),
                "calories": int(selected_menu.get("calories") or 0),
                "price": int(selected_menu.get("estimated_cost") or 0),
                "image_url": img_url,
            }
        )

    # 3. 명세서 규격에 맞춘 결과 반환
    return {
        "date": plan.meal_date,
        "calories_per_day": int(plan.total_calories or 0),
        "price_per_day": int(plan.estimated_cost or 0),
        "meals": detail_meals,
    }


# -------------------------- 식단 상세 레시피, 재료, 마켓 정보 조회 API -------------------------
@router.get("/menu/{meal_date}/{menu_id}")
async def get_menu_detail(
    meal_date: date,
    menu_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 일자의 메뉴 상세 정보(재료, 가격, 마켓 정보 등)를 조회하여 프론트엔드 규격에 맞게 반환합니다.
    """
    # 1. DB에서 해당 날짜의 식단 데이터 조회
    meal_plan = (
        db.query(MealPlan)
        .filter(MealPlan.user_id == current_user.id, MealPlan.meal_date == meal_date)
        .first()
    )

    if not meal_plan or not meal_plan.content:
        raise HTTPException(status_code=404, detail="해당 날짜의 식단 정보가 없습니다.")

    # 2. JSON 데이터(content) 안에서 요청받은 menu_id와 일치하는 메뉴 찾기
    target_menu = None
    for meal in meal_plan.content:
        selected = meal.get("selected_menu", {})
        if selected.get("menu_id") == menu_id:
            target_menu = selected
            break

    if not target_menu:
        raise HTTPException(status_code=404, detail="해당 메뉴를 찾을 수 없습니다.")

    # 3. 프론트엔드 명세에 맞게 데이터 가공 준비
    ingredients_data = []
    required_ingredient_ids = []

    # 우리가 관리할 3대 이커머스 마켓 키
    supported_markets = ["coupang", "market_kurly", "naver_shopping"]

    # 4. 재료 데이터 변환 (AI 데이터의 ingredient_costs 리스트 활용)
    ing_costs = target_menu.get("ingredient_costs", [])
    for ing_cost in target_menu.get("ingredient_costs", []):
        print(f"[ING] {ing_cost.get('ingredient_name')}: {ing_cost}")
        ing_id = ing_cost.get("ingredient_id")
        required_ingredient_ids.append(ing_id)

        has_price = ing_cost.get("pricing_status") == "calculated"
        mock_price = ing_cost.get("lowest_price") if has_price else None
        mock_market = ing_cost.get("lowest_market") if has_price else None

        # 일단 모든 마켓을 null로 초기화
        e_commerce_prices = {m: {"lowest_price": None} for m in supported_markets}

        # 가격 있는 경우에만 해당 마켓 채우기
        if has_price and mock_market in supported_markets:
            e_commerce_prices[mock_market] = {"lowest_price": mock_price}

        # 개별 재료 정보 조립 (lowest_price_between_market도 None 가능)
        ingredients_data.append(
            {
                "ingredient_id": ing_id,
                "ingredient_name": ing_cost.get("ingredient_name"),
                "standard_unit": ing_cost.get("display_amount"),
                "image_url": None,
                "lowest_price_between_market": {
                    "market": mock_market,  # None 가능
                    "price": mock_price,  # None 가능
                },
                "e_commerce_prices": e_commerce_prices,
            }
        )

    menu_name = target_menu.get("name", "")
    img_tasks = [
        get_food_image_url(menu_name, "food"),  # 메뉴 자체 이미지 (인덱스 0)
        *[
            get_food_image_url(ic.get("ingredient_name"), "food") for ic in ing_costs
        ],  # 재료 이미지들
    ]
    all_img_urls = await asyncio.gather(*img_tasks)
    menu_img_url = all_img_urls[0]
    ingredient_img_urls = all_img_urls[1:]

    # 4-3. 재료 결과 매핑
    for ingredient, url in zip(ingredients_data, ingredient_img_urls):
        ingredient["image_url"] = url

    # 5. 최종 응답 JSON 조립
    response_data = {
        "meal_id": str(target_menu.get("menu_id")),
        "menu_name": target_menu.get("name"),
        "calories": int(target_menu.get("calories") or 0),
        "price": int(target_menu.get("estimated_cost") or 0),  # 메뉴 전체 예상 비용
        "image_url": menu_img_url,
        "video_url": None,
        "required_ingredient_ids": required_ingredient_ids,
        "ingredients": ingredients_data,
    }

    return response_data


# -------------------------- 식단 swap API -----------------------------------
@router.patch("/{date}/swap", response_model=MealSwapResponse)
async def swap_meal_plans(
    date: date,
    request: MealSwapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    내용물(JSON)은 그대로 두고, 두 식단의 날짜(meal_date) 라벨만 서로 교환합니다.
    """
    from datetime import date as dt_date

    date1 = date
    date2 = request.with_date

    if date1 == date2:
        raise HTTPException(status_code=400, detail="동일한 날짜는 스왑할 수 없습니다.")

    # 1. 두 날짜 데이터 레코드 자체를 가져옴
    plan1 = (
        db.query(MealPlan)
        .filter(MealPlan.user_id == current_user.id, MealPlan.meal_date == date1)
        .first()
    )
    plan2 = (
        db.query(MealPlan)
        .filter(MealPlan.user_id == current_user.id, MealPlan.meal_date == date2)
        .first()
    )

    if not plan1 and not plan2:
        raise HTTPException(status_code=404, detail="스왑할 데이터가 없습니다.")

    # 2. 날짜(Date) 라벨만 교환 (temp 변수 활용)
    try:
        # DB Unique 제약 조건 충돌을 막기 위해 plan1을 아주 먼 임시 날짜로 잠깐 대피
        temp_date = dt_date(9999, 12, 31)

        if plan1:
            plan1.meal_date = temp_date
        db.flush()  # DB에 임시 반영 (commit 전 상태)

        if plan2:
            plan2.meal_date = date1
        db.flush()

        if plan1:
            plan1.meal_date = date2

        db.commit()  # 최종 확정!

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"스왑 실패: {str(e)}")

    # 3. 명세서에 맞춘 응답 구성
    def format_day(d, p):
        formatted_meals = []
        if p and p.content:
            for m in p.content:
                selected = m.get("selected_menu") or {}
                m_id = selected.get("menu_id")

                formatted_meals.append(
                    {
                        "slot": m.get("meal_order") or 1,
                        "meal_id": str(m_id) if m_id is not None else "",
                        "menu_name": selected.get("name") or "메뉴 정보 없음",
                    }
                )

        return {
            "date": d,
            "calories_per_day": int(p.total_calories or 0) if p else None,
            "price_per_day": int(p.estimated_cost or 0) if p else None,
            "meals": formatted_meals,
        }

    # 주의: plan1은 이제 date2를, plan2는 date1을 가리키고 있습니다.
    return {
        "swapped": [
            format_day(date1, plan2),  # 날짜1에는 원래 날짜2의 데이터(plan2)를 매핑
            format_day(date2, plan1),  # 날짜2에는 원래 날짜1의 데이터(plan1)를 매핑
        ]
    }


# ------------------------ 특정 날짜의 특정 메뉴 변경 API ----------------------------
@router.put("/{date}/menus/{slot}", response_model=DailyMealDetailResponse)
async def update_specific_menu_slot(
    date: date,
    slot: int,
    request: MenuUpdateRequest,  # 프론트에서 { "new_menu_id": "M_101" } 형태로 보낸다고 가정
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    [화면 10-3] 특정 날짜의 특정 슬롯 메뉴를 사용자가 선택한 대안 메뉴로 변경합니다.
    """
    # 1. 기존 식단 조회
    plan = (
        db.query(MealPlan)
        .filter(MealPlan.user_id == current_user.id, MealPlan.meal_date == date)
        .first()
    )

    if not plan:
        raise HTTPException(
            status_code=404, detail="해당 날짜의 식단이 존재하지 않습니다."
        )

    # 2. content 내에서 대상 슬롯(slot) 찾기
    target_index = -1
    for i, m in enumerate(plan.content):
        if m.get("meal_order") == slot:
            target_index = i
            break

    if target_index == -1:
        raise HTTPException(status_code=400, detail="유효하지 않은 슬롯 번호입니다.")

    # 3. 대안 메뉴 리스트에서 사용자가 선택한 메뉴 찾기
    # 같은 meal_id가 여러 슬롯에 존재할 수 있으므로 플랜 전체에서 검색
    current_slot_data = plan.content[target_index]
    alt_menus = current_slot_data.get("alternative_menus", [])

    new_menu_data = None
    for alt in alt_menus:
        if str(alt.get("menu_id")) == str(request.new_menu_id):
            new_menu_data = alt
            break
    
    if not new_menu_data:
        for meal_slot in plan.content:
            for alt in meal_slot.get("alternative_menus", []):
                if str(alt.get("menu_id")) == str(request.new_menu_id):
                    new_menu_data = alt
                    break
            if new_menu_data:
                break

    if not new_menu_data:
        raise HTTPException(
            status_code=400, detail="선택한 메뉴가 대안 리스트에 존재하지 않습니다."
        )

    # 4. 데이터 교체 및 통계 갱신
    try:
        # 기존 메뉴 백업 (selected_menu 구조 확인 필요)
        old_selected = current_slot_data.get("selected_menu", {})

        # 새로운 메뉴 데이터 구조 구성 (AI 명세 규격에 맞춤)
        # 선택된 메뉴를 selected_menu로 올리고, 대안 리스트는 유지하거나 갱신
        updated_slot_content = {
            "meal_order": slot,
            "selected_menu": new_menu_data,
            "alternative_menus": alt_menus,  # 필요 시 대안 리스트 유지
        }

        # 통계 갱신 (차이만큼 가감)
        plan.total_calories += new_menu_data.get("calories", 0) - old_selected.get(
            "calories", 0
        )
        plan.estimated_cost += new_menu_data.get(
            "estimated_cost", 0
        ) - old_selected.get("estimated_cost", 0)

        # 교체 실행
        plan.content[target_index] = updated_slot_content

        # JSON 변경 명시
        flag_modified(plan, "content")
        db.commit()
        db.refresh(plan)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"메뉴 업데이트 중 오류 발생: {str(e)}"
        )

    # 5. 최종 응답 구성 (이미지 포함)
    img_tasks = []
    for item in plan.content:
        menu = item.get("selected_menu", {})
        menu_name = menu.get("name", "")
        # Task를 리스트에 담기만 하고 아직 실행(await)하지 않음
        img_tasks.append(get_food_image_url(menu_name, "food"))

    # 모아둔 Task를 한꺼번에 병렬로 실행! (시간 단축 핵심)
    all_img_urls = await asyncio.gather(*img_tasks)

    detail_meals = []
    for item, img_url in zip(plan.content, all_img_urls):
        menu = item.get("selected_menu", {})
        detail_meals.append(
            {
                "slot": item.get("meal_order"),
                "meal_id": str(menu.get("menu_id")),
                "menu_name": menu.get("name", ""),  # menu_name 변수 말고 menu에서 직접
                "calories": int(menu.get("calories") or 0),
                "price": int(menu.get("estimated_cost") or 0),
                "image_url": img_url,
            }
        )

    return {
        "date": plan.meal_date,
        "calories_per_day": int(plan.total_calories or 0),
        "price_per_day": int(plan.estimated_cost or 0),
        "meals": detail_meals,
    }


# ----------------------------- 메뉴 변경용 추천 대안 조회 API ------------------------------
@router.get("/menus/{meal_id}/alternatives", response_model=AlternativeMenuResponse)
async def get_meal_alternatives(
    meal_id: str,
    target_date: str = Query(
        None, description="YYYY-MM-DD 형식 (정확한 식단 검색을 위해 권장)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    [화면 10-3] 메뉴 변경용 추천 대안 조회 API
    DB에 저장된 월간 식단 원본 데이터에서 현재 메뉴 정보와 대안 메뉴(alternatives)를 추출하여 반환합니다.
    """

    query = db.query(MealPlan).filter(MealPlan.user_id == current_user.id)

    if target_date:
        query = query.filter(MealPlan.meal_date == target_date)
    else:
        query = query.filter(MealPlan.meal_date >= date.today())

    meal_plans = query.order_by(MealPlan.meal_date.asc()).all()

    target_meal_data = None
    target_meal_date = None

    # 2. JSON 데이터(content 리스트)를 순회하며 해당 메뉴(meal_id) 찾기
    for plan in meal_plans:
        if not plan.content:
            continue

        for meal in plan.content:
            selected_menu = meal.get("selected_menu", {})
            if selected_menu.get("menu_id") == meal_id:
                target_meal_data = meal
                target_meal_date = plan.meal_date  # 날짜 객체
                break

        if target_meal_data:
            break

    if not target_meal_data:
        raise HTTPException(
            status_code=404, detail="해당 메뉴가 포함된 식단 기록을 찾을 수 없습니다."
        )

    selected_menu = target_meal_data.get("selected_menu", {})
    alt_menus = target_meal_data.get("alternative_menus", [])

    current_menu_name = selected_menu.get("name", "")

    # 인덱스 0번은 항상 Current Meal의 이미지가 되도록 세팅
    img_tasks = [get_food_image_url(current_menu_name, "food")]

    # Alternatives 이미지 작업 추가
    for alt in alt_menus:
        img_tasks.append(
            get_food_image_url(alt.get("name", ""), alt.get("category", ""))
        )

    # 모아둔 작업 병렬 실행
    all_img_urls = await asyncio.gather(*img_tasks)

    # 결과 분리
    current_img_url = all_img_urls[0]
    alt_img_urls = all_img_urls[1:]

    # 3. 명세서 기반 Current Meal 가공 (데이터 매핑)
    # AI의 필드명(estimated_cost 등)을 프론트 명세(price 등)로 변환
    current_meal = {
        "meal_id": selected_menu.get("menu_id", meal_id),
        "menu_name": selected_menu.get("name", ""),
        "calories": int(selected_menu.get("calories") or 0),
        "price": int(selected_menu.get("estimated_cost") or 0),
        "image_url": current_img_url,  # 병렬 결과 매핑
        "date": target_meal_date.strftime("%Y-%m-%d")
        if target_meal_date
        else "",  # 문자열로 변환
        "slot": target_meal_data.get("meal_order", 1),
    }

    # 4. 명세서 기반 Alternatives 가공
    alternatives = []
    for alt, url in zip(alt_menus, alt_img_urls):
        alternatives.append(
            {
                "meal_id": alt.get("menu_id", ""),
                "menu_name": alt.get("name", ""),
                "calories": int(alt.get("calories") or 0),
                "price": int(alt.get("estimated_cost") or 0),
                "image_url": url,  # 병렬 결과 매핑
            }
        )

    # 5. 최종 반환 (Pydantic 스키마가 자동으로 JSON 변환 및 검증을 수행합니다)
    return {"current_meal": current_meal, "alternatives": alternatives}


# ------------------------------- AI 모델 서버 호출용 API ----------------------------------


def get_modeling_user_id(current_user: User) -> str:
    """
    DB user id를 모델링에서 사용하는 user_id 형식으로 변환합니다.

    예:
    current_user.id == 4 -> user_004
    """

    return f"user_{current_user.id:03d}"


def build_modeling_profile_from_user(
    current_user: User,
    sample_period_days: int | None = None,
    period_days: int | None = None,
) -> dict:
    """
    DB의 User 정보를 모델링 profile 형식으로 변환합니다.
    """

    persona = current_user.persona_setting
    taste = current_user.onboarding_setting
    
    profile = {
        "goals": (persona.purpose if persona else []) or [], 
        "monthly_budget": persona.monthly_budget if persona else 300000,
        "meal_count_per_day": persona.meals_per_day if persona else 3,

        # 2. UserOnboardingSetting (2단계 온보딩 취향 설정 테이블)에서 추출
        "cooking_skill": taste.cooking_skill if taste else 3,
        "preferred_categories": (taste.preferred_categories if taste else []) or [],
        "diversity_level": taste.diversity_level if taste else "보통",
        "ingredient_preferences": (taste.preferred_ingredients if taste else []) or [],
        "allergy_ingredients": (taste.excluded_ingredients if taste else []) or [],
    }

    if sample_period_days is not None:
        profile["sample_period_days"] = sample_period_days

    if period_days is not None:
        profile["period_days"] = period_days

    return profile


def build_selected_style_from_style_id(style_id: str) -> dict:
    """
    프론트에서 전달받은 selected_style_id를
    모델링이 사용하는 selected_style 객체로 변환합니다.

    모델링 월간 식단 생성 함수는 selected_style_id가 아니라
    source_goal, focus_key 등이 포함된 selected_style 객체를 필요로 합니다.
    """

    style_map = {
        "budget_first": {
            "style_id": "budget_first",
            "style_name": "가성비 최우선",
            "description": "예산을 가장 우선으로 고려한 식단",
            "summary_comment": "예산 부담을 줄이고 간편하게 구성한 식단입니다.",
            "source_goal": "식비 절약",
            "focus_key": "budget",
            "display_scores": {
                "health": 7,
                "cost_efficiency": 10,
                "taste": 6,
                "cooking_ease": 7,
            },
            "display_labels": {
                "health": "건강",
                "cost_efficiency": "가성비",
                "taste": "맛",
                "cooking_ease": "조리",
            },
        },
        "nutrition_balance": {
            "style_id": "nutrition_balance",
            "style_name": "영양 균형식",
            "description": "칼로리와 단백질 균형을 함께 고려한 식단",
            "summary_comment": "영양 균형을 고려해 건강하게 구성한 식단입니다.",
            "source_goal": "영양 균형",
            "focus_key": "nutrition",
            "display_scores": {
                "health": 9,
                "cost_efficiency": 7,
                "taste": 7,
                "cooking_ease": 7,
            },
            "display_labels": {
                "health": "건강",
                "cost_efficiency": "가성비",
                "taste": "맛",
                "cooking_ease": "조리",
            },
        },
        "diet_light": {
            "style_id": "diet_light",
            "style_name": "가벼운 관리식",
            "description": "칼로리 부담을 줄이고 가볍게 구성한 식단",
            "summary_comment": "부담이 적은 메뉴를 중심으로 구성한 식단입니다.",
            "source_goal": "다이어트",
            "focus_key": "nutrition",
            "display_scores": {
                "health": 9,
                "cost_efficiency": 7,
                "taste": 7,
                "cooking_ease": 7,
            },
            "display_labels": {
                "health": "건강",
                "cost_efficiency": "가성비",
                "taste": "맛",
                "cooking_ease": "조리",
            },
        },
        "high_protein": {
            "style_id": "high_protein",
            "style_name": "고단백 관리식",
            "description": "단백질 섭취를 우선으로 고려한 식단",
            "summary_comment": "단백질 섭취를 늘리고 싶은 사용자에게 적합한 식단입니다.",
            "source_goal": "고단백",
            "focus_key": "nutrition",
            "display_scores": {
                "health": 9,
                "cost_efficiency": 10,
                "taste": 7,
                "cooking_ease": 7,
            },
            "display_labels": {
                "health": "건강",
                "cost_efficiency": "가성비",
                "taste": "맛",
                "cooking_ease": "조리",
            },
        },
        "easy_cooking": {
            "style_id": "easy_cooking",
            "style_name": "간편 조리식",
            "description": "조리 난이도와 시간을 낮게 유지한 식단",
            "summary_comment": "조리 부담을 줄이고 빠르게 준비할 수 있는 식단입니다.",
            "source_goal": "간편식",
            "focus_key": "difficulty",
            "display_scores": {
                "health": 7,
                "cost_efficiency": 10,
                "taste": 6,
                "cooking_ease": 8,
            },
            "display_labels": {
                "health": "건강",
                "cost_efficiency": "가성비",
                "taste": "맛",
                "cooking_ease": "조리",
            },
        },
        "taste_first": {
            "style_id": "taste_first",
            "style_name": "취향 맞춤식",
            "description": "선호 카테고리와 재료 취향을 더 많이 반영한 식단",
            "summary_comment": "사용자의 취향과 선호 재료를 중심으로 구성한 식단입니다.",
            "source_goal": "맛 중심",
            "focus_key": "preference",
            "display_scores": {
                "health": 7,
                "cost_efficiency": 7,
                "taste": 9,
                "cooking_ease": 7,
            },
            "display_labels": {
                "health": "건강",
                "cost_efficiency": "가성비",
                "taste": "맛",
                "cooking_ease": "조리",
            },
        },
    }

    selected_style = style_map.get(style_id)

    if selected_style is None:
        raise ValueError(f"지원하지 않는 selected_style_id입니다: {style_id}")

    return selected_style


# ---------------- 3일치 식단 샘플 생성 요청 API ----------------------
@router.post("/generate_sample_3days")
async def generate_initial_meal_plan(
    sample_period_days: int = 3,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    사용자의 온보딩 정보를 기반으로 모델링 파트에 3일치 샘플 식단 생성을 요청합니다.

    user_id는 프론트에서 받지 않고,
    백엔드의 current_user.id를 기준으로 생성합니다.
    """

    # 분리된 연관 테이블 데이터를 joinedload로 한방에 가져옵니다.
    full_user = db.query(User).options(
        joinedload(User.family_members),
        joinedload(User.persona_setting),
        joinedload(User.onboarding_setting)
    ).filter(User.id == current_user.id).first()

    ai_payload = {
        "user_id": get_modeling_user_id(current_user),
        "request_type": "meal_style_candidates",
        "profile": build_modeling_profile_from_user(
            current_user=full_user,
            sample_period_days=sample_period_days,
        ),
    }

    try:
        ai_response = await asyncio.to_thread(
            create_meal_style_candidates,
            ai_payload,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )

    frontend_candidates = []

    for candidate in ai_response.get("meal_style_candidates", []):
        # 첫째 날의 메뉴 3개를 뽑아서 대표 메뉴로 사용
        # 1. 먼저 days 리스트를 안전하게 가져옵니다.
        days_list = candidate.get("sample_plan", {}).get("days", [])

        # 2. days 리스트에 데이터가 존재할 때만 첫 번째 날의 meals를 가져옵니다.
        first_day_meals = days_list[0].get("meals", []) if days_list else []
        representative_menus = [meal.get("name") for meal in first_day_meals[:3]]

        frontend_candidates.append(
            {
                "style_id": candidate.get(
                    "style_id"
                ),  # 나중에 유저가 선택했을 때 백엔드로 다시 보낼 식별자
                "style_name": candidate.get("style_name"),  # 예: "가성비 최우선"
                "description": candidate.get(
                    "description"
                ),  # "단백질 섭취를 우선으로 고려한 식단" 등 상세 설명
                "summary_comment": candidate.get(
                    "summary_comment"
                ),  # 예: "단백질 섭취를 늘리고 싶은..."
                "display_labels": candidate.get(
                    "display_labels"
                ),  # 점수 라벨 (건강, 가성비 등)
                "display_scores": candidate.get(
                    "display_scores"
                ),  # 실제 점수 데이터 (그래프용)
                "representative_menus": representative_menus,  # 예: ["새우 두부 계란찜", "닭가슴살 브로콜리 만두", "부추 콩가루 찜"]
            }
        )

    return {
        "message": "3일치 식단 스타일 후보 생성이 완료되었습니다.",
        "candidates": frontend_candidates,
    }


# --------------------------- 모델링 연동 API ---------------------------


@router.post("/modeling/style-candidates")
async def create_modeling_style_candidates(
    request_data: dict,
):
    """
    Back → Modeling 3일치 식단 스타일 후보 생성 테스트 API.

    이 API는 Swagger 또는 curl에서 모델링 응답 구조를 직접 확인하기 위한 개발용 API입니다.
    request body에 들어온 user_id, request_type, profile을 그대로 사용합니다.
    """

    try:
        return await asyncio.to_thread(
            create_meal_style_candidates,
            request_data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )


@router.post("/modeling/monthly-plan")
async def create_modeling_monthly_plan(
    request_data: dict,
):
    """
    Back → Modeling 월간 식단 생성 테스트 API.

    이 API는 Swagger 또는 curl에서 모델링 월간 식단 응답 구조를 직접 확인하기 위한 개발용 API입니다.
    request body에 들어온 user_id, request_type, profile, selected_style을 그대로 사용합니다.
    """

    try:
        return await asyncio.to_thread(
            create_monthly_plan,
            request_data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )