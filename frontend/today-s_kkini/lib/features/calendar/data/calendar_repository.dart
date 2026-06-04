import 'package:dio/dio.dart';

import '../../../core/utils/format.dart';
import '../domain/monthly_meal_plan.dart';

class CalendarRepository {
  final Dio _dio;
  CalendarRepository(this._dio);

  // 특정 월의 식단 캘린더 데이터
  // 백엔드: GET /api/v1/meal/calendar?month=YYYY-MM
  Future<MonthlyMealPlan> fetchMonth(int year, int month) async {
    final monthStr = formatYearMonth(year, month);
    final response = await _dio.get(
      '/meal/calendar',
      queryParameters: {'month': monthStr},
    );
    return MonthlyMealPlan.fromJson(response.data as Map<String, dynamic>);
  }

  // 두 날짜의 식단을 통째로 교환 (내용은 그대로, meal_date 라벨만 swap)
  // 백엔드: PATCH /api/v1/meal/{date}/swap   body: { "with_date": "YYYY-MM-DD" }
  // 응답: { "swapped": [CalendarDay, CalendarDay] } — 교환 후 두 날짜의 요약
  // 응답 CalendarDay 구조가 DayEntry와 동일하므로 그대로 파싱해 반환한다.
  Future<List<DayEntry>> swapDays(DateTime date, DateTime withDate) async {
    final response = await _dio.patch(
      '/meal/${formatDate(date)}/swap',
      data: {'with_date': formatDate(withDate)},
    );
    final data = response.data as Map<String, dynamic>;
    return (data['swapped'] as List)
        .map((d) => DayEntry.fromJson(d as Map<String, dynamic>))
        .toList();
  }
}
