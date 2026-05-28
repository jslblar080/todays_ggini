class MyProfile {
  final int id;
  final String provider;
  final String? nickname;
  final String? email;
  final String? imageUrl;
  final bool isGuest;
  final bool isOnboarded;
  final int personaId;
  final int mealsPerDay;
  final List<String> purpose;
  final int monthlyBudget;
  final int cookingSkill;
  final List<String> preferredIngredients;
  final List<String> preferredCategories;
  final String diversityLevel;
  final List<String> excludedIngredients;
  final String? selectedStyleId;

  const MyProfile({
    required this.id,
    required this.provider,
    this.nickname,
    this.email,
    this.imageUrl,
    required this.isGuest,
    required this.isOnboarded,
    required this.personaId,
    required this.mealsPerDay,
    required this.purpose,
    required this.monthlyBudget,
    required this.cookingSkill,
    required this.preferredIngredients,
    required this.preferredCategories,
    required this.diversityLevel,
    required this.excludedIngredients,
    this.selectedStyleId,
  });

  factory MyProfile.fromJson(Map<String, dynamic> json) {
    return MyProfile(
      id: json['id'] as int,
      provider: json['provider'] as String,
      nickname: json['nickname'] as String?,
      email: json['email'] as String?,
      imageUrl: json['image_url'] as String?,
      isGuest: json['is_guest'] as bool,
      isOnboarded: json['is_onboarded'] as bool,
      personaId: json['persona_id'] as int,
      mealsPerDay: json['meals_per_day'] as int,
      purpose: List<String>.from(json['purpose'] as List),
      monthlyBudget: json['monthly_budget'] as int,
      cookingSkill: json['cooking_skill'] as int,
      preferredIngredients: List<String>.from(json['preferred_ingredients'] as List),
      preferredCategories: List<String>.from(json['preferred_categories'] as List),
      diversityLevel: json['diversity_level'] as String,
      excludedIngredients: List<String>.from(json['excluded_ingredients'] as List),
      selectedStyleId: json['selected_style_id'] as String?,
    );
  }
}