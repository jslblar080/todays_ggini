import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/format.dart';
import '../../domain/shopping_list.dart';

class ShoppingListSummary extends StatelessWidget {
  final ShoppingList data;
  final List<String> userMarkets;

  const ShoppingListSummary({
    super.key,
    required this.data,
    this.userMarkets = const ['쿠팡', '컬리', '네이버'],
  });

  String _marketToKorean(String market) {
    switch (market) {
      case 'coupang': return '쿠팡';
      case 'market_kurly': return '컬리';
      case 'naver_shopping': return '네이버';
      default: return market;
    }
  }

  @override
  Widget build(BuildContext context) {
    final filteredCounts = data.marketCounts
        .where((c) =>
            userMarkets.contains(c.market) ||
            userMarkets.contains(_marketToKorean(c.market)))
        .toList();

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.border, width: 3),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // 왼쪽: 총 항목 수 + 금액
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '   총 ${data.checkedItemsCount}개 항목',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 6),
                Text(
                  '   ₩${formatPrice(data.totalPricePerShopping)}',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
              ],
            ),
          ),
          // 오른쪽: 마켓별 체크박스 + 개수
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: filteredCounts.map((c) {
              final label = _marketToKorean(c.market);
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Row(
                  children: [
                    Container(
                      width: 18,
                      height: 18,
                      decoration: BoxDecoration(
                        border: Border.all(color: AppColors.textPrimary),
                        borderRadius: BorderRadius.circular(5),
                      ),
                      child: c.count > 0
                          ? const Icon(Icons.check, size: 14, color: AppColors.textPrimary)
                          : null,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      '$label ${c.count}',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppColors.textPrimary,
                          ),
                    ),
                    const SizedBox(width: 6),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}