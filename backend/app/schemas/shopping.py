from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from enum import Enum

class ItemStatus(str, Enum):
    PENDING = "PENDING"
    CHECKED = "CHECKED"
    ORDERED = "ORDERED"
    OUT_OF_STOCK = "OUT_OF_STOCK"

# -------------- 재료 마켓별 가격 비교 상세 전용 스키마 -----------------
class MarketProductDetail(BaseModel):
    delivery_type: str
    lowest_price: int
    product_title: str
    purchase_link: str
    is_lowest: bool

class ECommercePrices(BaseModel):
    coupang: Optional[MarketProductDetail] = None
    market_kurly: Optional[MarketProductDetail] = None
    naver_shopping: Optional[MarketProductDetail] = None

# 재료 상세 가격 조회 응답 (GET /ingredients/{id}/prices)
class IngredientPriceResponse(BaseModel):
    ingredient_id: str
    ingredient_name: str
    standard_unit: str
    image_url: Optional[str] = None
    e_commerce_prices: ECommercePrices

# ------------ 장보기 목록 화면 전용 스키마 --------------
class MarketCount(BaseModel):
    market: str
    count: int

class ShoppingItem(BaseModel):
    item_id: str
    ingredient_id: str
    ingredient_name: str
    standard_unit: str
    delivery_type: str
    lowest_price: int
    product_title: str
    purchase_link: str
    is_checked: bool
    status: Optional[ItemStatus] = None # [추가됨] 커머스 라이프사이클 상태

    model_config = ConfigDict(from_attributes=True) # [추가됨] ORM 매핑

class MarketGroup(BaseModel):
    market: str
    subtotal: int
    items: List[ShoppingItem]

class ShoppingListResponse(BaseModel):
    total_items: int
    checked_items_count: int
    total_price_per_shopping: int
    market_counts: List[MarketCount]
    market_groups: List[MarketGroup]

# 장바구니 아이템 추가/수정 요청 (POST /shopping-list/items)
# 체크박스를 포함한 재료 상세 정보
class IngredientSelectRequest(BaseModel):
    ingredient_id: str
    ingredient_name: Optional[str] = None
    standard_unit: Optional[str] = None
    market_name: str
    price: Optional[int] = None
    delivery_type: Optional[str] = None
    product_title: Optional[str] = None
    purchase_link: Optional[str] = None
    is_essential: bool = True
    is_checked: bool = True # # 체크된 것만 담기 로직용
    status: ItemStatus = ItemStatus.CHECKED # [추가됨] 기본 상태는 CHECKED

# --- 공통 요약(Summary) 스키마 ---
class ShoppingSummary(BaseModel):
    total_items: int
    checked_items_count: int
    total_price_per_shopping: int
    market_counts: List[MarketCount]

# 항목 체크 상태 업데이트
class CheckUpdateItem(BaseModel):
    item_id: str
    is_checked: bool

# 4. 일괄 삭제 요청
class DeleteItemsRequest(BaseModel):
    item_ids: List[str]

# --- PATCH 응답용 스키마 ---
# (명세서 이미지 반영: 단일 항목 변경 응답)
class CheckUpdateResponse(BaseModel):
    updated_items: List[CheckUpdateItem] # 업데이트된 여러 항목의 결과를 리스트로 반환
    summary: ShoppingSummary

# --- DELETE 응답용 스키마 ---
class BatchDeleteResponse(BaseModel):
    deleted_count: int
    deleted_item_ids: List[str]  # 또는 List[int]
    summary: ShoppingSummary

# 5. 복원 요청 (삭제된 항목 되돌리기) — body 는 삭제와 동일하게 item_ids 만 받음
class RestoreItemsRequest(BaseModel):
    item_ids: List[str]

# --- 복원 응답용 스키마 ---
class RestoreItemsResponse(BaseModel):
    restored_count: int
    restored_item_ids: List[str]
    summary: ShoppingSummary