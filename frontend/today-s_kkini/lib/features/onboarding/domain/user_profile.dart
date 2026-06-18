import 'persona.dart';

class UserProfile {
  const UserProfile({
    required this.persona,
    required this.foods,
    required this.ingredient,
    required this.allergies,
    required this.diversity,
    required this.cookingSkill,
    this.selectedStyleId = '',
  });

  final Persona persona;
  final List<String> foods;
  final List<String> ingredient;
  final List<String> allergies;
  final String diversity;
  final int cookingSkill;
  final String selectedStyleId;

  Map<String, dynamic> toJson() => {
    'preferred_categories': foods,
    'preferred_ingredients': ingredient,
    'excluded_ingredients': allergies,
    'diversity_level': diversity,
    'cooking_skill': cookingSkill,
    'selected_style_id': selectedStyleId,
  };

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
    persona: Persona.fromId(json['persona_id'] as int? ?? 1),
    foods: List<String>.from(json['preferred_categories'] as List? ?? []),
    ingredient: List<String>.from(json['preferred_ingredients'] as List? ?? []),
    allergies: List<String>.from(json['excluded_ingredients'] as List? ?? []),
    diversity: json['diversity_level'] as String? ?? '보통',
    cookingSkill: json['cooking_skill'] as int? ?? 3,
    selectedStyleId: json['selected_style_id'] as String? ?? '',
  );

  UserProfile copyWith({
    Persona? persona,
    List<String>? foods,
    List<String>? ingredient,
    List<String>? allergies,
    String? diversity,
    int? cookingSkill,
    String? selectedStyleId,
  }) {
    return UserProfile(
      persona: persona ?? this.persona,
      foods: foods ?? this.foods,
      ingredient: ingredient ?? this.ingredient,
      allergies: allergies ?? this.allergies,
      diversity: diversity ?? this.diversity,
      cookingSkill: cookingSkill ?? this.cookingSkill,
      selectedStyleId: selectedStyleId ?? this.selectedStyleId,
    );
  }
}