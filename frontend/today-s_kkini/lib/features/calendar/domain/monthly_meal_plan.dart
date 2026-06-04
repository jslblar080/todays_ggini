class MonthlyMealPlan {
  final String month; // "2026-04"
  final int durationDays; // 식단 있는 일수
  final int totalPricePerMonth; // 그 달 총 비용
  final int averageCaloriesPerMonth; // 평균 칼로리
  final List<DayEntry> days; // 그 달 모든 날짜 (식단 없는 날 포함)

  const MonthlyMealPlan({
    required this.month,
    required this.durationDays,
    required this.totalPricePerMonth,
    required this.averageCaloriesPerMonth,
    required this.days,
  });

  factory MonthlyMealPlan.fromJson(Map<String, dynamic> json) {
    return MonthlyMealPlan(
      month: json['month'] as String,
      durationDays: (json['duration_days'] as num).toInt(),
      totalPricePerMonth: (json['total_price_per_month'] as num).toInt(),
      averageCaloriesPerMonth:
          (json['average_calories_per_month'] as num).toInt(),
      days:
          (json['days'] as List)
              .map((d) => DayEntry.fromJson(d as Map<String, dynamic>))
              .toList(),
    );
  }

  // 일부 날짜만 교체한 새 인스턴스 (swap 후 캐시 갱신용).
  // 월 내 swap은 합계/평균이 불변이므로 days만 갈아끼우면 된다.
  MonthlyMealPlan copyWith({List<DayEntry>? days}) {
    return MonthlyMealPlan(
      month: month,
      durationDays: durationDays,
      totalPricePerMonth: totalPricePerMonth,
      averageCaloriesPerMonth: averageCaloriesPerMonth,
      days: days ?? this.days,
    );
  }
}

// 한 날짜의 식단 정보
// 식단 없는 날: caloriesPerDay/pricePerDay가 null, meals가 빈 배열
class DayEntry {
  final DateTime date;
  final int? caloriesPerDay;
  final int? pricePerDay;
  final List<DayMeal> meals;

  const DayEntry({
    required this.date,
    this.caloriesPerDay,
    this.pricePerDay,
    required this.meals,
  });

  // 식단이 있는 날인지 (UI에서 활성/비활성 분기용)
  bool get hasMealPlan => meals.isNotEmpty;

  factory DayEntry.fromJson(Map<String, dynamic> json) {
    return DayEntry(
      date: DateTime.parse(json['date'] as String),
      caloriesPerDay: (json['calories_per_day'] as num?)?.toInt(),
      pricePerDay: (json['price_per_day'] as num?)?.toInt(),
      meals:
          (json['meals'] as List)
              .map((m) => DayMeal.fromJson(m as Map<String, dynamic>))
              .toList(),
    );
  }
}

// 캘린더 셀에 표시할 슬롯 정보 (간소화)
// 일일 상세 화면(#10)의 풀 정보와 다른 모델
class DayMeal {
  final int slot;
  final String mealId;
  final String menuName;

  const DayMeal({
    required this.slot,
    required this.mealId,
    required this.menuName,
  });

  factory DayMeal.fromJson(Map<String, dynamic> json) {
    return DayMeal(
      slot: json['slot'] as int,
      mealId: json['meal_id'] as String,
      menuName: json['menu_name'] as String,
    );
  }
}
