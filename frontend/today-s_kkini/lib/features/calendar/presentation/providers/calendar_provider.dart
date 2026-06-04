import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../../../../core/network/api_client.dart';
import '../../data/calendar_repository.dart';
import '../../domain/monthly_meal_plan.dart';

// Repository Provider
final calendarRepositoryProvider = Provider<CalendarRepository>((ref) {
  return CalendarRepository(ref.watch(dioProvider));
});

// State 클래스
class CalendarState {
  final int currentYear;
  final int currentMonth;
  final Map<String, MonthlyMealPlan> cache; // "2026-05" → MonthlyMealPlan
  final bool isLoading;
  final Object? error;

  const CalendarState({
    required this.currentYear,
    required this.currentMonth,
    this.cache = const {},
    this.isLoading = false,
    this.error,
  });

  // 지금 보고 있는 달의 데이터 (캐시에서 꺼냄). 없으면 null
  MonthlyMealPlan? get currentPlan {
    final key = _monthKey(currentYear, currentMonth);
    return cache[key];
  }

  CalendarState copyWith({
    int? currentYear,
    int? currentMonth,
    Map<String, MonthlyMealPlan>? cache,
    bool? isLoading,
    Object? error,
  }) {
    return CalendarState(
      currentYear: currentYear ?? this.currentYear,
      currentMonth: currentMonth ?? this.currentMonth,
      cache: cache ?? this.cache,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
    );
  }

  static String _monthKey(int year, int month) {
    return '${year.toString().padLeft(4, '0')}-${month.toString().padLeft(2, '0')}';
  }
}

// Notifier 클래스
class CalendarNotifier extends StateNotifier<CalendarState> {
  final CalendarRepository _repository;

  CalendarNotifier(this._repository)
    : super(
        CalendarState(
          currentYear: DateTime.now().year,
          currentMonth: DateTime.now().month,
        ),
      ) {
    _loadIfNeeded(state.currentYear, state.currentMonth);
  }

  // 이전 달로 이동
  void goToPrevMonth() {
    final (y, m) = _prevMonth(state.currentYear, state.currentMonth);
    state = state.copyWith(currentYear: y, currentMonth: m);
    _loadIfNeeded(y, m);
  }

  // 다음 달로 이동
  void goToNextMonth() {
    final (y, m) = _nextMonth(state.currentYear, state.currentMonth);
    state = state.copyWith(currentYear: y, currentMonth: m);
    _loadIfNeeded(y, m);
  }

  // 캐시에 없으면 API 호출
  Future<void> _loadIfNeeded(int year, int month) async {
    final key = CalendarState._monthKey(year, month);
    if (state.cache.containsKey(key)) return; // 이미 있으면 스킵

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

  // 두 날짜의 식단을 교환한다 (드래그-앤-드롭으로 from을 to에 떨어뜨림).
  // 성공 시 백엔드 응답으로 받은 두 날짜만 현재 달 캐시에서 갈아끼운다(월 재요청 X).
  // 같은 쌍으로 다시 호출하면 원래대로 되돌아간다 → 실행취소(Undo)에 그대로 재사용.
  // 실패 시 예외를 다시 던져 화면에서 안내한다.
  Future<void> swapDates(DateTime from, DateTime to) async {
    if (_sameYmd(from, to)) return;
    final swapped = await _repository.swapDays(from, to);
    if (!mounted) return;

    final key = CalendarState._monthKey(state.currentYear, state.currentMonth);
    final plan = state.cache[key];
    if (plan == null) return;

    final updatedDays = [
      for (final d in plan.days)
        swapped.firstWhere(
          (s) => _sameYmd(s.date, d.date),
          orElse: () => d,
        ),
    ];
    final newCache = Map<String, MonthlyMealPlan>.from(state.cache);
    newCache[key] = plan.copyWith(days: updatedDays);
    state = state.copyWith(cache: newCache);
  }

  (int, int) _prevMonth(int y, int m) {
    if (m == 1) return (y - 1, 12);
    return (y, m - 1);
  }

  (int, int) _nextMonth(int y, int m) {
    if (m == 12) return (y + 1, 1);
    return (y, m + 1);
  }
}

// 연/월/일이 같은 날짜인지 비교 (시각 무시)
bool _sameYmd(DateTime a, DateTime b) =>
    a.year == b.year && a.month == b.month && a.day == b.day;

// StateNotifierProvider
final calendarProvider =
    StateNotifierProvider.autoDispose<CalendarNotifier, CalendarState>(
      (ref) => CalendarNotifier(ref.watch(calendarRepositoryProvider)),
    );