import 'package:dio/dio.dart';

import '../domain/shopping_item_request.dart';
import '../domain/shopping_list.dart';
import '../domain/shopping_summary.dart';

class ShoppingListRepository {
  final Dio _dio;

  ShoppingListRepository(this._dio);

  // 장보기 목록 조회
  // 백엔드: GET /api/v1/shopping/shopping-list
  Future<ShoppingList> fetchShoppingList() async {
    final response = await _dio.get('/shopping/shopping-list');
    return ShoppingList.fromJson(response.data as Map<String, dynamic>);
  }

  // 항목 체크 상태 갱신 (배치)
  // 백엔드: PATCH /api/v1/shopping/shopping-list/items/check
  Future<ShoppingSummary> updateItemChecks(
    List<({String itemId, bool isChecked})> updates,
  ) async {
    final response = await _dio.patch(
      '/shopping/shopping-list/items/check',
      data:
          updates
              .map((u) => {'item_id': u.itemId, 'is_checked': u.isChecked})
              .toList(),
    );
    final data = response.data as Map<String, dynamic>;
    return ShoppingSummary.fromJson(data['summary'] as Map<String, dynamic>);
  }

  // 항목 일괄 삭제
  // 백엔드: DELETE /api/v1/shopping/shopping-list/items/batch-delete
  Future<ShoppingSummary> deleteItems(List<String> itemIds) async {
    final response = await _dio.delete(
      '/shopping/shopping-list/items/batch-delete',
      data: {'item_ids': itemIds},
    );
    final data = response.data as Map<String, dynamic>;
    return ShoppingSummary.fromJson(data['summary'] as Map<String, dynamic>);
  }

  // 삭제(soft delete)된 항목 목록 조회 — 휴지통 화면용
  // 백엔드: GET /api/v1/shopping/shopping-list/trash
  // 응답은 장보기 목록과 동일한 구조(삭제된 항목들을 마켓별 그룹으로 묶음).
  Future<ShoppingList> fetchTrash() async {
    final response = await _dio.get('/shopping/shopping-list/trash');
    return ShoppingList.fromJson(response.data as Map<String, dynamic>);
  }

  // 삭제된 항목 복원 (배치)
  // 백엔드: POST /api/v1/shopping/shopping-list/items/restore
  // 응답: { restored_count, restored_item_ids, summary: {...} }
  // summary 는 복원 후의 "살아있는" 장보기 목록 합계.
  Future<ShoppingSummary> restoreItems(List<String> itemIds) async {
    final response = await _dio.post(
      '/shopping/shopping-list/items/restore',
      data: {'item_ids': itemIds},
    );
    final data = response.data as Map<String, dynamic>;
    return ShoppingSummary.fromJson(data['summary'] as Map<String, dynamic>);
  }

  // 식단의 재료들을 장보기 목록에 추가
  // 백엔드: POST /api/v1/shopping/add-shopping-items
  // body 로 ShoppingItemRequest 배열 전송.
  // 응답은 본 메서드에서 사용 안 함 — 호출 후 화면 이동 시 GET 으로 최신 목록 받음.
  Future<void> addShoppingItems(List<ShoppingItemRequest> items) async {
    await _dio.post(
      '/shopping/add-shopping-items',
      data: items.map((i) => i.toJson()).toList(),
    );
  }
}
