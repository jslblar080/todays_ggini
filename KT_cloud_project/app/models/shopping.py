from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    id = Column(Integer, primary_key=True, index=True)
    # 유저당 하나의 목록만 가지도록 unique=True 설정
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 관계 설정
    owner = relationship("User", back_populates="shopping_list")
    items = relationship("ShoppingItem", back_populates="shopping_list", cascade="all, delete-orphan")

class ShoppingItem(Base):
    __tablename__ = "shopping_items"

    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer, ForeignKey("shopping_lists.id", ondelete="CASCADE"), nullable=False)
    
    # 재료 정보
    ingredient_id = Column(String, index=True)  # 외부 식재료 마스터 ID
    ingredient_name = Column(String, nullable=False)
    standard_unit = Column(String)  # 예: 100g, 10구
    
    # 마켓 및 구매 정보 (명세서 기반)
    market_name = Column(String, nullable=False)  # coupang, market_kurly, naver_shopping
    delivery_type = Column(String)  # 로켓프레시, 샛별배송 등
    price = Column(Integer, nullable=False)  # lowest_price
    product_title = Column(String)  # 실제 판매 상품명
    purchase_link = Column(String)  # 구매 연결 URL
    
    # 상태값 (핵심!)
    is_checked = Column(Boolean, default=False)
    is_essential = Column(Boolean, default=True) # 주재료/부재료 구분
    is_lowest = Column(Boolean, default=False)

    # 가격 비교 데이터 (명세서 image_9830b9의 계층 구조를 저장)
    # 팝업을 열었을 때 다른 마켓 가격을 즉시 보여주기 위해 JSON 형태로 캐싱
    market_details = Column(JSON, nullable=True)

    shopping_list = relationship("ShoppingList", back_populates="items")