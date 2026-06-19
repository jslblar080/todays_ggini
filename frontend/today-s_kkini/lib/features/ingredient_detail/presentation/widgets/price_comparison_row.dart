import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/format.dart';
import '../../domain/ingredient_prices.dart';

class PriceComparisonRow extends StatelessWidget {
  final String market;
  final MarketPrice price;
  final bool isUserSelected;
  final VoidCallback onSelect;

  const PriceComparisonRow({
    super.key,
    required this.market,
    required this.price,
    required this.isUserSelected,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    final isAvailable = price.isAvailable;

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
          child: Row(
            children: [
              Expanded(
                flex: 2,
                child: Row(
                  children: [
                    Text(
                      _marketLabel(market),
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    if (price.isLowest && isAvailable) ...[
                      const SizedBox(width: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          border: Border.all(color: AppColors.primary, width: 1),
                          borderRadius: BorderRadius.circular(5),
                        ),
                        child: Text(
                          '최저',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: AppColors.primary,
                              ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              Expanded(
                flex: 2,
                child: Text(
                  isAvailable ? '₩${formatPrice(price.lowestPrice!)}' : '재고 없음',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: isAvailable ? AppColors.textPrimary : AppColors.textSecondary,
                      ),
                ),
              ),
              GestureDetector(
                onTap: isAvailable ? onSelect : null,
                child: Container(
                  width: 60,
                  height: 34,
                  decoration: BoxDecoration(
                    color: AppColors.grayLight,
                    borderRadius: BorderRadius.circular(0),
                  ),
                  child: Center(
                    child: Text(
                      '선택',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: isUserSelected
                                ? AppColors.primary
                                : isAvailable
                                    ? AppColors.textPrimary
                                    : AppColors.textSecondary,
                          ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
        const Divider(color: AppColors.border, height: 3),
      ],
    );
  }

  String _marketLabel(String market) {
    switch (market) {
      case 'coupang':
        return '쿠팡';

      case 'market_kurly':
        return '컬리';

      case 'naver_shopping':
        return '네이버';

      default:
        return market;
    }
  }
}
