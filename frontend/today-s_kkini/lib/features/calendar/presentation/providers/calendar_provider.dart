import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../../../../core/network/api_client.dart';
import '../../data/calendar_repository.dart';
import '../../domain/monthly_meal_plan.dart';

final calendarRepositoryProvider = Provider<CalendarRepository>((ref) {
  return CalendarRepository(ref.watch(dioProvider));
});

/// 주의 시작일(월요일)을 반환
DateTime _weekStart(DateTime date) {
  return date.subtract(Duration(days: date.weekday - 1));
}

/// 해당 주가 속하는 "표시용 연/월/주차"를 계산
({int year, int month, int weekNumber}) _weekLabel(DateTime monday) {
  final today = DateTime.now();
  final weekDays = List.generate(7, (i) => monday.add(Duration(days: i)));
  
  // 오늘이 이 주에 포함되어 있으면 오늘 기준 월 사용
  final todayInWeek = weekDays.any((d) =>
      d.year == today.year && d.month == today.month && d.day == today.day);
  
  final referenceDate = todayInWeek ? today : monday;
  final year = referenceDate.year;
  final month = referenceDate.month;

  // 해당 월의 첫 번째 같은 요일(월요일) 찾기
  final firstOfMonth = DateTime(year, month, 1);
  final firstMonday = firstOfMonth.add(
    Duration(days: (8 - firstOfMonth.weekday) % 7),
  );

  // 월요일 기준으로 몇 번째 주인지 계산
  final weekStart = weekDays.firstWhere((d) => d.month == month, orElse: () => monday);
  final firstWeekMonday = firstOfMonth.weekday == 1
      ? firstOfMonth
      : firstOfMonth.subtract(Duration(days: firstOfMonth.weekday - 1));
  
  final weekNumber = ((weekStart.difference(firstWeekMonday).inDays) ~/ 7) + 1;

  return (year: year, month: month, weekNumber: weekNumber);
}

class CalendarState {
  final DateTime currentWeekStart; // 현재 보고 있는 주의 월요일
  final Map<String, MonthlyMealPlan> cache; // "2026-05" → MonthlyMealPlan
  final bool isLoading;
  final Object? error;

  const CalendarState({
    required this.currentWeekStart,
    this.cache = const {},
    this.isLoading = false,
    this.error,
  });

  /// 현재 주에 필요한 연/월 (월~일 중 목요일 기준)
  ({int year, int month, int weekNumber}) get weekLabel =>
      _weekLabel(currentWeekStart);

  /// 현재 주의 7일 리스트
  List<DateTime> get currentWeekDays =>
      List.generate(7, (i) => currentWeekStart.add(Duration(days: i)));

  /// 현재 주가 걸쳐있는 월들의 플랜 (월~일이 두 달에 걸칠 수 있음)
  MonthlyMealPlan? planFor(DateTime date) {
    final key = _monthKey(date.year, date.month);
    return cache[key];
  }

  /// 현재 주 레이블 기준 월의 플랜 (SummaryCard용)
  MonthlyMealPlan? get currentPlan {
    final label = weekLabel;
    return cache[_monthKey(label.year, label.month)];
  }

  CalendarState copyWith({
    DateTime? currentWeekStart,
    Map<String, MonthlyMealPlan>? cache,
    bool? isLoading,
    Object? error,
  }) {
    return CalendarState(
      currentWeekStart: currentWeekStart ?? this.currentWeekStart,
      cache: cache ?? this.cache,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }

  static String _monthKey(int year, int month) =>
      '${year.toString().padLeft(4, '0')}-${month.toString().padLeft(2, '0')}';
}

class CalendarNotifier extends StateNotifier<CalendarState> {
  final CalendarRepository _repository;

  CalendarNotifier(this._repository)
      : super(CalendarState(
          currentWeekStart: _weekStart(DateTime.now()),
        )) {
    _loadWeekIfNeeded(state.currentWeekStart);
  }

  void goToPrevWeek() {
    final prev = state.currentWeekStart.subtract(const Duration(days: 7));
    state = state.copyWith(currentWeekStart: prev);
    _loadWeekIfNeeded(prev);
  }

  void goToNextWeek() {
    final next = state.currentWeekStart.add(const Duration(days: 7));
    state = state.copyWith(currentWeekStart: next);
    _loadWeekIfNeeded(next);
  }

  /// 주의 월~일에 걸쳐있는 달들을 모두 로드
  Future<void> _loadWeekIfNeeded(DateTime monday) async {
    final days = List.generate(7, (i) => monday.add(Duration(days: i)));
    final months = <String>{};
    for (final d in days) {
      months.add(CalendarState._monthKey(d.year, d.month));
    }

    for (final key in months) {
      if (state.cache.containsKey(key)) continue;
      final parts = key.split('-');
      final year = int.parse(parts[0]);
      final month = int.parse(parts[1]);

      state = state.copyWith(isLoading: true, error: null);
      try {
        final plan = await _repository.fetchMonth(year, month);
        if (!mounted) return;
        final newCache = Map<String, MonthlyMealPlan>.from(state.cache);
        newCache[key] = plan;
        state = state.copyWith(cache: newCache, isLoading: false);
      } catch (e) {
        if (!mounted) return;
        state = state.copyWith(error: e, isLoading: false);
      }
    }
  }

  Future<void> swapDates(DateTime from, DateTime to) async {
    final swapped = await _repository.swapDays(from, to);
    if (!mounted) return;

    // 영향받는 달 캐시 업데이트
    final affectedMonths = <String>{
      CalendarState._monthKey(from.year, from.month),
      CalendarState._monthKey(to.year, to.month),
    };

    var newCache = Map<String, MonthlyMealPlan>.from(state.cache);
    for (final key in affectedMonths) {
      final plan = newCache[key];
      if (plan == null) continue;
      final updatedDays = [
        for (final d in plan.days)
          swapped.firstWhere(
            (s) => _sameYmd(s.date, d.date),
            orElse: () => d,
          ),
      ];
      newCache[key] = plan.copyWith(days: updatedDays);
    }
    state = state.copyWith(cache: newCache);
  }
}

bool _sameYmd(DateTime a, DateTime b) =>
    a.year == b.year && a.month == b.month && a.day == b.day;

final calendarProvider =
    StateNotifierProvider.autoDispose<CalendarNotifier, CalendarState>(
  (ref) => CalendarNotifier(ref.watch(calendarRepositoryProvider)),
);