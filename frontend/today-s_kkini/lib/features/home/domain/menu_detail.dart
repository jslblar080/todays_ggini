class MenuDetail {
  final String mealId;
  final String menuName;
  final int calories;
  final int price;
  final String? imageUrl;
  final String? videoUrl;
  final List<Ingredient> ingredients;

  const MenuDetail({
    required this.mealId,
    required this.menuName,
    required this.calories,
    required this.price,
    this.imageUrl,
    this.videoUrl,
    required this.ingredients,
  });

  factory MenuDetail.fromJson(Map<String, dynamic> json) {
    // 서버 응답 예:
    // ```json
    // {
    //     "date": "2026-04-06",
    //     "calories_per_day": 1850,
    //     "price_per_day": 10800,
    //     "meals": [
    //         {
    //             "slot": 1,
    //             "meal_id": "M_001",
    //             "menu_name": "볶음밥",
    //             "calories": 650,
    //             "price": 3600,
    //             "image_url": null
    //         },
    //         {
    //             "slot": 2,
    //             "meal_id": "M_002",
    //             "menu_name": "콩나물국",
    //             "calories": 550,
    //             "price": 3600,
    //             "image_url": null
    //         },
    //         {
    //             "slot": 3,
    //             "meal_id": "M_003",
    //             "menu_name": "제철 나물 비빔밥",
    //             "calories": 650,
    //             "price": 3600,
    //             "image_url": null
    //         }
    //     ]
    // }
    // ```
    return MenuDetail(
      mealId: json['meal_id'] as String,
      menuName: json['menu_name'] as String,
      calories: (json['calories'] as num).toInt(),
      price: (json['price'] as num).toInt(),
      imageUrl: json['image_url'] as String?,
      videoUrl: json['video_url'] as String?,
      ingredients: (json['ingredients'] as List)
          .map((i) => Ingredient.fromJson(i as Map<String, dynamic>))
          .toList(),
    );
  }
}

class Ingredient {
  final String ingredientId;
  final String ingredientName;
  final String standardUnit;
  final String? imageUrl;
  final LowestPrice lowestPrice;
  final EcommercePrices prices;

  const Ingredient({
    required this.ingredientId,
    required this.ingredientName,
    required this.standardUnit,
    this.imageUrl,
    required this.lowestPrice,
    required this.prices,
  });

  factory Ingredient.fromJson(Map<String, dynamic> json) {
    return Ingredient(
      ingredientId: json['ingredient_id'] as String,
      ingredientName: json['ingredient_name'] as String,
      standardUnit: json['standard_unit'] as String,
      imageUrl: json['image_url'] as String?,
      lowestPrice: LowestPrice.fromJson(
        json['lowest_price_between_market'] as Map<String, dynamic>,
      ),
      prices: EcommercePrices.fromJson(
        json['e_commerce_prices'] as Map<String, dynamic>,
      ),
    );
  }

  // 마켓 키 → 한글 변환
  static String marketToKorean(String market) {
    switch (market) {
      case 'coupang': return '쿠팡';
      case 'market_kurly': return '컬리';
      case 'naver_shopping': return '네이버';
      default: return market;
    }
  }

  // 마켓 ID로 해당 마켓의 가격을 가져옴. 재고 없으면 null
  int? priceFor(String market) {
    switch (market) {
      case 'coupang':
        return prices.coupang;
      case 'market_kurly':
        return prices.marketKurly;
      case 'naver_shopping':
        return prices.naverShopping;
      default:
        return null;
    }
  }

  // 사용자 선택 마켓에 따른 적용 가격. 선택 안 했거나 재고 없으면 최저가 폴백
  int? effectivePrice(String? selectedMarket) {
    if (selectedMarket != null) {
      final p = priceFor(selectedMarket);
      if (p != null) return p;
    }
    return lowestPrice.price;
  }

  // 어떤 마켓도 재고가 없는 재료인지 (모든 가격 null)
  bool get hasAnyMarketStock =>
      prices.coupang != null ||
      prices.marketKurly != null ||
      prices.naverShopping != null;

  // 사용자 선택 마켓 ID. 선택 안 했거나 재고 없으면 최저가 마켓
  String? effectiveMarket(String? selectedMarket) {
    if (selectedMarket != null && priceFor(selectedMarket) != null) {
      return selectedMarket;
    }
    return lowestPrice.market;
  }

  // ─────────── 사용자 마켓(제외 반영) 고려 버전 ───────────

  // 허용된 마켓들 중에서만 최저가 마켓 키 찾기
  String? lowestMarketAmong(List<String> userMarkets) {
    final candidates = <String, int>{};
    for (final key in ['coupang', 'market_kurly', 'naver_shopping']) {
      if (userMarkets.contains(marketToKorean(key))) {
        final p = priceFor(key);
        if (p != null) candidates[key] = p;
      }
    }
    if (candidates.isEmpty) return null;
    return candidates.entries.reduce((a, b) => a.value <= b.value ? a : b).key;
  }

  // 사용자 마켓 고려한 적용 가격
  int? effectivePriceWithin(String? selectedMarket, List<String> userMarkets) {
    if (selectedMarket != null &&
        userMarkets.contains(marketToKorean(selectedMarket))) {
      final p = priceFor(selectedMarket);
      if (p != null) return p;
    }
    final m = lowestMarketAmong(userMarkets);
    return m != null ? priceFor(m) : null;
  }

  // 사용자 마켓 고려한 적용 마켓 키
  String? effectiveMarketWithin(String? selectedMarket, List<String> userMarkets) {
    if (selectedMarket != null &&
        userMarkets.contains(marketToKorean(selectedMarket)) &&
        priceFor(selectedMarket) != null) {
      return selectedMarket;
    }
    return lowestMarketAmong(userMarkets);
  }
}

class LowestPrice {
  final String? market;
  final int? price;

  const LowestPrice({this.market, this.price});

  factory LowestPrice.fromJson(Map<String, dynamic> json) {
    return LowestPrice(
      market: json['market'] as String?,
      price: (json['price'] as num?)?.toInt(),
    );
  }
}

// 쿠팡/컬리/네이버 가격으로 어느 마켓이든 재고 없는 null일 수 있음
class EcommercePrices {
  final int? coupang;
  final int? marketKurly;
  final int? naverShopping;

  const EcommercePrices({this.coupang, this.marketKurly, this.naverShopping});

  factory EcommercePrices.fromJson(Map<String, dynamic> json) {
    int? extractPrice(String key) {
      final marketData = json[key];
      if (marketData == null) return null;
      if (marketData is Map<String, dynamic>) {
        return (marketData['lowest_price'] as num?)?.toInt();
      }
      return null;
    }

    return EcommercePrices(
      coupang: extractPrice('coupang'),
      marketKurly: extractPrice('market_kurly'),
      naverShopping: extractPrice('naver_shopping'),
    );
  }
}