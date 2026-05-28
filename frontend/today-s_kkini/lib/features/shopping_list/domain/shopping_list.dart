// 장보기 목록 (화면 #9-1)
//
// API 명세서 7번 GET /shopping-list 응답을 매핑
// 토글/삭제 시 클라이언트에서 즉시 갱신할 수 있도록 모든 클래스에 copyWith 제공

class ShoppingList {
  // 전체 항목 개수 (체크 여부 무관)
  final int totalItems;

  // 체크된 항목 개수
  final int checkedItemsCount;

  // 체크된 항목들의 합계 금액
  final int totalPricePerShopping;

  // 마켓별 체크된 항목 개수 (UI 상단 인디케이터에 사용)
  final List<ShoppingMarketCount> marketCounts;

  // 마켓별로 묶인 항목 그룹
  final List<ShoppingMarketGroup> marketGroups;

  const ShoppingList({
    required this.totalItems,
    required this.checkedItemsCount,
    required this.totalPricePerShopping,
    required this.marketCounts,
    required this.marketGroups,
  });

  List<ShoppingItem> get flatItems => [
    for (final g in marketGroups) ...g.items,
  ];

  // 체크된 항목 개수가 0보다 큰 마켓의 개수 (예: "마켓 2곳")
  int get activeMarketCount => marketCounts.where((m) => m.count > 0).length;

  factory ShoppingList.fromJson(Map<String, dynamic> json) {
    return ShoppingList(
      totalItems: (json['total_items'] as num).toInt(),
      checkedItemsCount: (json['checked_items_count'] as num).toInt(),
      totalPricePerShopping: (json['total_price_per_shopping'] as num).toInt(),
      marketCounts:
          (json['market_counts'] as List<dynamic>)
              .map(
                (e) => ShoppingMarketCount.fromJson(e as Map<String, dynamic>),
              )
              .toList(),
      marketGroups:
          (json['market_groups'] as List<dynamic>)
              .map(
                (e) => ShoppingMarketGroup.fromJson(e as Map<String, dynamic>),
              )
              .toList(),
    );
  }

  ShoppingList copyWith({
    int? totalItems,
    int? checkedItemsCount,
    int? totalPricePerShopping,
    List<ShoppingMarketCount>? marketCounts,
    List<ShoppingMarketGroup>? marketGroups,
  }) {
    return ShoppingList(
      totalItems: totalItems ?? this.totalItems,
      checkedItemsCount: checkedItemsCount ?? this.checkedItemsCount,
      totalPricePerShopping:
          totalPricePerShopping ?? this.totalPricePerShopping,
      marketCounts: marketCounts ?? this.marketCounts,
      marketGroups: marketGroups ?? this.marketGroups,
    );
  }
}

class ShoppingMarketCount {
  final String market;
  final int count;

  const ShoppingMarketCount({required this.market, required this.count});

  factory ShoppingMarketCount.fromJson(Map<String, dynamic> json) {
    return ShoppingMarketCount(
      market: json['market'] as String,
      count: (json['count'] as num).toInt(),
    );
  }

  ShoppingMarketCount copyWith({String? market, int? count}) {
    return ShoppingMarketCount(
      market: market ?? this.market,
      count: count ?? this.count,
    );
  }
}

class ShoppingMarketGroup {
  final String market;
  final int subtotal;
  final List<ShoppingItem> items;

  const ShoppingMarketGroup({
    required this.market,
    required this.subtotal,
    required this.items,
  });

  factory ShoppingMarketGroup.fromJson(Map<String, dynamic> json) {
    return ShoppingMarketGroup(
      market: json['market'] as String,
      subtotal: (json['subtotal'] as num).toInt(),
      items:
          (json['items'] as List<dynamic>)
              .map((e) => ShoppingItem.fromJson(e as Map<String, dynamic>))
              .toList(),
    );
  }

  ShoppingMarketGroup copyWith({
    String? market,
    int? subtotal,
    List<ShoppingItem>? items,
  }) {
    return ShoppingMarketGroup(
      market: market ?? this.market,
      subtotal: subtotal ?? this.subtotal,
      items: items ?? this.items,
    );
  }
}

class ShoppingItem {
  final String itemId;
  final String ingredientId;
  final String ingredientName;
  final String standardUnit;
  final String deliveryType;
  final int lowestPrice;
  final String productTitle;
  final String purchaseLink;
  final bool isChecked;
  final String? status;

  const ShoppingItem({
    required this.itemId,
    required this.ingredientId,
    required this.ingredientName,
    required this.standardUnit,
    required this.deliveryType,
    required this.lowestPrice,
    required this.productTitle,
    required this.purchaseLink,
    required this.isChecked,
    this.status,
  });

  factory ShoppingItem.fromJson(Map<String, dynamic> json) {
    return ShoppingItem(
      itemId: json['item_id'] as String,
      ingredientId: json['ingredient_id'] as String,
      ingredientName: json['ingredient_name'] as String,
      standardUnit: json['standard_unit'] as String,
      deliveryType: json['delivery_type'] as String,
      lowestPrice: (json['lowest_price'] as num).toInt(),
      productTitle: json['product_title'] as String,
      purchaseLink: json['purchase_link'] as String,
      isChecked: json['is_checked'] as bool,
      status: json['status'] as String?,
    );
  }

  ShoppingItem copyWith({
    String? itemId,
    String? ingredientId,
    String? ingredientName,
    String? standardUnit,
    String? deliveryType,
    int? lowestPrice,
    String? productTitle,
    String? purchaseLink,
    bool? isChecked,
    String? status,
  }) {
    return ShoppingItem(
      itemId: itemId ?? this.itemId,
      ingredientId: ingredientId ?? this.ingredientId,
      ingredientName: ingredientName ?? this.ingredientName,
      standardUnit: standardUnit ?? this.standardUnit,
      deliveryType: deliveryType ?? this.deliveryType,
      lowestPrice: lowestPrice ?? this.lowestPrice,
      productTitle: productTitle ?? this.productTitle,
      purchaseLink: purchaseLink ?? this.purchaseLink,
      isChecked: isChecked ?? this.isChecked,
      status: status ?? this.status,
    );
  }
}

// 마켓 식별자 → 한글 라벨
String shoppingMarketLabel(String market) => switch (market) {
  'coupang' => '쿠팡',
  'market_kurly' => '컬리',
  'naver_shopping' => '네이버',
  _ => market,
};
