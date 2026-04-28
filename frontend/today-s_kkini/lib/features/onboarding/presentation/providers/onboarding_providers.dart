import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../../../../core/network/api_client.dart';
import '../../data/onboarding_remote_data_source.dart';
import '../../data/onboarding_repository.dart';
import '../../domain/persona.dart';
import '../../domain/user_profile.dart';

// ─────────────────────────────────────────────────────────────
// Data layer providers (의존성 주입 체인)
// ─────────────────────────────────────────────────────────────

final _onboardingRemoteProvider = Provider<OnboardingRemoteDataSource>((ref) {
  return OnboardingRemoteDataSource(ref.watch(dioProvider));
});

final onboardingRepositoryProvider = Provider<OnboardingRepository>((ref) {
  return OnboardingRepository(ref.watch(_onboardingRemoteProvider));
});

// ─────────────────────────────────────────────────────────────
// 선택된 페르소나 (persona_select 화면에서 set, onboarding 화면에서 read)
// ─────────────────────────────────────────────────────────────

final selectedPersonaProvider = StateProvider<Persona>((ref) {
  // TODO: persona_select 화면 구현 시 거기서 set.
  // 스타터에선 default 값으로 시작.
  return Persona.singleValue;
});

// ─────────────────────────────────────────────────────────────
// 슬라이더 입력값을 들고 있는 draft state
// ─────────────────────────────────────────────────────────────

class OnboardingDraft {
  const OnboardingDraft({
    this.cookingSkill = 5,
    this.vegMeatPreference = 5,
    this.freshFrozenPreference = 5,
    this.mealStyle = 5,
    this.monthlyBudget = 350000,
  });

  final int cookingSkill;
  final int vegMeatPreference;
  final int freshFrozenPreference;
  final int mealStyle;
  final int monthlyBudget;

  OnboardingDraft copyWith({
    int? cookingSkill,
    int? vegMeatPreference,
    int? freshFrozenPreference,
    int? mealStyle,
    int? monthlyBudget,
  }) {
    return OnboardingDraft(
      cookingSkill: cookingSkill ?? this.cookingSkill,
      vegMeatPreference: vegMeatPreference ?? this.vegMeatPreference,
      freshFrozenPreference:
          freshFrozenPreference ?? this.freshFrozenPreference,
      mealStyle: mealStyle ?? this.mealStyle,
      monthlyBudget: monthlyBudget ?? this.monthlyBudget,
    );
  }
}

class OnboardingNotifier extends StateNotifier<OnboardingDraft> {
  OnboardingNotifier(this._repo, this._readPersona)
    : super(const OnboardingDraft());

  final OnboardingRepository _repo;
  final Persona Function() _readPersona;

  void setCookingSkill(int v) => state = state.copyWith(cookingSkill: v);
  void setVegMeatPreference(int v) =>
      state = state.copyWith(vegMeatPreference: v);
  void setFreshFrozenPreference(int v) =>
      state = state.copyWith(freshFrozenPreference: v);
  void setMealStyle(int v) => state = state.copyWith(mealStyle: v);
  void setMonthlyBudget(int v) => state = state.copyWith(monthlyBudget: v);

  /// 현재 draft 를 서버에 저장.
  Future<UserProfile> submit() async {
    final profile = UserProfile(
      cookingSkill: state.cookingSkill,
      vegMeatPreference: state.vegMeatPreference,
      freshFrozenPreference: state.freshFrozenPreference,
      mealStyle: state.mealStyle,
      monthlyBudget: state.monthlyBudget,
      persona: _readPersona(),
    );
    return _repo.saveProfile(profile);
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
// submit 결과를 별도 AsyncValue 로 노출 (로딩 / 에러 / 성공 처리용)
// ─────────────────────────────────────────────────────────────

final submitOnboardingProvider = StateProvider<AsyncValue<UserProfile>?>(
  (ref) => null,
);
