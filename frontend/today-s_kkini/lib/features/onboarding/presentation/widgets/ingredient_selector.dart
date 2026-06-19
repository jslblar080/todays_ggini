import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class IngredientSelector extends StatelessWidget {
  final List<String> selectedIngredients;
  final ValueChanged<List<String>> onChanged;

  const IngredientSelector({
    super.key,
    required this.selectedIngredients,
    required this.onChanged,
  });

  static const List<(String, String)> _ingredients = [
    ('육류', 'assets/images/onboarding/ing_meat.png'),
    ('해산물류', 'assets/images/onboarding/ing_fish.png'),
    ('채소류', 'assets/images/onboarding/ing_veg.png'),
    ('식물성 단백질류', 'assets/images/onboarding/ing_tofu.png'),
    ('계란 및 유제품류', 'assets/images/onboarding/ing_milk.png'),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: _ingredients.map((ingredient) {
        final isSelected = selectedIngredients.contains(ingredient.$1);
        return GestureDetector(
          onTap: () {
            final newList = List<String>.from(selectedIngredients);
            isSelected
                ? newList.remove(ingredient.$1)
                : newList.add(ingredient.$1);
            onChanged(newList);
          },
          child: Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 12),
            padding:
                const EdgeInsets.symmetric(vertical: 10, horizontal: 20),
            decoration: BoxDecoration(
              color: isSelected ? AppColors.primaryLight : Colors.white,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: isSelected ? AppColors.primary : AppColors.gray,
                width: 3,
              ),
            ),
            child: Row(
              children: [
                Image.asset(
                  ingredient.$2,
                  width: 36,
                  height: 36,
                  fit: BoxFit.contain,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    ingredient.$1,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: isSelected
                              ? AppColors.primary
                              : AppColors.textPrimary,
                        ),
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}