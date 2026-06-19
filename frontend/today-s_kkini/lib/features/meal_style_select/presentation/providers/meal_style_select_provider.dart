import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart'; 

import '../../../../core/network/api_client.dart';
import '../../data/meal_style_select_remote_data_source.dart';
import '../../data/meal_style_select_repository.dart';
import '../../domain/meal_style.dart';

// Data layer providers
final mealStyleSelectRemoteProvider =
    Provider<MealStyleSelectRemoteDataSource>((ref) {
  return MealStyleSelectRemoteDataSource(ref.watch(dioProvider));
});

final mealStyleSelectRepositoryProvider =
    Provider<MealStyleSelectRepository>((ref) {
  return MealStyleSelectRepository(ref.watch(mealStyleSelectRemoteProvider));
});

// 식단 스타일 후보 상태
class MealStyleSelectState {
  final List<MealStyle> candidates;
  final bool isLoading;
  final Object? error;
  final MealStyle? selectedStyle;

  const MealStyleSelectState({
    this.candidates = const [],
    this.isLoading = false,
    this.error,
    this.selectedStyle,
  });

  MealStyleSelectState copyWith({
    List<MealStyle>? candidates,
    bool? isLoading,
    Object? error,
    bool clearError = false,
    MealStyle? selectedStyle,
  }) {
    return MealStyleSelectState(
      candidates: candidates ?? this.candidates,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      selectedStyle: selectedStyle ?? this.selectedStyle,
    );
  }
}

class MealStyleSelectNotifier extends StateNotifier<MealStyleSelectState> {
  MealStyleSelectNotifier(this._repository) : super(const MealStyleSelectState());

  final MealStyleSelectRepository _repository;

  Future<void> fetchCandidates() async {
    state = state.copyWith(isLoading: true, clearError: true);
    
    try {
      final candidates = await _repository.fetchStyleCandidates();
      if (!mounted) return;
      state = state.copyWith(candidates: candidates, isLoading: false);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e, isLoading: false);
    }
  }

  // 스타일 선택
  void selectStyle(MealStyle style) {
    state = state.copyWith(selectedStyle: style);
  }
}

final mealStyleSelectProvider =
    StateNotifierProvider<MealStyleSelectNotifier, MealStyleSelectState>((ref) {
  return MealStyleSelectNotifier(
    ref.watch(mealStyleSelectRepositoryProvider),
  );
});