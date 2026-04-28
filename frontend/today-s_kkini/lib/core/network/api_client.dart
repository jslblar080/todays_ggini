import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../env/env.dart';
import 'mock_interceptor.dart';

/// 앱 전체에서 공유하는 Dio 인스턴스.
/// `USE_MOCKS=true` 일 때 [MockInterceptor] 가 자동으로 mock JSON 을 반환.
final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: Env.apiBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      contentType: 'application/json',
    ),
  );

  if (Env.useMocks) {
    dio.interceptors.add(MockInterceptor());
  }

  // TODO: 추후 추가
  // - AuthInterceptor (Authorization 헤더 자동 부착)
  // - LogInterceptor (debug 빌드에서만)

  return dio;
});
