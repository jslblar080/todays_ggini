import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/format.dart';
import '../../../../core/widgets/bottom_nav_bar.dart';
import '../../../mypage/presentation/providers/mypage_provider.dart';
import '../../../shopping_selection/presentation/providers/shopping_selection_provider.dart';
import '../providers/ingredient_list_provider.dart';
import '../widgets/ingredient_row.dart';
import '../widgets/menu_summary_card.dart';


class IngredientListScreen extends ConsumerWidget {
  final String mealId;
  final DateTime? sourceDate;
  final int? sourceSlot;

  const IngredientListScreen({
    super.key,
    required this.mealId,
    this.sourceDate,
    this.sourceSlot,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final args = (
      mealId: mealId,
      date: sourceDate ?? DateTime.now(),
      slot: sourceSlot ?? 1,
    );
    final state = ref.watch(ingredientListProvider(args));
    final notifier = ref.read(ingredientListProvider(args).notifier);

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(context),
            Expanded(child: _buildBodyContent(context, ref, state, notifier)),
          ],
        ),
      ),
      bottomNavigationBar: const BottomNavBar(currentIndex: 1),
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
          Text('재료 목록', style: Theme.of(context).textTheme.headlineLarge),
          const Spacer(),
          const SizedBox(width: 48),
        ],
      ),
    );
  }

  Widget _buildBodyContent(
    BuildContext context,
    WidgetRef ref,
    IngredientListState state,
    IngredientListNotifier notifier,
  ) {
    if (state.error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            '재료 목록을 불러오지 못했습니다.\n${state.error}',
            textAlign: TextAlign.center,
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(color: AppColors.error),
          ),
        ),
      );
    }

    if (state.isLoading || state.menu == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final menu = state.menu!;

    final userMarkets =
        ref.watch(myPageProvider).profile?.markets ?? ['쿠팡', '컬리', '네이버'];

    final selection = ref.watch(shoppingSelectionProvider);
    final checkedSet =
        selection.selectionFor(sourceDate ?? DateTime.now(), sourceSlot ?? 1) ??
        <String>{};
    final totalPrice = menu.ingredients
        .where((i) => checkedSet.contains(i.ingredientId))
        .fold<int>(0, (sum, i) {
          final selectedMarket = selection.selectedMarketFor(i.ingredientId);
          return sum + (i.effectivePriceWithin(selectedMarket, userMarkets) ?? 0);
        });

    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 8),
                MenuSummaryCard(
                  menu: menu,
                  sourceDate: sourceDate,
                  sourceSlot: sourceSlot,
                ),
                const SizedBox(height: 16),
                ...menu.ingredients.map(
                  (ing) => IngredientRow(
                    ingredient: ing,
                    isChecked: checkedSet.contains(ing.ingredientId),
                    selectedMarket: selection.selectedMarketFor(
                      ing.ingredientId,
                    ),
                    userMarkets: userMarkets,
                    onToggle: () => notifier.toggleIngredient(ing.ingredientId),
                    onTapDetail: () {
                      context.push(
                        AppRoutes.ingredientDetailPath(ing.ingredientId),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ),
          ),
        ),
        _buildBottomSummary(
          context: context,
          checkedCount: checkedSet.length,
          totalPrice: totalPrice,
        ),
      ],
    );
  }

  Widget _buildBottomSummary({
    required BuildContext context,
    required int checkedCount,
    required int totalPrice,
  }) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          border: Border.all(color: AppColors.border, width: 3),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '장볼 재료 $checkedCount개',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 8),
            Text(
              '합계 ₩${formatPrice(totalPrice)}',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
          ],
        ),
      ),
    );
  }
}