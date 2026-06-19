import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/format.dart';

class MealDetailSummary extends StatelessWidget {
  final int totalPrice;
  final int totalCalories;

  const MealDetailSummary({
    super.key,
    required this.totalPrice,
    required this.totalCalories,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.border, width: 3),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Expanded(
            child: _item(
              context,
              label: '총 비용',
              value: '₩${formatPrice(totalPrice)}',
            ),
          ),
          Container(width: 3, height: 60, color: AppColors.border),
          Expanded(
            child: _item(
              context,
              label: '총 칼로리',
              value: '${formatPrice(totalCalories)} kcal',
            ),
          ),
        ],
      ),
    );
  }

  Widget _item(BuildContext context, {required String label, required String value}) {
    return Column(
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyLarge,
        ),
      ],
    );
  }
}
