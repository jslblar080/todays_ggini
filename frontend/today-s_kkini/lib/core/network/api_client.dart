import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../env/env.dart';
import 'auth_interceptor.dart';
import 'mock_interceptor.dart';

final secureStorageProvider = Provider<FlutterSecureStorage>((ref) {
  return const FlutterSecureStorage();
});

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: Env.apiBaseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      contentType: 'application/json',
    ),
  );

  if (Env.useMocks) {
    dio.interceptors.add(MockInterceptor());
  }

  // JWT 토큰 자동 부착 + 401 시 refresh 토큰으로 재발급/재시도.
  // onAuthFailure(세션 초기화) 콜백은 순환 참조를 피하려고 authProvider 쪽에서 연결한다.
  dio.interceptors.add(
    AuthInterceptor(
      storage: ref.watch(secureStorageProvider),
      dio: dio,
    ),
  );

  return dio;
});