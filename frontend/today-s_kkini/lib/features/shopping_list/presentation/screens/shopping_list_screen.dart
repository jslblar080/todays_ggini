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
      body: SafeArea(child: _buildBody(context, state, notifier, userMarkets)),
      bottomNavigationBar: const BottomNavBar(currentIndex: 2),
    );
  }

  // 마켓 키를 한글로 변환
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
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
            child: Column(
              children: [
                const SizedBox(height: 14),
                ShoppingListSummary(data: data, userMarkets: userMarkets),
                const SizedBox(height: 16),
                if (flatRows.isNotEmpty)
                  _buildSelectAll(context, flatRows, notifier),
                Expanded(
                  child: flatRows.isEmpty
                      ? const _EmptyState()
                      : ListView.builder(
                          padding: EdgeInsets.zero,
                          itemCount: flatRows.length + 1,
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

  // 헤더 — '장보기 목록' 타이틀 중앙 정렬, 우측에 휴지통(삭제 내역) 진입점.
  // 좌측 SizedBox(48)로 우측 아이콘과 균형을 맞춰 타이틀이 정확히 가운데 오도록 함.
  Widget _buildHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 12, 8, 0),
      child: Row(
        children: [
          const SizedBox(width: 48),
          const Spacer(),
          Text('장보기 목록', style: Theme.of(context).textTheme.headlineLarge),
          const Spacer(),
          IconButton(
            icon: const Icon(Icons.delete_outline, size: 24),
            color: AppColors.textPrimary,
            tooltip: '삭제 내역',
            onPressed: () => context.push(AppRoutes.shoppingTrash),
          ),
        ],
      ),
    );
  }

  // 전체 선택 / 해제 — 모두 체크되면 체크, 일부만 체크면 중간(indeterminate) 표시.
  // 탭하면 화면에 보이는 모든 항목을 한 번에 선택/해제한다.
  Widget _buildSelectAll(
    BuildContext context,
    List<(String, ShoppingItem)> flatRows,
    ShoppingListNotifier notifier,
  ) {
    final visibleIds = [for (final (_, item) in flatRows) item.itemId];
    final checkedCount = flatRows.where((r) => r.$2.isChecked).length;
    final allChecked = checkedCount == flatRows.length;
    final someChecked = checkedCount > 0 && !allChecked;

    return InkWell(
      onTap: () => notifier.setChecked(visibleIds, !allChecked),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          children: [
            SizedBox(
              width: 32,
              height: 32,
              child: Checkbox(
                value: allChecked ? true : (someChecked ? null : false),
                tristate: true,
                onChanged: (_) => notifier.setChecked(visibleIds, !allChecked),
                activeColor: AppColors.textPrimary,
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                visualDensity: VisualDensity.compact,
                side: const BorderSide(color: AppColors.textPrimary),
              ),
            ),
            const SizedBox(width: 8),
            Text('전체 선택', style: Theme.of(context).textTheme.bodyMedium),
            const Spacer(),
            Text(
              '$checkedCount / ${flatRows.length}',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
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