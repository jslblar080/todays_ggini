import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../../../../core/network/api_client.dart';
import '../../data/onboarding_remote_data_source.dart';
import '../../data/onboarding_repository.dart';
import '../../domain/persona.dart';
import '../../domain/user_profile.dart';

// diversity int → String 변환 헬퍼
String diversityToString(int value) {
  if (value == 1) return '낮음';
  if (value == 2) return '보통';
  return '높음';
}

// diversity String → int 변환 헬퍼 (마이페이지 프로필 prefill용)
int diversityToInt(String value) {
  switch (value) {
    case '낮음':
      return 1;
    case '보통':
      return 2;
    case '높음':
      return 3;
    default:
      return 2;
  }
}

// ─────────────────────────────────────────────────────────────
// Data layer providers
// ─────────────────────────────────────────────────────────────

final _onboardingRemoteProvider = Provider<OnboardingRemoteDataSource>((ref) {
  return OnboardingRemoteDataSource(ref.watch(dioProvider));
});

final onboardingRepositoryProvider = Provider<OnboardingRepository>((ref) {
  return OnboardingRepository(ref.watch(_onboardingRemoteProvider));
});

// ─────────────────────────────────────────────────────────────
// 선택된 페르소나
// ─────────────────────────────────────────────────────────────

final selectedPersonaProvider = StateProvider<Persona>((ref) {
  return Persona.singleValue;
});

// ─────────────────────────────────────────────────────────────
// 슬라이더 입력값 draft state
// ─────────────────────────────────────────────────────────────

class OnboardingDraft {
  const OnboardingDraft({
    this.foods = const [],
    this.ingredient = const [],
    this.allergies = const [],
    this.diversity = 3,
    this.cookingSkill = 3,
    this.selectedStyleId = '',
  });

  final List<String> foods;
  final List<String> ingredient;
  final List<String> allergies;
  final int diversity;
  final int cookingSkill;
  final String selectedStyleId;

  OnboardingDraft copyWith({
    List<String>? foods,
    List<String>? ingredient,
    List<String>? allergies,
    int? diversity,
    int? cookingSkill,
    String? selectedStyleId,
  }) {
    return OnboardingDraft(
      foods: foods ?? this.foods,
      ingredient: ingredient ?? this.ingredient,
      allergies: allergies ?? this.allergies,
      diversity: diversity ?? this.diversity,
      cookingSkill: cookingSkill ?? this.cookingSkill,
      selectedStyleId: selectedStyleId ?? this.selectedStyleId,
    );
  }
}

class OnboardingNotifier extends StateNotifier<OnboardingDraft> {
  OnboardingNotifier(this._repo, this._readPersona)
      : super(const OnboardingDraft());

  final OnboardingRepository _repo;
  final Persona Function() _readPersona;

  void initializeWith(OnboardingDraft draft) => state = draft;

  void setFoods(List<String> v) => state = state.copyWith(foods: v);
  void setIngredient(List<String> v) => state = state.copyWith(ingredient: v);
  void setAllergies(List<String> v) => state = state.copyWith(allergies: v);
  void setDiversity(int v) => state = state.copyWith(diversity: v);
  void setCookingSkill(int v) => state = state.copyWith(cookingSkill: v);
  void setSelectedStyleId(String v) =>
      state = state.copyWith(selectedStyleId: v);

  Future<void> submit() async {
    final profile = UserProfile(
      persona: _readPersona(),
      foods: state.foods,
      ingredient: state.ingredient,
      allergies: state.allergies,
      diversity: diversityToString(state.diversity),
      cookingSkill: state.cookingSkill,
      selectedStyleId: state.selectedStyleId,
    );
    await _repo.saveProfile(profile);
  }
}

final onboardingNotifierProvider =
    StateNotifierProvider<OnboardingNotifier, OnboardingDraft>((ref) {
      return OnboardingNotifier(
        ref.watch(onboardingRepositoryProvider),
        () => ref.read(selectedPersonaProvider),
      );
    });

// ─────────────────────────────────────────────────────────────
// submit 결과
// ─────────────────────────────────────────────────────────────

final submitOnboardingProvider = StateProvider<AsyncValue<void>?>(
  (ref) => null,
);