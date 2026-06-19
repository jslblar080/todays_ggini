import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../domain/ingredient_prices.dart';

class IngredientHeaderCard extends StatelessWidget {
  final IngredientPrices prices;

  const IngredientHeaderCard({super.key, required this.prices});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.border, width: 3),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 70,
            height: 70,
            decoration: BoxDecoration(
              color: AppColors.border,
              borderRadius: BorderRadius.circular(10),
            ),
            child:
                prices.imageUrl == null
                    ? Center(
                      child: Text(
                        '이미지',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    )
                    : ClipRRect(
                      borderRadius: BorderRadius.circular(10),
                      child: Image.network(prices.imageUrl!, fit: BoxFit.cover),
                    ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 3),
                Text(
                  prices.ingredientName,
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                const SizedBox(height: 4),
                Text(
                  '${prices.standardUnit} 이상',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
