from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from datetime import date, datetime
import uuid
import calendar

from app.api.deps import get_db, get_current_user
from app.utils.meal_transformer import transform_ai_plan_to_front
from app.utils.mock_data import get_mock_3days_response, get_mock_month_data_response, get_mock_3days_data_front_response
from app.core.constants import MEAL_STYLES_META
from app.models.user import User
from app.crud.crud_user import update_user_selected_style
from app.models.meal import MealPlan
from app.schemas.meal import (DailyMealDetailResponse, MealGenerateResponse, MealConfirmResponse, CalendarResponse,
                              MealSwapResponse, MealSwapRequest, MenuUpdateRequest, AlternativeMenuResponse,
                              StyleSelectRequest, MealDetailFullResponse)
from app.crud import crud_meal
from app.utils.image_search import get_food_image_url
from app.utils.ai_client import request_ai_meal_plan

router = APIRouter()

# ---------------------------  프론트엔드 호출용 API ---------------------------------
# ---------- 3일치 샘플 식단 후보 제공 (Front에 보여주기 용) -----------------------
@router.post("/sample_data_three_days")
async def initial_meal_plan(
    style_id: StyleSelectRequest,
    sample_period_days: int = 3,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사용자 온보딩 데이터를 기반으로 3일치 샘플 식단 후보 3가지를 생성합니다.
    (현재는 AI 연동 전이므로 모델링 파트의 JSON 규격을 그대로 Mock으로 반환합니다.)
    """
    user_id = f"user_{current_user.id:03d}"

    style_info = MEAL_STYLES_META.get(style_id)

    # 모델링 파트에서 전달받은 JSON 구조를 그대로 Mock 데이터로 사용 (프론트 연동용)
    mock_ai_response = get_mock_3days_data_front_response(user_id, sample_period_days)
    
    # 프론트엔드가 이 데이터를 바로 쓸 수 있도록 AI 응답 결과 자체를 리턴합니다.
    return {
        "style_meta": style_info,  # 화면 상단의 타이틀, 설명 문구용
        "plan_data": mock_ai_response  # 화면 하단의 달력/리스트용
    }

# ---------------------- 식단 생성 트리거 ---------------------------------
@router.post("/generate", response_model=MealGenerateResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_meal_plans_trigger(
    current_user: User = Depends(get_current_user)
):
    """
    [화면 6] 프로필 기반 식단 생성 트리거
    JSON 초안에 맞춰 job_id와 진행 단계 정보를 반환합니다.
    """
    
    # 1. 고유 작업 ID 생성
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    
    # 2. 실제 구현 시: Celery나 FastAPI BackgroundTasks를 사용하여 
    # 비동기로 crud_meal.save_recommendation_result를 실행해야 합니다.
    # 지금은 흐름을 맞추기 위해 즉시 작업 정보를 반환합니다.
    
    return {
        "job_id": job_id,
        "estimated_seconds": 10,
        "stages": ["프로필 분석", "식단 후보 생성", "가격 비교", "최적 조합 선정"]
    }

# --------------------- 생성된 30일 식단 최종 확정 및 요약 정보 반환 API -----------------------
@router.post("/confirm", response_model=MealConfirmResponse)
def confirm_meal_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [화면 9] 생성된 30일 식단을 최종 확정하고 요약 정보를 반환합니다.
    """
    # 1. 해당 유저의 가장 최근 생성된(혹은 임시 상태인) 식단 리스트 조회
    # (실제 서비스에서는 is_confirmed 등의 상태 값을 활용할 수 있습니다)
    plans = db.query(MealPlan).filter(
        MealPlan.user_id == current_user.id
    ).order_by(MealPlan.meal_date.asc()).all()

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
        "generated_at": datetime.now() # 혹은 DB의 생성일시 컬럼 사용
    }

# -------------------- 월간 캘린더 조회 API ----------------------------
@router.get("/calendar", response_model=CalendarResponse)
def get_monthly_calendar(
    month: str, # "2026-04" 형식
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    plans = db.query(MealPlan).filter(
        MealPlan.user_id == current_user.id,
        MealPlan.meal_date >= start_date,
        MealPlan.meal_date <= end_date
    ).all()
    
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
            for meal in (plan.content or []):
                # Mock 데이터 구조에 맞춰 selected_menu 내부를 탐색
                selected_menu = meal.get("selected_menu") or {}
                
                # 데이터가 None이거나 키가 없을 때를 대비한 방어 로직
                raw_menu_id = selected_menu.get("menu_id")
                raw_name = selected_menu.get("name")

                extracted_meals.append({
                    "slot": meal.get("meal_order") or 1,
                    "meal_id": str(raw_menu_id) if raw_menu_id is not None else "",
                    "menu_name": raw_name or "메뉴 정보 없음"
                })

            # 식단이 있는 날
            day_data = {
                "date": curr_date,
                "calories_per_day": plan.total_calories,
                "price_per_day": plan.estimated_cost,
                "meals": extracted_meals
            }
            total_price += plan.estimated_cost
            total_cal += plan.total_calories
            meal_count += 1
        else:
            # 식단이 없는 날 (명세서 규격 준수)
            day_data = {
                "date": curr_date,
                "calories_per_day": None,
                "price_per_day": None,
                "meals": []
            }
        days_list.append(day_data)

    return {
        "month": month,
        "duration_days": meal_count,
        "total_price_per_month": total_price,
        "average_calories_per_month": total_cal // meal_count if meal_count > 0 else 0,
        "days": days_list
    }

# ----------------------- 일일 식단 상세 정보 조회 API ---------------------------------
@router.get("/{date}", response_model=DailyMealDetailResponse)
async def get_daily_meal_detail(
    date: date, # YYYY-MM-DD 형식의 경로 파라미터
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [화면 10] 일일 식단 상세 정보를 조회합니다.
    """
    # 1. 해당 유저와 날짜에 맞는 식단 조회
    plan = db.query(MealPlan).filter(
        MealPlan.user_id == current_user.id,
        MealPlan.meal_date == date
    ).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"{date}에 해당하는 식단 데이터가 없습니다."
        )

    # 2. DB의 content(JSON) 데이터 정제 및 타입 변환
    detail_meals = []
    for item in plan.content:
        selected_menu = item.get("selected_menu") or {}
        menu_name = selected_menu.get("name")
        category = selected_menu.get("category")
        img_url = await get_food_image_url(menu_name, category)

        detail_meals.append({
            "slot": item.get("meal_order"),
            "meal_id": str(selected_menu.get("menu_id")),
            "menu_name": menu_name,
            "calories": selected_menu.get("calories", 0),
            "price": selected_menu.get("estimated_cost", 0),
            "image_url": img_url # Pixabay API를 호출하여 이미지를 가져옴
        })

    # 3. 명세서 규격에 맞춘 결과 반환
    return {
        "date": plan.meal_date,
        "calories_per_day": plan.total_calories,
        "price_per_day": plan.estimated_cost,
        "meals": detail_meals
    }

# -------------------------- 식단 상세 레시피, 재료, 마켓 정보 조회 API -------------------------
@router.get("/menu/{meal_date}/{menu_id}")
async def get_menu_detail(
    meal_date: date, 
    menu_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 일자의 메뉴 상세 정보(재료, 가격, 마켓 정보 등)를 조회하여 프론트엔드 규격에 맞게 반환합니다.
    """
    # 1. DB에서 해당 날짜의 식단 데이터 조회
    meal_plan = db.query(MealPlan).filter(
        MealPlan.user_id == current_user.id, 
        MealPlan.meal_date == meal_date
    ).first()

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
    for ing_cost in target_menu.get("ingredient_costs", []):
        ing_id = ing_cost.get("ingredient_id")
        required_ingredient_ids.append(ing_id)
        
        # 모델링 데이터에서 제공한 최저가 및 마켓 정보
        mock_price = ing_cost.get("lowest_price", 0)
        mock_market = ing_cost.get("lowest_market", "coupang") # 기본값 fallback
        
        # e_commerce_prices 조립 (요청하신 100,000원 처리 로직)
        e_commerce_prices = {}
        for market in supported_markets:
            if market == mock_market:
                e_commerce_prices[market] = {"lowest_price": mock_price}
            else:
                # 데이터가 없는 마켓은 임시로 100,000원 처리
                e_commerce_prices[market] = {"lowest_price": 100000}
        
        img_url = await get_food_image_url(ing_cost.get("ingredient_name"), "재료")
                
        # 개별 재료 정보 조립
        ingredients_data.append({
            "ingredient_id": ing_id,
            "ingredient_name": ing_cost.get("ingredient_name"),
            "standard_unit": ing_cost.get("display_amount"), # 예: "122g", "1공기"
            "image_url": img_url,
            "lowest_price_between_market": {
                "market": mock_market,
                "price": mock_price
            },
            "e_commerce_prices": e_commerce_prices
        })

    # 5. 최종 응답 JSON 조립
    response_data = {
        "meal_id": target_menu.get("menu_id"),
        "menu_name": target_menu.get("name"),
        "calories": target_menu.get("calories"),
        "price": target_menu.get("estimated_cost"), # 메뉴 전체 예상 비용
        "image_url": img_url,
        "video_url": None,
        "required_ingredient_ids": required_ingredient_ids,
        "ingredients": ingredients_data
    }

    return response_data

# -------------------------- 식단 swap API -----------------------------------
@router.patch("/{date}/swap", response_model=MealSwapResponse)
def swap_meal_plans(
    date: date,
    request: MealSwapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    plan1 = db.query(MealPlan).filter(MealPlan.user_id == current_user.id, MealPlan.meal_date == date1).first()
    plan2 = db.query(MealPlan).filter(MealPlan.user_id == current_user.id, MealPlan.meal_date == date2).first()

    if not plan1 and not plan2:
        raise HTTPException(status_code=404, detail="스왑할 데이터가 없습니다.")

    # 2. 날짜(Date) 라벨만 교환 (temp 변수 활용)
    try:
        # DB Unique 제약 조건 충돌을 막기 위해 plan1을 아주 먼 임시 날짜로 잠깐 대피
        temp_date = dt_date(9999, 12, 31) 

        if plan1:
            plan1.meal_date = temp_date
        db.flush() # DB에 임시 반영 (commit 전 상태)

        if plan2:
            plan2.meal_date = date1
        db.flush()

        if plan1:
            plan1.meal_date = date2
            
        db.commit() # 최종 확정!
        
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
                
                formatted_meals.append({
                    "slot": m.get("meal_order") or 1,
                    "meal_id": str(m_id) if m_id is not None else "",
                    "menu_name": selected.get("name") or "메뉴 정보 없음"
                })

        return {
            "date": d,
            "calories_per_day": p.total_calories if p else None,
            "price_per_day": p.estimated_cost if p else None,
            "meals": formatted_meals
        }

    # 주의: plan1은 이제 date2를, plan2는 date1을 가리키고 있습니다.
    return {
        "swapped": [
            format_day(date1, plan2), # 날짜1에는 원래 날짜2의 데이터(plan2)를 매핑
            format_day(date2, plan1)  # 날짜2에는 원래 날짜1의 데이터(plan1)를 매핑
        ]
    }

# ------------------------ 특정 날짜의 특정 메뉴 변경 API ----------------------------
@router.put("/{date}/menus/{slot}", response_model=DailyMealDetailResponse)
async def update_specific_menu_slot(
    date: date,
    slot: int,
    request: MenuUpdateRequest, # 프론트에서 { "new_menu_id": "M_101" } 형태로 보낸다고 가정
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [화면 10-3] 특정 날짜의 특정 슬롯 메뉴를 사용자가 선택한 대안 메뉴로 변경합니다.
    """
    # 1. 기존 식단 조회
    plan = db.query(MealPlan).filter(
        MealPlan.user_id == current_user.id,
        MealPlan.meal_date == date
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="해당 날짜의 식단이 존재하지 않습니다.")

    # 2. content 내에서 대상 슬롯(slot) 찾기
    target_index = -1
    for i, m in enumerate(plan.content):
        if m.get("meal_order") == slot:
            target_index = i
            break

    if target_index == -1:
        raise HTTPException(status_code=400, detail="유효하지 않은 슬롯 번호입니다.")

    # 3. 대안 메뉴 리스트에서 사용자가 선택한 메뉴 찾기
    current_slot_data = plan.content[target_index]
    alt_menus = current_slot_data.get("alternative_menus", [])
    
    new_menu_data = None
    for alt in alt_menus:
        if str(alt.get("menu_id")) == str(request.new_menu_id):
            new_menu_data = alt
            break

    if not new_menu_data:
        raise HTTPException(status_code=400, detail="선택한 메뉴가 대안 리스트에 존재하지 않습니다.")

    # 4. 데이터 교체 및 통계 갱신
    try:
        # 기존 메뉴 백업 (selected_menu 구조 확인 필요)
        old_selected = current_slot_data.get("selected_menu", {})
        
        # 새로운 메뉴 데이터 구조 구성 (AI 명세 규격에 맞춤)
        # 선택된 메뉴를 selected_menu로 올리고, 대안 리스트는 유지하거나 갱신
        updated_slot_content = {
            "meal_order": slot,
            "selected_menu": new_menu_data,
            "alternative_menus": alt_menus # 필요 시 대안 리스트 유지
        }

        # 통계 갱신 (차이만큼 가감)
        plan.total_calories += (new_menu_data.get("calories", 0) - old_selected.get("calories", 0))
        plan.estimated_cost += (new_menu_data.get("estimated_cost", 0) - old_selected.get("estimated_cost", 0))
        
        # 교체 실행
        plan.content[target_index] = updated_slot_content
        
        # JSON 변경 명시
        flag_modified(plan, "content")
        db.commit()
        db.refresh(plan)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"메뉴 업데이트 중 오류 발생: {str(e)}")

    # 5. 최종 응답 구성 (이미지 포함)
    detail_meals = []
    for item in plan.content:
        menu = item.get("selected_menu", {})
        menu_name = menu.get("name", "")
        menu_category = menu.get("category", "")
        
        img_url = await get_food_image_url(menu_name, menu_category)
        
        detail_meals.append({
            "slot": item.get("meal_order"),
            "meal_id": str(menu.get("menu_id")),
            "menu_name": menu_name,
            "calories": menu.get("calories", 0),
            "price": menu.get("estimated_cost", 0),
            "image_url": img_url
        })

    return {
        "date": plan.meal_date,
        "calories_per_day": plan.total_calories,
        "price_per_day": plan.estimated_cost,
        "meals": detail_meals
    }

# ----------------------------- 메뉴 변경용 추천 대안 조회 API ------------------------------
@router.get("/menus/{meal_id}/alternatives", response_model=AlternativeMenuResponse)
async def get_meal_alternatives(
    meal_id: str,
    target_date: str = Query(None, description="YYYY-MM-DD 형식 (정확한 식단 검색을 위해 권장)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
                target_meal_date = plan.meal_date # 날짜 객체
                break
                
        if target_meal_data:
            break

    if not target_meal_data:
        raise HTTPException(status_code=404, detail="해당 메뉴가 포함된 식단 기록을 찾을 수 없습니다.")

    selected_menu = target_meal_data.get("selected_menu", {})
    alt_menus = target_meal_data.get("alternative_menus", [])

    current_menu_name = selected_menu.get("name", "")
    current_menu_category = selected_menu.get("category", "") # 카테고리 추출

    # 3. 명세서 기반 Current Meal 가공 (데이터 매핑)
    # AI의 필드명(estimated_cost 등)을 프론트 명세(price 등)로 변환
    current_meal = {
        "meal_id": selected_menu.get("menu_id", meal_id),
        "menu_name": selected_menu.get("name", ""),
        "calories": selected_menu.get("calories", 0),
        "price": selected_menu.get("estimated_cost", 0),
        "image_url": await get_food_image_url(current_menu_name, current_menu_category),
        "date": target_meal_date.strftime("%Y-%m-%d") if target_meal_date else "", # 문자열로 변환
        "slot": target_meal_data.get("meal_order", 1)
    }

    # 4. 명세서 기반 Alternatives 가공
    alternatives = []
    for alt in alt_menus:
        alt_menu_name = alt.get("name", "")
        alt_menu_category = alt.get("category", "")
        alternatives.append({
            "meal_id": alt.get("menu_id", ""),
            "menu_name": alt.get("name", ""),
            "calories": alt.get("calories", 0),
            "price": alt.get("estimated_cost", 0),
            "image_url": await get_food_image_url(alt_menu_name, alt_menu_category)
        })

    # 5. 최종 반환 (Pydantic 스키마가 자동으로 JSON 변환 및 검증을 수행합니다)
    return {
        "current_meal": current_meal,
        "alternatives": alternatives
    }


# ------------------------------- AI 모델 서버 호출용 API ----------------------------------  

# ---------------- 3일치 식단 샘플 생성 요청 API ---------------------- 
@router.post("/generate_sample_3days")
async def generate_initial_meal_plan(
    sample_period_days: int = 3, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사용자의 온보딩을 기반으로 모델링 파트에 3일치 샘플 식단 생성을 모델링 파트에 요청합니다.
    """
    # 1. DB의 User 테이블에서 페르소나 데이터 추출 및 가공
    # 명세서의 규격에 맞게 변환합니다.
    ai_payload = {
        "user_id": f"user_{current_user.id:03d}", # user_001 형식
        "request_type": "meal_style_candidates",
        "profile": {
            "goals": current_user.purpose, # List[string]
            "sample_period_days": sample_period_days,
            "monthly_budget": current_user.monthly_budget,
            "meal_count_per_day": current_user.meals_per_day,
            "cooking_skill": current_user.cooking_skill,
            "preferred_categories": current_user.preferred_style, # 한식, 분식 등
            "diversity_level": current_user.diversity_level,
            "ingredient_preferences": current_user.preferred_ingredients,
            "allergy_ingredients": current_user.excluded_ingredients # 제외 재료
        }
    }

    # 2. 모델링 파트에 데이터 전송 (AI 서버 호출)
    # ai_response = await request_ai_meal_plan(ai_payload)

    # if not ai_response:
    #     # AI 서버 응답 실패 시 Mock 데이터나 에러 반환
    #     raise HTTPException(status_code=500, detail="AI 모델 서버로부터 응답을 받을 수 없습니다.")
    mock_ai_response = get_mock_3days_response()
    
    return {
        "message": "식단 생성 요청이 성공적으로 전달되었습니다.",
        "sent_data": ai_payload, # 디버깅용
        # "ai_result": ai_response
        "ai_result": mock_ai_response
    }

# -------------------- 월간 식단 요청 API ----------------------------
@router.post("/request_monthly_plan")
async def request_monthly_plan(
    request: StyleSelectRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사용자가 선택한 식단 스타일 ID를 바탕으로 모델링 서버에 30일치 월간 식단을 요청합니다.
    """
    update_user_selected_style(db, current_user.id, request.selected_style_id)

    today = date.today()
    
    # [로직 추가] 해당 월의 마지막 날짜 구하기
    # calendar.monthrange(연도, 월) -> (시작 요일, 마지막 날짜) 반환
    _, last_day = calendar.monthrange(today.year, today.month)
    
    # 남은 일 수 계산 (오늘 포함: 마지막 날 - 오늘 날짜 + 1)
    days_remaining = last_day - today.day + 1
    
    # 1. Back -> Modeling 요청 JSON 생성
    modeling_payload = {
        "user_id": f"user_{current_user.id:03d}",
        "request_type": "monthly_plan",
        "selected_style_id": request.selected_style_id, # 프론트에서 넘어온 값
        "profile": {
            "days_remaining": days_remaining,
            "goals": current_user.purpose,
            "monthly_budget": current_user.monthly_budget,
            "period_days": 30, # 명세서에 30으로 고정되어 있음
            "meal_count_per_day": current_user.meals_per_day,
            "cooking_skill": current_user.cooking_skill,
            "preferred_categories": current_user.preferred_style,
            "diversity_level": current_user.diversity_level,
            "ingredient_preferences": current_user.preferred_ingredients,
            "allergy_ingredients": current_user.excluded_ingredients
        }
    }

    # 2. 모델링 파트에 데이터 전송 (AI 서버 호출) - 현재 주석 처리
    # ai_response = await request_ai_monthly_plan(modeling_payload)
    # if not monthly_ai_response:
    #     raise HTTPException(status_code=500, detail="AI 모델 서버로부터 월간 식단 응답을 받을 수 없습니다.")

    # [임시 Mock 데이터] 질문자님이 올려주신 모델링 JSON 원본 데이터 예시
    ai_response = get_mock_month_data_response()

    # 5. DB에 월간 식단 원본 데이터 저장
    days_data = ai_response.get("monthly_plan", {}).get("days")
    if not days_data:
        # monthly_plan에 없으면 style_validation에서 찾음
        days_data = ai_response.get("style_validation", {}).get("days", [])

    # 저장 함수 호출 (에러가 나면 날 것 그대로 콘솔에 뿜어냅니다)
    crud_meal.save_monthly_plan(
        db=db, 
        user_id=current_user.id,  
        ai_days_list=days_data
    )

    # 6. 프론트엔드 달력용으로 데이터 가공 (Transformer)
    current_month_str = datetime.now().strftime("%Y-%m")
    front_response_data = transform_ai_plan_to_front(ai_response, start_date=today)

    # 7. 프론트에 가벼운 달력 데이터 반환
    return front_response_data