import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../../core/theme/app_colors.dart';
import '../../domain/shopping_list.dart';

// 마켓별 원클릭 구매 시트.
//
// 현재: marketGroups의 subtotal(각 마켓 최저가 기준 체크 항목 합계)을 표시.
// TODO: GET /shopping/checkout-options 연동 후 "이 마켓에서 전부 살 때 총액"과
//       missing_ingredients(재고 없는 재료 목록)로 교체.

void showCheckoutMarketSheet(BuildContext context, ShoppingList data) {
  showModalBottomSheet(
    context: context,
    backgroundColor: Colors.transparent,
    isScrollControlled: true,
    builder: (_) => CheckoutMarketSheet(data: data),
  );
}

class CheckoutMarketSheet extends StatelessWidget {
  final ShoppingList data;

  const CheckoutMarketSheet({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final activeGroups = data.marketGroups
        .where((g) => g.items.any((item) => item.isChecked))
        .toList();

    return Container(
      decoration: const BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: EdgeInsets.fromLTRB(
        20,
        16,
        20,
        MediaQuery.of(context).viewInsets.bottom + 32,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 20),
          Text(
            '어디서 한 번에 살까요?',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '각 마켓 최저가 기준',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 16),
          if (activeGroups.isEmpty)
            const _EmptyState()
          else
            ...activeGroups.map(
              (g) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _MarketCard(group: g),
              ),
            ),
        ],
      ),
    );
  }
}

class _MarketCard extends StatelessWidget {
  final ShoppingMarketGroup group;

  const _MarketCard({required this.group});

  @override
  Widget build(BuildContext context) {
    final info = _marketInfo(group.market);
    final checkedCount = group.items.where((i) => i.isChecked).length;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          Container(
            width: 8,
            height: 40,
            decoration: BoxDecoration(
              color: info.color,
              borderRadius: BorderRadius.circular(4),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  info.label,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '${_formatPrice(group.subtotal)}원  ·  $checkedCount개 항목',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          TextButton(
            onPressed: () => _openMarket(info.url),
            style: TextButton.styleFrom(
              foregroundColor: info.color,
              padding: const EdgeInsets.symmetric(horizontal: 8),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '${info.label} 열기',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: info.color,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(width: 2),
                Icon(Icons.arrow_forward_ios, size: 12, color: info.color),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _openMarket(String url) async {
    final uri = Uri.parse(url);
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      await launchUrl(uri, mode: LaunchMode.inAppBrowserView);
    }
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 24),
      child: Center(
        child: Text(
          '체크된 항목이 없어요',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: AppColors.textSecondary,
          ),
        ),
      ),
    );
  }
}

String _formatPrice(int price) {
  if (price == 0) return '0';
  final result = StringBuffer();
  final s = price.toString();
  for (int i = 0; i < s.length; i++) {
    if (i > 0 && (s.length - i) % 3 == 0) result.write(',');
    result.write(s[i]);
  }
  return result.toString();
}

class _MarketInfo {
  final String label;
  final Color color;
  final String url;

  const _MarketInfo({
    required this.label,
    required this.color,
    required this.url,
  });
}

_MarketInfo _marketInfo(String market) => switch (market) {
  'coupang' => const _MarketInfo(
    label: '쿠팡',
    color: Color(0xFFEE2222),
    url: 'https://www.coupang.com',
  ),
  'market_kurly' => const _MarketInfo(
    label: '컬리',
    color: Color(0xFF5F0080),
    url: 'https://www.kurly.com',
  ),
  'naver_shopping' => const _MarketInfo(
    label: '네이버',
    color: Color(0xFF03C75A),
    url: 'https://shopping.naver.com',
  ),
  _ => _MarketInfo(
    label: market,
    color: AppColors.textSecondary,
    url: 'https://www.google.com/search?q=$market',
  ),
};
