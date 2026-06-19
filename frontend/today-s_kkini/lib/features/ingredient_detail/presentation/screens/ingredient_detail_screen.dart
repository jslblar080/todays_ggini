import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/bottom_nav_bar.dart';
import '../../../mypage/presentation/providers/mypage_provider.dart';
import '../../../shopping_selection/presentation/providers/shopping_selection_provider.dart';
import '../providers/ingredient_detail_provider.dart';
import '../widgets/ingredient_header_card.dart';
import '../widgets/price_comparison_row.dart';

class IngredientDetailScreen extends ConsumerWidget {
  final String ingredientId;

  const IngredientDetailScreen({super.key, required this.ingredientId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(ingredientDetailProvider(ingredientId));

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(context),
            Expanded(child: _buildBody(context, ref, state)),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.chevron_left, size: 32),
            color: AppColors.textPrimary,
            onPressed: () {
              if (context.canPop()) {
                context.pop();
              } else {
                context.go(AppRoutes.calendar);
              }
            },
          ),
          const Spacer(),
          Text(
            '재료 상세',
            style: Theme.of(context).textTheme.headlineLarge,
          ),
          const Spacer(),
          const SizedBox(width: 48),
        ],
      ),
    );
  }

  // 마켓 키를 한글 이름으로 변환
  String _marketToKorean(String market) {
    switch (market) {
      case 'coupang': return '쿠팡';
      case 'market_kurly': return '컬리';
      case 'naver_shopping': return '네이버';
      default: return market;
    }
  }

  Widget _buildBody(
    BuildContext context,
    WidgetRef ref,
    IngredientDetailState state,
  ) {
    if (state.error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            '가격 정보를 불러오지 못했습니다.\n${state.error}',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: AppColors.error,
            ),
          ),
        ),
      );
    }

    if (state.isLoading || state.prices == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final prices = state.prices!;
    final selection = ref.watch(shoppingSelectionProvider);
    final selectedMarket = selection.selectedMarketFor(ingredientId);
    final userMarkets = ref.watch(myPageProvider).profile?.markets ?? ['쿠팡', '컬리', '네이버'];

    // 사용자 마켓으로 필터링
    final filteredPrices = prices.sortedByPrice
        .where((entry) => userMarkets.contains(_marketToKorean(entry.key)))
        .toList();

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 8),
          IngredientHeaderCard(prices: prices),
          const SizedBox(height: 24),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              children: [
                Expanded(
                  flex: 2,
                  child: Text(
                    '마켓',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppColors.textPrimary,
                        ),
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Row(
                    children: [
                      const SizedBox(width: 10),
                      Text('가격', style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textPrimary)),
                    ],
                  ),
                ),
                const SizedBox(width: 80),
              ],
            ),
          ),
          const SizedBox(height: 4),
          const Divider(color: AppColors.border, height: 3),
          const SizedBox(height: 4),
          ...filteredPrices.map(
            (entry) => PriceComparisonRow(
              market: entry.key,
              price: entry.value,
              isUserSelected: selectedMarket == entry.key,
              onSelect: () {
                ref
                    .read(shoppingSelectionProvider.notifier)
                    .selectMarket(ingredientId, entry.key);
              },
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}