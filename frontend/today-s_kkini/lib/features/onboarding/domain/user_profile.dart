import 'persona.dart';

/// 온보딩 슬라이더로 입력받는 사용자 프로필.
/// OpenAPI `UserProfile` 스키마와 1:1 매핑.
class UserProfile {
  const UserProfile({
    required this.cookingSkill,
    required this.vegMeatPreference,
    required this.freshFrozenPreference,
    required this.mealStyle,
    required this.monthlyBudget,
    required this.persona,
  });

  /// 1=초보(라면), 10=일류 셰프
  final int cookingSkill;

  /// 1=채소 위주, 10=육류 위주
  final int vegMeatPreference;

  /// 1=냉동·간편식 OK, 10=생식·신선만
  final int freshFrozenPreference;

  /// 1=건강식·일상식, 10=술안주·즐거움
  final int mealStyle;

  /// 한 달 식비 KRW (100,000 ~ 1,000,000)
  final int monthlyBudget;

  final Persona persona;

  Map<String, dynamic> toJson() => {
    'cookingSkill': cookingSkill,
    'vegMeatPreference': vegMeatPreference,
    'freshFrozenPreference': freshFrozenPreference,
    'mealStyle': mealStyle,
    'monthlyBudget': monthlyBudget,
    'persona': persona.code,
  };

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
    cookingSkill: json['cookingSkill'] as int,
    vegMeatPreference: json['vegMeatPreference'] as int,
    freshFrozenPreference: json['freshFrozenPreference'] as int,
    mealStyle: json['mealStyle'] as int,
    monthlyBudget: json['monthlyBudget'] as int,
    persona: Persona.fromCode(json['persona'] as String),
  );

  UserProfile copyWith({
    int? cookingSkill,
    int? vegMeatPreference,
    int? freshFrozenPreference,
    int? mealStyle,
    int? monthlyBudget,
    Persona? persona,
  }) {
    return UserProfile(
      cookingSkill: cookingSkill ?? this.cookingSkill,
      vegMeatPreference: vegMeatPreference ?? this.vegMeatPreference,
      freshFrozenPreference:
          freshFrozenPreference ?? this.freshFrozenPreference,
      mealStyle: mealStyle ?? this.mealStyle,
      monthlyBudget: monthlyBudget ?? this.monthlyBudget,
      persona: persona ?? this.persona,
    );
  }
}
