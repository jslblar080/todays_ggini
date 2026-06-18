import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../../../../core/network/api_client.dart';
import '../../data/home_repository.dart';
import '../../domain/daily_meal_plan.dart';
import '../../domain/menu_detail.dart';

// Repository Provider: Provider<Repository 클래스>
// 앱 전역에서 사용하는 dioProvider를 가져와
// Dio 객체를 주입해 Repository 객체를 생성
final homeRepositoryProvider = Provider<HomeRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return HomeRepository(dio);
});

// State 클래스
class HomeState {
  final DailyMealPlan? dailyPlan; // 하루 식단 요약 (slot 1~N)
  final int selectedSlot; // 현재 선택된 slot (1부터 시작)
  final MenuDetail? selectedMenu; // 선택된 slot의 상세 정보
  final bool isLoadingMenu; // 메뉴 상세 로딩 중 (탭 전환 시 표시)
  final Object? error;
  final DateTime? selectedDate; 

  const HomeState({
    this.dailyPlan,
    this.selectedSlot = 1,
    this.selectedMenu,
    this.isLoadingMenu = false,
    this.error,
    this.selectedDate,
  });

  // 기존 값을 베이스로 인자로 받은 것만 바꾼 새 상태
  HomeState copyWith({
    DailyMealPlan? dailyPlan,
    int? selectedSlot,
    MenuDetail? selectedMenu,
    bool? isLoadingMenu,
    Object? error,
    DateTime? selectedDate,
  }) {
    return HomeState(
      // 인자로 받은 바뀐 값이면 ?? 왼쪽으로, 인자를 받지 않은 null이면 오른쪽으로
      dailyPlan: dailyPlan ?? this.dailyPlan,
      selectedSlot: selectedSlot ?? this.selectedSlot,
      selectedMenu: selectedMenu ?? this.selectedMenu,
      isLoadingMenu: isLoadingMenu ?? this.isLoadingMenu,
      error: error ?? this.error,
      selectedDate: selectedDate ?? this.selectedDate,
    );
  }
}

// Notifier 클래스: StateNotifier<State 클래스> 상속
// 화면의 비즈니스 로직(API 호출, 단계별 진행)을 담당
// state 변수와 mounted 변수를 사용 가능
class HomeNotifier extends StateNotifier<HomeState> {
  final HomeRepository _repository;

  HomeNotifier(this._repository) : super(const HomeState()) {
    _loadToday();
  }

  // 초기 진입: 오늘 날짜의 식단 + 현재 시간대에 맞는 slot의 상세 정보를 가져옴
  Future<void> _loadToday() async {
    await loadDate(DateTime.now());
  }

  // 사용자가 다른 slot 탭을 누름
  Future<void> selectSlot(int slot) async {
    if (state.dailyPlan == null) return;
    if (state.selectedSlot == slot && state.selectedMenu != null) return;

    state = state.copyWith(selectedSlot: slot, isLoadingMenu: true);

    try {
      final meal = state.dailyPlan!.meals.firstWhere((m) => m.slot == slot);
      final menu = await _repository.fetchMenuDetail(
        mealDate: state.dailyPlan!.date,
        mealId: meal.mealId,
      );
      if (!mounted) return;
      state = state.copyWith(selectedMenu: menu, isLoadingMenu: false);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e, isLoadingMenu: false);
    }
  }

  Future<void> loadDate(DateTime date) async {
    state = state.copyWith(
      dailyPlan: null,
      selectedMenu: null,
      isLoadingMenu: true,
      error: null,
      selectedDate: date,
    );
    try {
      final plan = await _repository.fetchDailyMealPlan(date);
      if (!mounted) return;

      final defaultSlot = _pickDefaultSlot(plan.meals.length);
      state = state.copyWith(
        dailyPlan: plan,
        selectedSlot: defaultSlot,
        isLoadingMenu: true,
      );

      final defaultMeal = plan.meals.firstWhere((m) => m.slot == defaultSlot);
      final menu = await _repository.fetchMenuDetail(
        mealDate: date,
        mealId: defaultMeal.mealId,
      );
      if (!mounted) return;
      state = state.copyWith(selectedMenu: menu, isLoadingMenu: false);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e, isLoadingMenu: false);
    }
  }

  // 현재 시간대에 맞는 디폴트 slot 선택
  //
  // 슬롯 수에 따라 임의 분할:
  //   1끼 → 항상 slot 1
  //   2끼 → 점심 기준(12시) 이전이면 1, 이후면 2
  //   3끼 → 아침/점심/저녁
  //   4끼 → 아침/점심/저녁/야식
  //   5끼 → 아침/간식/점심/저녁/야식
  //
  // TODO: 백엔드 응답에 slot별 시간 범위(start_hour, end_hour 등)가 들어오면
  //       그 정보로 분기하도록 변경
  int _pickDefaultSlot(int slotCount) {
    final hour = DateTime.now().hour;
    if (slotCount <= 1) return 1;

    switch (slotCount) {
      case 2:
        return hour < 12 ? 1 : 2;
      case 3:
        if (hour < 11) return 1;
        if (hour < 17) return 2;
        return 3;
      case 4:
        if (hour < 11) return 1;
        if (hour < 17) return 2;
        if (hour < 21) return 3;
        return 4;
      case 5:
        if (hour < 10) return 1;
        if (hour < 12) return 2;
        if (hour < 17) return 3;
        if (hour < 21) return 4;
        return 5;
      default:
        return 1;
    }
  }
}

// StateNotifierProvider: Notifier가 State를 관리함을 명시
// StateNotifierProvider.autoDispose<Notifier 클래스, State 클래스>
// autoDispose: 화면 떠나면 Notifier도 정리되어 다음 진입 시 처음부터 다시 시작
final homeProvider = StateNotifierProvider.autoDispose<HomeNotifier, HomeState>(
  (ref) => HomeNotifier(ref.watch(homeRepositoryProvider)),
);
