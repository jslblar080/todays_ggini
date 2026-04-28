import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/services.dart' show rootBundle;

/// `assets/mocks/` 의 정적 JSON 으로 응답을 가짜로 만들어 주는 Dio interceptor.
///
/// 새 mock 을 추가할 때:
///  1. `assets/mocks/<group>/<name>.json` 파일 생성
///  2. `pubspec.yaml` 의 `flutter > assets` 에 폴더 등록
///  3. 아래 [_mockMap] 에 `'METHOD /path': asset_path` 추가
class MockInterceptor extends Interceptor {
  static const Map<String, String> _mockMap = {
    'PUT /users/me/profile': 'assets/mocks/users/profile_after-onboarding.json',
    // 백엔드 팀원이 mock 을 commit 하면 여기에 매핑 추가:
    // 'POST /auth/social-login': 'assets/mocks/auth/social-login_new-user.json',
    // 'GET /meal-plan/preview':  'assets/mocks/meal-plan/preview_single-value.json',
    // ...
  };

  /// 네트워크 지연 시뮬레이션.
  static const _simulatedLatency = Duration(milliseconds: 300);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final key = '${options.method} ${options.path}';
    final assetPath = _mockMap[key];

    if (assetPath == null) {
      // mock 매핑이 없으면 그냥 진짜 HTTP 호출로 진행.
      // 실제 백엔드도 없으면 Dio 가 connection error 를 반환할 거임.
      handler.next(options);
      return;
    }

    try {
      final raw = await rootBundle.loadString(assetPath);
      final data = json.decode(raw);
      await Future.delayed(_simulatedLatency);
      handler.resolve(
        Response(requestOptions: options, statusCode: 200, data: data),
      );
    } catch (e) {
      handler.reject(
        DioException(
          requestOptions: options,
          error: 'Mock asset load failed: $assetPath ($e)',
          type: DioExceptionType.unknown,
        ),
      );
    }
  }
}
