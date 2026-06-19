import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../../../../core/network/api_client.dart';
import '../../../home/domain/daily_meal_plan.dart';
import '../../data/menu_change_repository.dart';
import '../../domain/menu_alternatives.dart';

final menuChangeRepositoryProvider = Provider<MenuChangeRepository>((ref) {
  return MenuChangeRepository(ref.watch(dioProvider));
});

typedef MenuChangeArgs = ({String mealId, DateTime date, int slot});

class MenuChangeState {
  final MenuAlternatives? data;
  final bool isLoading;
  final bool isChanging; // PUT 진행 중
  final String? changingMealId; // 어떤 대안 메뉴가 변경 중인지
  final Object? error;

  const MenuChangeState({
    this.data,
    this.isLoading = false,
    this.isChanging = false,
    this.changingMealId,
    this.error,
  });

  MenuChangeState copyWith({
    MenuAlternatives? data,
    bool? isLoading,
    bool? isChanging,
    String? changingMealId,
    Object? error,
    bool clearError = false,
    bool clearChangingMealId = false,
  }) {
    return MenuChangeState(
      data: data ?? this.data,
      isLoading: isLoading ?? this.isLoading,
      isChanging: isChanging ?? this.isChanging,
      changingMealId: clearChangingMealId
          ? null
          : (changingMealId ?? this.changingMealId),
      error: clearError ? null : (error ?? this.error),
    );
  }
}

class MenuChangeNotifier extends StateNotifier<MenuChangeState> {
  final MenuChangeRepository _repository;
  final String _mealId;
  final DateTime _date;
  final int _slot;

  MenuChangeNotifier(this._repository, this._mealId, this._date, this._slot)
    : super(const MenuChangeState(isLoading: true)) {
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await _repository.fetchAlternatives(
        currentMealId: _mealId,
        targetDate: _date,
      );
      if (!mounted) return;
      state = state.copyWith(data: data, isLoading: false);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e, isLoading: false);
    }
  }

  Future<DailyMealPlan?> applyChange({
    required DailyMealPlan currentPlan,
    required AlternativeMeal chosenAlternative,
  }) async {
    state = state.copyWith(
      isChanging: true,
      changingMealId: chosenAlternative.mealId,
      clearError: true,
    );
    try {
      await _repository.changeMenu(
        date: _date,
        slot: _slot,
        newMenuId: chosenAlternative.mealId,
      );
      if (!mounted) return null;

      final newPlan = _buildLocalPlan(currentPlan, chosenAlternative);
      state = state.copyWith(isChanging: false, clearChangingMealId: true);
      return newPlan;
    } catch (e) {
      if (!mounted) return null;
      state = state.copyWith(
        isChanging: false,
        clearChangingMealId: true,
        error: e,
      );
      return null;
    }
  }

  DailyMealPlan _buildLocalPlan(DailyMealPlan current, AlternativeMeal alt) {
    final newSlotMeal = MealSlotSummary(
      slot: _slot,
      mealId: alt.mealId,
      menuName: alt.menuName,
      calories: alt.calories,
      price: alt.price,
      imageUrl: alt.imageUrl,
    );
    final newMeals =
        current.meals.map((m) => m.slot == _slot ? newSlotMeal : m).toList();
    final newCalories = newMeals.fold<int>(0, (sum, m) => sum + m.calories);
    final newPrice = newMeals.fold<int>(0, (sum, m) => sum + m.price);
    return DailyMealPlan(
      date: current.date,
      caloriesPerDay: newCalories,
      pricePerDay: newPrice,
      meals: newMeals,
    );
  }
}

final menuChangeProvider = StateNotifierProvider.autoDispose
    .family<MenuChangeNotifier, MenuChangeState, MenuChangeArgs>((ref, args) {
      final repository = ref.watch(menuChangeRepositoryProvider);
      return MenuChangeNotifier(repository, args.mealId, args.date, args.slot);
    });