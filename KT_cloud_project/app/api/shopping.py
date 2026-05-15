from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db

from app.models.shopping import ShoppingList, ShoppingItem
from app.schemas.shopping import (IngredientPriceResponse, ShoppingListResponse, IngredientSelectRequest, DeleteItemsRequest,
                                  CheckUpdateItem, CheckUpdateResponse, BatchDeleteResponse)
from app.models.user import User

router = APIRouter()

@router.get("/ingredients/{ingredient_id}/prices", response_model=IngredientPriceResponse)
async def get_ingredient_market_prices(
    ingredient_id: str,
    db: Session = Depends(get_db)
):
    """
    [화면 10-2] 특정 재료의 마켓별 상세 가격 정보 조회
    - 각 마켓의 가격을 비교하여 가장 저렴한 곳의 is_lowest를 True로 설정합니다.
    """
    
    # 1. 기초 데이터 (AI 연동 전 Mock 데이터)
    prices_data = {
        "coupang": {
            "delivery_type": "로켓프레시",
            "lowest_price": 1200,
            "product_title": "곰곰 국내산 제철 나물 100g",
            "purchase_link": "https://www.coupang.com/...",
            "is_lowest": False
        },
        "market_kurly": {
            "delivery_type": "샛별배송",
            "lowest_price": 1400,
            "product_title": "[KF365] 제철 나물 100g",
            "purchase_link": "https://www.kurly.com/...",
            "is_lowest": False
        },
        "naver_shopping": {
            "delivery_type": "일반배송",
            "lowest_price": 1300,
            "product_title": "농협 제철 나물 100g",
            "purchase_link": "https://smartstore.naver.com/...",
            "is_lowest": False
        }
    }

    # 2. 최저가 계산 로직
    # 모든 마켓의 가격 중 최소값을 찾습니다.
    min_price = min(market["lowest_price"] for market in prices_data.values())

    # 최소값과 일치하는 마켓의 is_lowest를 True로 변경합니다.
    for details in prices_data.values():
        if details["lowest_price"] == min_price:
            details["is_lowest"] = True
            # 최저가가 여러 곳일 수 있으므로 break를 쓰지 않거나, 
            # 한 곳만 지정하고 싶다면 break를 추가하세요.

    return {
        "ingredient_id": ingredient_id,
        "ingredient_name": "제철 나물",
        "standard_unit": "100g",
        "image_url": None,
        "e_commerce_prices": prices_data
    }

# ---------------------------- 재료 상세 화면 관련 ----------------------------------

@router.post("/add-shopping-items")
async def sync_shopping_items(
    items: List[IngredientSelectRequest],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [화면 10-1] 재료 상세 화면에서 선택한 항목들을 장바구니에 추가/업데이트합니다.
    """
    # 1. 유저의 고정 장바구니(ShoppingList) 조회 및 생성
    shopping_list = db.query(ShoppingList).filter(ShoppingList.user_id == current_user.id).first()
    if not shopping_list:
        shopping_list = ShoppingList(user_id=current_user.id)
        db.add(shopping_list)
        db.flush()

    added_count = 0
    for item_data in items:
        # 장바구니에 이미 있는지 확인 (Upsert)
        existing_item = db.query(ShoppingItem).filter(
            ShoppingItem.list_id == shopping_list.id,
            ShoppingItem.ingredient_id == item_data.ingredient_id
        ).first()

        if existing_item:
            for key, value in item_data.dict().items():
                setattr(existing_item, key, value)
        else:
            # 없다면 새로 추가
            new_item = ShoppingItem(
                list_id=shopping_list.id,
                **item_data.dict()
            )
            db.add(new_item)
        added_count += 1
    
    db.commit()
    return {"message": "선택된 재료들이 장바구니에 반영되었습니다.", "added_count": added_count}

# --------------------------- 장보기 목록 화면 관련 --------------------------------
# --- 공통 요약 정보 계산 Helper 함수 ---
def calculate_shopping_summary(db: Session, list_id: int) -> dict:
    """해당 장바구니의 최신 요약 정보를 계산하여 반환합니다."""
    items = db.query(ShoppingItem).filter(ShoppingItem.list_id == list_id).all()
    
    market_data = {
        "coupang": 0,
        "market_kurly": 0,
        "naver_shopping": 0
    }
    
    total_price = 0
    checked_count = 0
    
    for item in items:
        # 체크된 항목만 금액과 마켓별 개수에 포함
        if item.is_checked:
            total_price += item.price
            checked_count += 1
            if item.market_name in market_data:
                market_data[item.market_name] += 1
            else:
                market_data[item.market_name] = 1 # 예외 마켓 처리

    market_counts = [
        {"market": m, "count": c} for m, c in market_data.items()
    ]
    
    return {
        "total_items": len(items),
        "checked_items_count": checked_count,
        "total_price_per_shopping": total_price,
        "market_counts": market_counts
    }

@router.get("/shopping-list", response_model=ShoppingListResponse)
async def get_shopping_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [화면 9-1] 장보기 목록 정밀 조회
    - 마켓별 그룹화 (Coupang, Kurly, Naver)
    - 상단 요약 바 데이터 (총 금액, 아이템 수)
    """
    # 1. 해당 유저의 단일 장바구니 헤더 조회
    shopping_list = db.query(ShoppingList).filter(ShoppingList.user_id == current_user.id).first()
    
    if not shopping_list:
        return {
            "total_items": 0, "checked_items_count": 0, "total_price_per_shopping": 0,
            "market_counts": [], "market_groups": []
        }

    # 체크 여부와 상관없이 내 바구니에 있는 모든 아이템 조회
    items = db.query(ShoppingItem).filter(
        ShoppingItem.list_id == shopping_list.id
    ).all()

    # 3. 마켓별 그룹화 및 통계 산출
    # 디자인에 나온 3대 마켓 기본 틀 생성
    market_data = {
        "coupang": {"subtotal": 0, "items": []},
        "market_kurly": {"subtotal": 0, "items": []},
        "naver_shopping": {"subtotal": 0, "items": []}
    }
    
    total_price = 0
    checked_count = 0

    for item in items:
        m_name = item.market_name
        if m_name in market_data:
            # DB 모델(item)의 데이터를 응답 스키마가 원하는 이름(key)으로 매핑
            mapped_item = {
                "item_id": str(item.id),               
                "ingredient_id": item.ingredient_id,
                "ingredient_name": item.ingredient_name,
                "standard_unit": item.standard_unit,
                "market_name": item.market_name,
                "lowest_price": item.price,        
                "delivery_type": item.delivery_type,
                "product_title": item.product_title,
                "purchase_link": item.purchase_link,
                "is_checked": item.is_checked,
                "is_essential": item.is_essential,
                "is_lowest": item.is_lowest
            }

            market_data[m_name]["items"].append(mapped_item)
            
            # 수정 2: '합계'와 '체크된 개수'는 is_checked가 True일 때만 증가시킴
            if item.is_checked:
                market_data[m_name]["subtotal"] += item.price
                total_price += item.price
                checked_count += 1

    # 4. 프론트엔드용 리스트 포맷으로 변환
    market_groups = []
    market_counts = []
    
    for m_name, data in market_data.items():
        market_groups.append({
            "market": m_name,
            "subtotal": data["subtotal"],
            "items": data["items"]
        })
        market_counts.append({
            "market": m_name,
            "count": len(data["items"])
        })

    return {
        "total_items": len(items),               # 담긴 전체 개수
        "checked_items_count": checked_count,    # 체크된 개수
        "total_price_per_shopping": total_price, # 체크된 항목들의 총액
        "market_counts": market_counts,
        "market_groups": market_groups
    }

@router.patch("/shopping-list/items/check", response_model=CheckUpdateResponse)
async def update_item_checks(
    updates: List[CheckUpdateItem],  # 이미지 명세상 단일 객체 업데이트로 보임
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [화면 9-1] 장보기 목록 내 아이템의 체크 상태 업데이트 및 최신 요약 정보 반환
    """
    shopping_list = db.query(ShoppingList).filter(ShoppingList.user_id == current_user.id).first()
    
    updated_results = []

    # 상태 업데이트
    for update in updates:
        item = db.query(ShoppingItem).filter(
            ShoppingItem.id == int(update.item_id),
            ShoppingItem.list_id == shopping_list.id
        ).first()
        
        if item:
            item.is_checked = update.is_checked
            updated_results.append({
                "item_id": str(item.id), 
                "is_checked": item.is_checked
            })

    # 변경사항을 DB에 한 번에 반영 (트랜잭션 최적화)
    db.commit()

    # 업데이트된 최신 요약 정보 계산
    summary_data = calculate_shopping_summary(db, shopping_list.id)

    # 3. 명세서 형식에 맞춰 반환
    return {
        "updated_items": updated_results,
        "summary": summary_data
    }

@router.delete("/shopping-list/items/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_items(
    request: DeleteItemsRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [화면 9-1] 선택 항목 일괄 삭제 및 최신 요약 정보 반환
    """
    shopping_list = db.query(ShoppingList).filter(ShoppingList.user_id == current_user.id).first()

    # 1. 일괄 삭제 진행
    deleted_count = db.query(ShoppingItem).filter(
        ShoppingItem.id.in_(request.item_ids),
        ShoppingItem.list_id == shopping_list.id
    ).delete(synchronize_session=False)
    db.commit()

    # 2. 삭제 반영된 최신 요약 정보 계산
    summary_data = calculate_shopping_summary(db, shopping_list.id)

    # 3. 명세서 형식에 맞춰 반환
    return {
        "deleted_count": deleted_count,
        "deleted_item_ids": request.item_ids,
        "summary": summary_data
    }