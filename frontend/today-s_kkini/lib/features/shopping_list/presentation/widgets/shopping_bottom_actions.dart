import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/app_primary_button.dart';

class ShoppingBottomActions extends StatelessWidget {
  final int checkedCount;
  final int totalCount;
  final VoidCallback onToggleAll;
  final VoidCallback onDeleteChecked;
  final VoidCallback onCheckoutByMarket;

  const ShoppingBottomActions({
    super.key,
    required this.checkedCount,
    required this.totalCount,
    required this.onToggleAll,
    required this.onDeleteChecked,
    required this.onCheckoutByMarket,
  });

  @override
  Widget build(BuildContext context) {
    final allChecked = checkedCount == totalCount && totalCount > 0;
    final hasCheckedItems = checkedCount > 0;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          children: [
            GestureDetector(
              onTap: onToggleAll,
              child: Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  color: allChecked ? AppColors.primary : AppColors.grayLight,
                  borderRadius: BorderRadius.circular(5),
                ),
                child: Icon(
                  Icons.check,
                  size: 18,
                  color: allChecked ? Colors.white : AppColors.gray,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Text(
              '$checkedCount개 선택',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const Spacer(),
            GestureDetector(
              onTap: hasCheckedItems ? onDeleteChecked : null,
              child: Container(
                width: 90,
                height: 34,
                decoration: const BoxDecoration(
                  color: AppColors.grayLight,
                  borderRadius: BorderRadius.zero,
                ),
                child: Center(
                  child: Text(
                    '선택 삭제',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: hasCheckedItems
                              ? AppColors.textPrimary
                              : AppColors.textSecondary,
                        ),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            GestureDetector(
              onTap: totalCount > 0 ? onDeleteChecked : null,
              child: Container(
                width: 90,
                height: 34,
                decoration: const BoxDecoration(
                  color: AppColors.grayLight,
                  borderRadius: BorderRadius.zero,
                ),
                child: Center(
                  child: Text(
                    '전체 삭제',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: totalCount > 0
                              ? AppColors.textPrimary
                              : AppColors.textSecondary,
                        ),
                  ),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        AppPrimaryButton(
          text: '마켓별 한 번에 구매하기',
          enabled: hasCheckedItems,
          onPressed: onCheckoutByMarket,
        ),
      ],
    );
  }
}