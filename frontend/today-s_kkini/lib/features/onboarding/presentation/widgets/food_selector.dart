import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class FoodSelector extends StatelessWidget {
  final List<String> selectedFoods;
  final ValueChanged<List<String>> onChanged;

  const FoodSelector({
    super.key,
    required this.selectedFoods,
    required this.onChanged,
  });

  static const List<(String, String)> _foods = [
    ('한식', 'assets/images/onboarding/flavor_k.png'),
    ('일식', 'assets/images/onboarding/flavor_j.png'),
    ('중식', 'assets/images/onboarding/flavor_c.png'),
    ('양식', 'assets/images/onboarding/flavor_e.png'),
    ('분식', 'assets/images/onboarding/flavor_b.png'),
    ('디저트', 'assets/images/onboarding/flavor_d.png'),
    ('샐러드/건강식', 'assets/images/onboarding/flavor_s.png'),
    ('다 좋아요', 'assets/images/onboarding/flavor_all.png'),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: _foods.map((food) {
        final isSelected = selectedFoods.contains(food.$1);
        return GestureDetector(
          onTap: () {
            final newList = List<String>.from(selectedFoods);
            isSelected ? newList.remove(food.$1) : newList.add(food.$1);
            onChanged(newList);
          },
          child: Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 20),
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
                  food.$2,
                  width: 32,
                  height: 32,
                  fit: BoxFit.contain,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    food.$1,
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