import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/bottom_nav_bar.dart';
import '../../../../core/widgets/popup.dart';
import '../../../mypage/presentation/providers/mypage_provider.dart';
import '../../domain/shopping_list.dart';
import '../providers/shopping_list_provider.dart';
import '../widgets/checkout_market_sheet.dart';
import '../widgets/shopping_bottom_actions.dart';
import '../widgets/shopping_item_row.dart';
import '../widgets/shopping_list_summary.dart';

class ShoppingListScreen extends ConsumerWidget {
  const ShoppingListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(shoppingListProvider);
    final notifier = ref.read(shoppingListProvider.notifier);
    final myPageState = ref.watch(myPageProvider);
    final userMarkets = myPageState.profile?.markets ?? ['쿠팡', '컬리', '네이버'];

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(child: _buildBody(context, ref, state, notifier, userMarkets)),
      bottomNavigationBar: const BottomNavBar(currentIndex: 2),
    );
  }

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
    ShoppingListState state,
    ShoppingListNotifier notifier,
    List<String> userMarkets,
  ) {
    if (state.error != null && state.data == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            '장보기 목록을 불러오지 못했습니다.\n${state.error}',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: AppColors.error,
            ),
          ),
        ),
      );
    }

    if (state.data == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final data = state.data!;
    final flatRows = _flattenForDisplay(data, userMarkets);

    return Column(
      children: [
        _buildHeader(context),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 0),
            child: Column(
              children: [
                const SizedBox(height: 8),
                ShoppingListSummary(data: data, userMarkets: userMarkets),
                const SizedBox(height: 16),
                Expanded(
                  child: flatRows.isEmpty
                      ? const _EmptyState()
                      : ListView.builder(
                          padding: EdgeInsets.zero,
                          itemCount: flatRows.length + 1,
                          itemBuilder: (_, i) {
                            if (i == flatRows.length) {
                              return const Divider(height: 3, color: AppColors.border);
                            }
                            final (market, item) = flatRows[i];
                            return ShoppingItemRow(
                              item: item,
                              market: market,
                              onToggle: () => notifier.toggleItem(item.itemId),
                            );
                          },
                        ),
                ),
              ],
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          child: ShoppingBottomActions(
            checkedCount: data.checkedItemsCount,
            totalCount: flatRows.length,
            onToggleAll: () {
              final allIds = [for (final (_, item) in flatRows) item.itemId];
              final allChecked = data.checkedItemsCount == flatRows.length;
              notifier.setChecked(allIds, !allChecked);
            },
            onDeleteChecked: () => _confirmDelete(context, notifier),
            onCheckoutByMarket: () => showCheckoutMarketSheet(context, data),
          ),
        ),
      ],
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        children: [
          const SizedBox(width: 48),
          const Spacer(),
          Text('장보기 목록', style: Theme.of(context).textTheme.headlineLarge),
          const Spacer(),
          IconButton(
            icon: const Icon(Icons.delete_outline, size: 32),
            color: AppColors.textPrimary,
            tooltip: '삭제 내역',
            onPressed: () => context.push(AppRoutes.shoppingTrash),
          ),
        ],
      ),
    );
  }

  List<(String, ShoppingItem)> _flattenForDisplay(ShoppingList data, List<String> userMarkets) {
    final out = <(String, ShoppingItem)>[];
    for (final g in data.marketGroups) {
      final koreanMarket = _marketToKorean(g.market);
      if (userMarkets.contains(g.market) || userMarkets.contains(koreanMarket)) {
        for (final item in g.items) {
          out.add((g.market, item));
        }
      }
    }
    return out;
  }

  void _confirmDelete(
    BuildContext context,
    ShoppingListNotifier notifier,
  ) {
    showAppPopup(
      context: context,
      content: '선택한 항목을 목록에서 제거할까요?',
      leftButtonText: '취소',
      rightButtonText: '제거',
      onLeftTap: () => Navigator.pop(context),
      onRightTap: () {
        Navigator.pop(context);
        notifier.deleteCheckedItems();
      },
      leftButtonColor: AppColors.textSecondary,
      rightButtonColor: AppColors.primary,
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text(
        '장보기 목록이 비어있어요',
        style: Theme.of(context).textTheme.bodyMedium,
      ),
    );
  }
}