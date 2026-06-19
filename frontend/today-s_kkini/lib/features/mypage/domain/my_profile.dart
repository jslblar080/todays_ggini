class FamilyMemberInfo {
  final String nickname;
  final String gender;
  final int age;
  final double height;
  final double weight;

  const FamilyMemberInfo({
    required this.nickname,
    required this.gender,
    required this.age,
    required this.height,
    required this.weight,
  });

  factory FamilyMemberInfo.fromJson(Map<String, dynamic> json) {
    return FamilyMemberInfo(
      nickname: json['nickname'] as String? ?? '',
      gender: json['gender'] as String? ?? '',
      age: json['age'] as int? ?? 0,
      height: (json['height'] as num?)?.toDouble() ?? 0,
      weight: (json['weight'] as num?)?.toDouble() ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
        'nickname': nickname,
        'gender': gender,
        'age': age,
        'height': height,
        'weight': weight,
      };
}

class MyProfile {
  final int id;
  final String provider;
  final String? nickname;
  final String? email;
  final String? imageUrl;
  final bool isGuest;
  final bool isOnboarded;
  final List<String> markets;
  final List<FamilyMemberInfo> familyMembers;

  // persona_setting
  final String householdType;
  final int familyCount;
  final int monthlyBudget;
  final int mealsPerDay;
  final List<String> purpose;
  final String? personaName;
  final String? personaId;
  final int activityLevel;

  // onboarding_setting
  final List<String> preferredCategories;
  final List<String> preferredIngredients;
  final List<String> excludedIngredients;
  final int cookingSkill;
  final String diversityLevel;
  final String? selectedStyleId;

  const MyProfile({
    required this.id,
    required this.provider,
    this.nickname,
    this.email,
    this.imageUrl,
    required this.isGuest,
    required this.isOnboarded,
    required this.markets,
    required this.familyMembers,
    required this.householdType,
    required this.familyCount,
    required this.monthlyBudget,
    required this.mealsPerDay,
    required this.purpose,
    this.personaName,
    this.personaId,
    required this.activityLevel,
    required this.preferredCategories,
    required this.preferredIngredients,
    required this.excludedIngredients,
    required this.cookingSkill,
    required this.diversityLevel,
    this.selectedStyleId,
  });

  factory MyProfile.fromJson(Map<String, dynamic> json) {
    final personaSetting =
        json['persona_setting'] as Map<String, dynamic>? ?? {};
    final onboardingSetting =
        json['onboarding_setting'] as Map<String, dynamic>? ?? {};

    return MyProfile(
      id: json['id'] as int,
      provider: json['provider'] as String,
      nickname: json['nickname'] as String?,
      email: json['email'] as String?,
      imageUrl: json['image_url'] as String?,
      isGuest: json['is_guest'] as bool,
      isOnboarded: json['is_onboarded'] as bool,
      markets: List<String>.from(json['markets'] ?? ['쿠팡', '컬리', '네이버']),
      familyMembers: (json['family_members'] as List<dynamic>? ?? [])
          .map((m) => FamilyMemberInfo.fromJson(m as Map<String, dynamic>))
          .toList(),
      householdType: personaSetting['household_type'] as String? ?? '1인 가구',
      familyCount: personaSetting['family_count'] as int? ?? 1,
      monthlyBudget: personaSetting['monthly_budget'] as int? ?? 300000,
      mealsPerDay: personaSetting['meals_per_day'] as int? ?? 3,
      purpose: List<String>.from(personaSetting['purpose'] ?? []),
      personaName: personaSetting['persona_name'] as String?,
      personaId: personaSetting['persona_id'] as String?,
      activityLevel: personaSetting['activity_level'] as int? ?? 0,
      preferredCategories:
          List<String>.from(onboardingSetting['preferred_categories'] ?? []),
      preferredIngredients:
          List<String>.from(onboardingSetting['preferred_ingredients'] ?? []),
      excludedIngredients:
          List<String>.from(onboardingSetting['excluded_ingredients'] ?? []),
      cookingSkill: onboardingSetting['cooking_skill'] as int? ?? 3,
      diversityLevel: onboardingSetting['diversity_level'] as String? ?? '보통',
      selectedStyleId: onboardingSetting['selected_style_id'] as String?,
    );
  }
}