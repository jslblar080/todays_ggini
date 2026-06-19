import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/format.dart';
import '../../../../core/widgets/app_primary_button.dart';
import '../../domain/shopping_list.dart';
import '../providers/shopping_trash_provider.dart';

class ShoppingTrashScreen extends ConsumerWidget {
  const ShoppingTrashScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(shoppingTrashProvider);
    final notifier = ref.read(shoppingTrashProvider.notifier);

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Column(
            children: [
              _buildHeader(context),
              Expanded(child: _buildBody(context, state, notifier)),
              if (!state.isEmpty)
                Padding(
                  padding: const EdgeInsets.fromLTRB(0, 8, 0, 16),
                  child: AppPrimaryButton(
                    text: '전체 복원하기',
                    onPressed: () => notifier.restoreAll(),
                  ),
                ),
            ],
          ),
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
                context.go(AppRoutes.shoppingList);
              }
            },
          ),
          const Spacer(),
          Text('삭제 목록', style: Theme.of(context).textTheme.headlineLarge),
          const Spacer(),
          const SizedBox(width: 48),
        ],
      ),
    );
  }

  Widget _buildBody(
    BuildContext context,
    ShoppingTrashState state,
    ShoppingTrashNotifier notifier,
  ) {
    if (state.error != null && state.data == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.cloud_off_outlined, size: 40, color: AppColors.textSecondary),
              const SizedBox(height: 12),
              Text('삭제 내역을 불러오지 못했어요', style: Theme.of(context).textTheme.bodyMedium),
              const SizedBox(height: 4),
              Text(
                '잠시 후 다시 시도해 주세요',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary),
              ),
              const SizedBox(height: 16),
              OutlinedButton(
                onPressed: () => notifier.refresh(),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.primary,
                  side: const BorderSide(color: AppColors.primary),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                ),
                child: const Text('다시 시도'),
              ),
            ],
          ),
        ),
      );
    }

    if (state.data == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final items = state.flatItems;
    if (items.isEmpty) {
      return Center(
        child: Text('삭제한 항목이 없어요', style: Theme.of(context).textTheme.bodyMedium),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.only(top: 4),
      itemCount: items.length + 1,
      itemBuilder: (_, i) {
        if (i == items.length) {
          return const Divider(height: 3, color: AppColors.border); 
        }
        final entry = items[i];
        return _TrashItemRow(
          market: entry.market,
          item: entry.item,
          onRestore: () => notifier.restore([entry]),
        );
      },
    );
  }
}

class _TrashItemRow extends StatelessWidget {
  final String market;
  final ShoppingItem item;
  final VoidCallback onRestore;

  const _TrashItemRow({
    required this.market,
    required this.item,
    required this.onRestore,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const Divider(height: 3, color: AppColors.border),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(item.ingredientName, style: Theme.of(context).textTheme.bodyMedium),
                    const SizedBox(height: 2),
                    Text(
                      '${item.standardUnit} - ${shoppingMarketLabel(market)} · ₩${formatPrice(item.lowestPrice)}',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textPrimary),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: onRestore,
                child: Container(
                  width: 60,
                  height: 34,
                  decoration: const BoxDecoration(
                    color: AppColors.grayLight,
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Center(
                    child: Text(
                      '복원',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppColors.textPrimary,
                          ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}