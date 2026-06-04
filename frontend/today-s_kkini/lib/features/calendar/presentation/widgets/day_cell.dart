import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../domain/monthly_meal_plan.dart';
import '../../../../core/utils/format.dart';

class DayCell extends StatelessWidget {
  final DayEntry? day;
  final VoidCallback? onTap;
  final bool isToday;
  final bool highlight; // 드래그 중 드롭 대상으로 떠 있을 때 강조

  const DayCell({
    super.key,
    this.day,
    this.onTap,
    this.isToday = false,
    this.highlight = false,
  });

  @override
  Widget build(BuildContext context) {
    if (day == null) {
      return const DecoratedBox(
        decoration: BoxDecoration(
          border: Border(
            right: BorderSide(color: AppColors.border, width: 1),
            bottom: BorderSide(color: AppColors.border, width: 1),
          ),
        ),
      );
    }

    final hasPlan = day!.hasMealPlan;

    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(3),
        decoration: BoxDecoration(
          color: highlight
              ? AppColors.primary.withValues(alpha: 0.15)
              : isToday
                  ? AppColors.mypage
                  : Colors.transparent,
          border: highlight
              ? Border.all(color: AppColors.primary, width: 2)
              : const Border(
                  right: BorderSide(color: AppColors.border, width: 1),
                  bottom: BorderSide(color: AppColors.border, width: 1),
                ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${day!.date.day}',
              style: TextStyle(
                fontSize: 11,
                color: isToday
                    ? AppColors.primary 
                    : hasPlan
                        ? AppColors.textPrimary
                        : AppColors.border,
              ),
            ),

            if (hasPlan)
              Expanded(
                child: _buildPlanInfo(context),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildPlanInfo(BuildContext context) {
    final meals = day!.meals;
    final visibleMeals = meals.length >= 4
        ? meals.take(2).toList()
        : meals.take(3).toList();
    final showMore = meals.length >= 4;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ...visibleMeals.map(
          (m) => Padding(
            padding: const EdgeInsets.only(bottom: 1),
            child: Text(
              m.menuName,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.textPrimary,
                    fontSize: 13,
                  ),
            ),
          ),
        ),

        // 4개 이상일 때
        if (showMore)
          Text(
            '... 더보기',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.textSecondary,
                  fontSize: 12,
                ),
          ),

        const Spacer(),

        if (day!.caloriesPerDay != null)
          Text(
            '${formatPrice(day!.caloriesPerDay!)}kcal',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.textPrimary,
                  fontSize: 9,
                ),
          ),

        if (day!.pricePerDay != null)
          Text(
            '₩${formatPrice(day!.pricePerDay!)}',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.textPrimary,
                  fontSize: 9,
                ),
          ),
      ],
    );
  }
}
