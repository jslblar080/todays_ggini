import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../../../../core/network/api_client.dart';
import '../../domain/persona_input.dart';

// ── 추천 페르소나 모델 ──────────────────────────────────────────

class RecommendedPersona {
  const RecommendedPersona({
    required this.personaId,
    required this.description,
    required this.summary,
    required this.rank,
  });

  final String personaId;
  final String description; // "가성비 자취생" 같은 이름
  final String summary;     // 상세 설명
  final int rank;

  String get name => description;

  factory RecommendedPersona.fromJson(Map<String, dynamic> json) {
    return RecommendedPersona(
      personaId: json['persona_id'] as String,
      description: json['description'] as String,
      summary: json['summary'] as String,
      rank: json['rank'] as int,
    );
  }
}

// ── 입력 상태 ──────────────────────────────────────────────────

class PersonaSelectNotifier extends StateNotifier<PersonaInput> {
  PersonaSelectNotifier() : super(const PersonaInput());

  void initializeWith(PersonaInput input) {
    state = input;
  }

  void setHouseholdType(String v) =>
      state = state.copyWith(householdType: v);

  void setMonthlyBudget(int v) =>
      state = state.copyWith(monthlyBudget: v);

  void setMealsPerDay(int v) =>
      state = state.copyWith(mealsPerDay: v);

  void setPurpose(List<String> v) =>
      state = state.copyWith(purpose: v);

  void setPersona(String name, String id) => state = state.copyWith(
        personaName: name,
        personaId: id,
      );

  void setFamilyMembers(List<FamilyMember> v) =>
      state = state.copyWith(familyMembers: v);

  void setFamilyCount(int v) =>
      state = state.copyWith(familyCount: v);

  void setActivityLevel(int v) =>
      state = state.copyWith(activityLevel: v);
}

final personaSelectProvider =
    StateNotifierProvider<PersonaSelectNotifier, PersonaInput>(
  (ref) => PersonaSelectNotifier(),
);

// ── AI 추천 페르소나 - 실제 API 호출 ────────────────────────────

final recommendedPersonasProvider =
    FutureProvider.autoDispose<List<RecommendedPersona>>((ref) async {
  final input = ref.read(personaSelectProvider);
  final dio = ref.watch(dioProvider);

  final response = await dio.post('/user/recommend-personas', data: {
    'household_type': input.householdType,
    'family_count': input.familyCount,
    'monthly_budget': input.monthlyBudget,
    'meals_per_day': input.mealsPerDay,
    'purpose': input.purpose,
    'family_members': input.familyMembers.map((m) => m.toJson()).toList(),
  });

  final data = response.data as Map<String, dynamic>;
  final personas = (data['recommended_personas'] as List)
      .map((e) => RecommendedPersona.fromJson(e as Map<String, dynamic>))
      .toList();

  personas.sort((a, b) => a.rank.compareTo(b.rank));
  return personas;
});

// ── PUT /api/v1/user/persona-setting ──────────────────────────

final submitPersonaProvider =
    FutureProvider.autoDispose.family<void, PersonaInput>((ref, input) async {
  final dio = ref.watch(dioProvider);
  await dio.put('/user/persona-setting', data: input.toJson());
});