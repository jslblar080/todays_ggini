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

  // 마켓 키를 한글로 변환
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
    final activeCount = filteredCounts.where((c) => c.count > 0).length;

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
      decoration: BoxDecoration(
        color: Colors.transparent,
        border: Border.all(color: AppColors.border, width: 3.0),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '총 ${data.checkedItemsCount}개 항목',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 6),
                Text(
                  '₩${formatPrice(data.totalPricePerShopping)}',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '마켓 $activeCount곳',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                _marketCountLine(filteredCounts),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 6),
              _MarketIndicators(counts: filteredCounts),
            ],
          ),
        ],
      ),
    );
  }

  String _marketCountLine(List<ShoppingMarketCount> counts) {
    return counts
        .map((c) => '${shoppingMarketLabel(c.market)} ${c.count}')
        .join(' · ');
  }
}

class _MarketIndicators extends StatelessWidget {
  final List<ShoppingMarketCount> counts;

  const _MarketIndicators({required this.counts});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (final c in counts) ...[
          _IndicatorBox(checked: c.count > 0),
          const SizedBox(width: 6),
        ],
      ],
    );
  }
}

class _IndicatorBox extends StatelessWidget {
  final bool checked;

  const _IndicatorBox({required this.checked});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 18,
      height: 18,
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.textPrimary),
        borderRadius: BorderRadius.circular(3),
      ),
      child: checked
          ? const Icon(Icons.check, size: 14, color: AppColors.textPrimary)
          : null,
    );
  }
}