import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../../data/shopping_list_repository.dart';
import '../../domain/shopping_list.dart';
import 'shopping_list_provider.dart';

// 휴지통(삭제 내역) 상태 — 삭제된 항목들을 ShoppingList 구조로 그대로 재사용.
class ShoppingTrashState {
  final ShoppingList? data;
  final bool isLoading;
  final Object? error;

  const ShoppingTrashState({this.data, this.isLoading = false, this.error});

  // 화면에 펼칠 (마켓, 항목) 평탄 리스트
  List<({String market, ShoppingItem item})> get flatItems => [
    for (final g in data?.marketGroups ?? const <ShoppingMarketGroup>[])
      for (final item in g.items) (market: g.market, item: item),
  ];

  bool get isEmpty => flatItems.isEmpty;

  ShoppingTrashState copyWith({
    ShoppingList? data,
    bool? isLoading,
    Object? error,
    bool clearError = false,
  }) {
    return ShoppingTrashState(
      data: data ?? this.data,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

class ShoppingTrashNotifier extends StateNotifier<ShoppingTrashState> {
  final Ref _ref;

  ShoppingTrashNotifier(this._ref) : super(const ShoppingTrashState()) {
    _load();
  }

  ShoppingListRepository get _repository =>
      _ref.read(shoppingListRepositoryProvider);

  Future<void> _load() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final data = await _repository.fetchTrash();
      if (!mounted) return;
      state = ShoppingTrashState(data: data, isLoading: false);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e, isLoading: false);
    }
  }

  Future<void> refresh() => _load();

  // 휴지통의 전체 항목 복원
  Future<void> restoreAll() {
    return restore(state.flatItems);
  }

  // 선택한 항목들을 복원 — 휴지통에서 즉시 제거(optimistic) 후 백엔드 호출.
  // 복원 성공 시 살아있는 장보기 목록도 갱신되도록 shoppingListProvider 를 무효화.
  Future<void> restore(
    List<({String market, ShoppingItem item})> items,
  ) async {
    final current = state.data;
    if (current == null || items.isEmpty) return;

    final restoredIds = {for (final r in items) r.item.itemId};

    // 1) 휴지통에서 즉시 제거
    final newGroups = [
      for (final group in current.marketGroups)
        group.copyWith(
          items:
              group.items
                  .where((i) => !restoredIds.contains(i.itemId))
                  .toList(),
        ),
    ];
    state = state.copyWith(data: current.copyWith(marketGroups: newGroups));

    // 2) 백엔드 sync
    try {
      await _repository.restoreItems(restoredIds.toList());
      if (!mounted) return;
      // 살아있는 목록 화면이 복원분을 반영하도록 갱신
      _ref.invalidate(shoppingListProvider);
    } catch (e) {
      if (!mounted) return;
      // 복원 실패 → 휴지통 원상복구
      state = state.copyWith(data: current, error: e);
    }
  }
}

final shoppingTrashProvider = StateNotifierProvider.autoDispose<
  ShoppingTrashNotifier,
  ShoppingTrashState
>((ref) => ShoppingTrashNotifier(ref));
