class FamilyMember {
  const FamilyMember({
    required this.nickname,
    required this.gender,
    required this.age,
    required this.height,
    required this.weight,
  });

  final String nickname;
  final String gender;
  final int age;
  final double height;
  final double weight;

  FamilyMember copyWith({
    String? nickname,
    String? gender,
    int? age,
    double? height,
    double? weight,
  }) {
    return FamilyMember(
      nickname: nickname ?? this.nickname,
      gender: gender ?? this.gender,
      age: age ?? this.age,
      height: height ?? this.height,
      weight: weight ?? this.weight,
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

class PersonaInput {
  const PersonaInput({
    this.householdType = '',
    this.monthlyBudget = 0,
    this.mealsPerDay = 3,
    this.purpose = const [],
    this.personaName,
    this.familyMembers = const [],
    this.familyCount = 1,
    this.activityLevel = 0,
  });

  final String householdType;
  final int monthlyBudget;
  final int mealsPerDay;
  final List<String> purpose;
  final String? personaName;
  final List<FamilyMember> familyMembers;
  final int familyCount;
  final int activityLevel;

  PersonaInput copyWith({
    String? householdType,
    int? monthlyBudget,
    int? mealsPerDay,
    List<String>? purpose,
    String? personaName,
    List<FamilyMember>? familyMembers,
    int? familyCount,
    int? activityLevel
  }) {
    return PersonaInput(
      householdType: householdType ?? this.householdType,
      monthlyBudget: monthlyBudget ?? this.monthlyBudget,
      mealsPerDay: mealsPerDay ?? this.mealsPerDay,
      purpose: purpose ?? this.purpose,
      personaName: personaName ?? this.personaName,
      familyMembers: familyMembers ?? this.familyMembers,
      familyCount: familyCount ?? this.familyCount,
      activityLevel: activityLevel ?? this.activityLevel,
    );
  }

  Map<String, dynamic> toJson() => {
        'household_type': householdType,
        'monthly_budget': monthlyBudget,
        'meals_per_day': mealsPerDay,
        'purpose': purpose,
        'persona_name': personaName,
        'family_members': familyMembers.map((m) => m.toJson()).toList(),
        'activity_level': activityLevel,
        'family_count': familyCount,
      };
}