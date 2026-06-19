import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../domain/meal_style.dart';
import 'package:auto_size_text/auto_size_text.dart';

Color _getBarColor(int value) {
  if (value <= 3) return Colors.red;
  if (value <= 6) return Colors.green;
  return Colors.blue;
}

class MealStyleCard extends StatelessWidget {
  final MealStyle style;
  final bool isSelected;
  final VoidCallback onTap;

  const MealStyleCard({
    super.key,
    required this.style,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primaryLight : Colors.white,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: isSelected ? AppColors.primary : AppColors.gray,
            width: 3,
          ),
        ),
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: isSelected ? AppColors.primary : AppColors.grayLight,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                style.styleName,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: isSelected ? Colors.white : AppColors.textPrimary,
                    ),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              crossAxisAlignment: CrossAxisAlignment.center, // start → center
              children: [
                // 왼쪽: 메뉴 목록
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: style.representativeMenus.map((meal) {
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 2),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.restaurant,
                              size: 18,
                              color: AppColors.textSecondary,
                            ),
                            const SizedBox(width: 4),
                            Expanded(
                              child: AutoSizeText(
                                meal,
                                maxLines: 1,
                                minFontSize: 10,
                                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                      color: AppColors.textPrimary,
                                    ),
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
                const SizedBox(width: 12),
                // 오른쪽: 점수 바
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: style.displayScores.entries.map((e) => Padding(
                        padding: const EdgeInsets.symmetric(vertical: 3),
                        child: Row(
                          children: [
                            SizedBox(
                              width: 60,
                              child: Text(
                                style.displayLabels[e.key] ?? e.key,
                                style: Theme.of(context)
                                    .textTheme
                                    .bodySmall
                                    ?.copyWith(color: AppColors.textPrimary),
                              ),
                            ),
                            const SizedBox(width: 4),
                            Container(
                              width: (e.value * 8.0).clamp(0.0, 80.0),
                              height: 10,
                              decoration: BoxDecoration(
                                color: _getBarColor(e.value),
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(
                              '${e.value}',
                              style: Theme.of(context)
                                  .textTheme
                                  .bodySmall
                                  ?.copyWith(color: AppColors.textPrimary),
                            ),
                          ],
                        ),
                      )).toList(),
                ),
              ],
            ),
            
            const SizedBox(height: 8),
            Text(
              style.summaryComment,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.primary,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}