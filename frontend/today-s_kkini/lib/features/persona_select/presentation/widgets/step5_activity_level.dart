import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class Step5ActivityLevel extends StatelessWidget {
  const Step5ActivityLevel({
    super.key,
    required this.selected,
    required this.onChanged,
  });

  final int selected;
  final ValueChanged<int> onChanged;

  static const _options = [
    (1, '거의 앉아서 생활해요', '운동은 거의 하지 않아요', 'assets/images/onboarding/activity_1.png'),
    (2, '가벼운 활동을 해요', '주 1~3회 가볍게 움직여요', 'assets/images/onboarding/activity_2.png'),
    (3, '보통 활동을 해요', '주 3~5회 운동해요', 'assets/images/onboarding/activity_3.png'),
    (4, '활동량이 많아요', '주 6회 이상 운동해요', 'assets/images/onboarding/activity_4.png'),
  ];

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(
            '평소 활동량은 어느 정도인가요?',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                  fontFamily: 'MemomentKkukkukk',
                  fontSize: 34,
                ),
          ),
          const SizedBox(height: 24),
          ..._options.map((option) {
            final isSelected = selected == option.$1;
            return GestureDetector(
              onTap: () => onChanged(option.$1),
              child: Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
                decoration: BoxDecoration(
                  color: isSelected ? AppColors.primaryLight : Colors.white,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: isSelected ? AppColors.primary : AppColors.gray,
                    width: 2,
                  ),
                ),
                child: Row(
                  children: [
                    Image.asset(
                      option.$4,
                      width: 32,
                      height: 32,
                      fit: BoxFit.contain,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Text(
                            option.$2,
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                  color: isSelected
                                      ? AppColors.primary
                                      : AppColors.textPrimary,
                                ),
                          ),
                          Text(
                            option.$3,
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: isSelected
                                      ? AppColors.primary
                                      : AppColors.textSecondary,
                                ),
                          ),
                        ],
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