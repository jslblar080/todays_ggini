import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/bottom_nav_bar.dart';
import '../../../../core/widgets/popup.dart';
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

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(child: _buildBody(context, state, notifier)),
      bottomNavigationBar: const BottomNavBar(currentIndex: 2),
    );
  }

  Widget _buildBody(
    BuildContext context,
    ShoppingListState state,
    ShoppingListNotifier notifier,
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
    final flatRows = _flattenForDisplay(data);

    return Column(
      children: [
        Expanded(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
            child: Column(
              children: [
                const SizedBox(height: 14),
                ShoppingListSummary(data: data),
                const SizedBox(height: 16),
                Expanded(
                  child: flatRows.isEmpty
                      ? const _EmptyState()
                      : ListView.builder(
                          padding: EdgeInsets.zero,
                          itemCount: flatRows.length + 1,  // ← +1
                          itemBuilder: (_, i) {
                            if (i == flatRows.length) {
                              return Divider(height: 1, color: AppColors.border);
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
            hasCheckedItems: data.checkedItemsCount > 0,
            onDeleteChecked: () => _confirmDelete(context, notifier),
            onCheckoutByMarket: () => showCheckoutMarketSheet(context, data),
          ),
        ),
      ],
    );
  }

  List<(String, ShoppingItem)> _flattenForDisplay(ShoppingList data) {
    final out = <(String, ShoppingItem)>[];
    for (final g in data.marketGroups) {
      for (final item in g.items) {
        out.add((g.market, item));
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
