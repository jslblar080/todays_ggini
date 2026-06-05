import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../../../../core/env/env.dart';
import '../../../../core/network/api_client.dart';
import '../../data/shopping_list_repository.dart';
import '../../domain/shopping_list.dart';
import '../../domain/shopping_summary.dart';

// Repository Provider
final shoppingListRepositoryProvider = Provider<ShoppingListRepository>((ref) {
  return ShoppingListRepository(ref.watch(dioProvider));
});

// State 클래스
class ShoppingListState {
  final ShoppingList? data;
  final bool isLoading;
  final Object? error;

  const ShoppingListState({this.data, this.isLoading = false, this.error});

  ShoppingListState copyWith({
    ShoppingList? data,
    bool? isLoading,
    Object? error,
    bool clearError = false,
  }) {
    return ShoppingListState(
      data: data ?? this.data,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

// Notifier 클래스
class ShoppingListNotifier extends StateNotifier<ShoppingListState> {
  final ShoppingListRepository _repository;

  ShoppingListNotifier(this._repository) : super(const ShoppingListState()) {
    _load();
  }

  Future<void> _load() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final data = await _repository.fetchShoppingList();
      if (!mounted) return;
      state = ShoppingListState(data: data, isLoading: false);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e, isLoading: false);
    }
  }

  // 사용자가 새로고침을 원할 때
  Future<void> refresh() => _load();

  // 항목 체크/해제
  //
  // Optimistic 동기화 패턴:
  // 1) 로컬에서 즉시 토글 + _recomputeSummary 로 UI 반영 (반응성)
  // 2) 백엔드 PATCH 호출
  // 3) 실서버 모드면 응답 summary 로 합계 부분만 덮어쓰기 (서버 진실 신뢰)
  //    mock 모드면 응답 무시 (mock JSON 이 fixed 값이라 부정확)
  //
  // market_groups 의 subtotal 은 응답에 없으므로 로컬 _recomputeSummary 결과 유지.
  Future<void> toggleItem(String itemId) async {
    final current = state.data;
    if (current == null) return;

    // 1) 로컬 토글 + 새 상태 계산
    bool? newCheckedValue;
    final newGroups =
        current.marketGroups.map((group) {
          final newItems =
              group.items.map((item) {
                if (item.itemId != itemId) return item;
                newCheckedValue = !item.isChecked;
                return item.copyWith(isChecked: newCheckedValue);
              }).toList();
          return group.copyWith(items: newItems);
        }).toList();

    state = state.copyWith(data: _recomputeSummary(current, newGroups));

    // 2) 백엔드 sync
    if (newCheckedValue == null) return; // 해당 itemId 가 없으면 호출 안 함
    try {
      final summary = await _repository.updateItemChecks([
        (itemId: itemId, isChecked: newCheckedValue!),
      ]);
      if (!mounted) return;
      if (!Env.useMocks) {
        state = state.copyWith(data: _applyServerSummary(state.data!, summary));
      }
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e);
    }
  }

  // 여러 항목의 체크 상태를 일괄 설정 (전체 선택 / 전체 해제)
  //
  // toggleItem 과 같은 optimistic 패턴. 상태가 실제로 바뀌는 항목만 백엔드로 전송.
  Future<void> setChecked(List<String> itemIds, bool checked) async {
    final current = state.data;
    if (current == null || itemIds.isEmpty) return;
    final idSet = itemIds.toSet();

    // 바뀔 항목이 하나도 없으면 no-op
    final updates = <({String itemId, bool isChecked})>[
      for (final group in current.marketGroups)
        for (final item in group.items)
          if (idSet.contains(item.itemId) && item.isChecked != checked)
            (itemId: item.itemId, isChecked: checked),
    ];
    if (updates.isEmpty) return;

    // 1) 로컬 일괄 갱신
    final newGroups =
        current.marketGroups.map((group) {
          final newItems =
              group.items.map((item) {
                if (!idSet.contains(item.itemId)) return item;
                return item.copyWith(isChecked: checked);
              }).toList();
          return group.copyWith(items: newItems);
        }).toList();

    state = state.copyWith(data: _recomputeSummary(current, newGroups));

    // 2) 백엔드 sync
    try {
      final summary = await _repository.updateItemChecks(updates);
      if (!mounted) return;
      if (!Env.useMocks) {
        state = state.copyWith(data: _applyServerSummary(state.data!, summary));
      }
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e);
    }
  }

  // 체크된 항목 일괄 삭제 (soft delete)
  //
  // toggleItem 과 같은 optimistic 패턴.
  // 백엔드는 물리 삭제 대신 deleted_at 만 기록 → 휴지통에서 복원 가능.
  Future<void> deleteCheckedItems() async {
    final current = state.data;
    if (current == null) return;

    // 체크된 itemId 수집
    final checkedItemIds = <String>[
      for (final group in current.marketGroups)
        for (final item in group.items)
          if (item.isChecked) item.itemId,
    ];
    if (checkedItemIds.isEmpty) return;

    // 1) 로컬 삭제 + 새 상태 계산
    final newGroups =
        current.marketGroups.map((group) {
          final remaining =
              group.items.where((item) => !item.isChecked).toList();
          return group.copyWith(items: remaining);
        }).toList();

    state = state.copyWith(data: _recomputeSummary(current, newGroups));

    // 2) 백엔드 sync
    try {
      final summary = await _repository.deleteItems(checkedItemIds);
      if (!mounted) return;
      if (!Env.useMocks) {
        state = state.copyWith(data: _applyServerSummary(state.data!, summary));
      }
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e);
    }
  }

  // 서버 응답 summary 로 합계 필드들만 덮어쓰기 — market_groups 는 보존
  ShoppingList _applyServerSummary(
    ShoppingList current,
    ShoppingSummary summary,
  ) {
    return current.copyWith(
      totalItems: summary.totalItems,
      checkedItemsCount: summary.checkedItemsCount,
      totalPricePerShopping: summary.totalPricePerShopping,
      marketCounts: summary.marketCounts,
    );
  }

  // market_groups 가 바뀐 후 상단 summary 필드들을 다시 계산.
  // 백엔드 응답이 summary 를 같이 주지만 market_groups 의 subtotal 은 응답에 없으므로
  // 이 함수가 계속 필요 (subtotal 계산용 + 1차 optimistic 갱신용).
  ShoppingList _recomputeSummary(
    ShoppingList current,
    List<ShoppingMarketGroup> newGroups,
  ) {
    int totalItems = 0;
    int checkedCount = 0;
    int totalPrice = 0;
    final newMarketCounts = <ShoppingMarketCount>[];
    final updatedGroups = <ShoppingMarketGroup>[];

    for (final group in newGroups) {
      int marketCheckedCount = 0;
      int marketSubtotal = 0;
      for (final item in group.items) {
        totalItems += 1;
        if (item.isChecked) {
          checkedCount += 1;
          totalPrice += item.lowestPrice;
          marketCheckedCount += 1;
          marketSubtotal += item.lowestPrice;
        }
      }
      newMarketCounts.add(
        ShoppingMarketCount(market: group.market, count: marketCheckedCount),
      );
      updatedGroups.add(group.copyWith(subtotal: marketSubtotal));
    }

    return current.copyWith(
      totalItems: totalItems,
      checkedItemsCount: checkedCount,
      totalPricePerShopping: totalPrice,
      marketCounts: newMarketCounts,
      marketGroups: updatedGroups,
    );
  }
}

// StateNotifierProvider
final shoppingListProvider =
    StateNotifierProvider.autoDispose<ShoppingListNotifier, ShoppingListState>(
      (ref) => ShoppingListNotifier(ref.watch(shoppingListRepositoryProvider)),
    );
