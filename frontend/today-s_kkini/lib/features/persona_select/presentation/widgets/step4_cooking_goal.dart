import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';

class Step4CookingGoal extends StatelessWidget {
  const Step4CookingGoal({
    super.key,
    required this.selected,
    required this.onChanged,
  });

  final List<String> selected;
  final ValueChanged<List<String>> onChanged;

  static const _options = [
    ('식비 절약', 'assets/images/onboarding/goal_money.png'),
    ('영양 균형', 'assets/images/onboarding/goal_nutrition.png'),
    ('다이어트', 'assets/images/onboarding/goal_diet.png'),
    ('고단백', 'assets/images/onboarding/goal_protein.png'),
    ('간편식', 'assets/images/onboarding/goal_conv.png'),
    ('맛 중심', 'assets/images/onboarding/goal_flavor.png'),
  ];

  static const _maxSelect = 3;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(
            '요리 목적을 선택해 주세요',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                  fontFamily: 'MemomentKkukkukk',
                  fontSize: 34,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            '최대 ${_maxSelect}개 항목까지 선택 가능합니다.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 24),
          ..._options.map((option) {
            final isSelected = selected.contains(option.$1);
            final isDisabled = !isSelected && selected.length >= _maxSelect;
            return GestureDetector(
              onTap: isDisabled
                  ? null
                  : () {
                      final updated = List<String>.from(selected);
                      if (isSelected) {
                        updated.remove(option.$1);
                      } else {
                        updated.add(option.$1);
                      }
                      onChanged(updated);
                    },
              child: Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.symmetric(
                    vertical: 10, horizontal: 20),
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
                      option.$2,
                      width: 32,
                      height: 32,
                      fit: BoxFit.contain,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        option.$1,
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}