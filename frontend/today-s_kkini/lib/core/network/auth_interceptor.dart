import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../env/env.dart';

/// 모든 요청에 JWT access 토큰을 붙이고,
/// 401(access 토큰 만료) 응답이 오면 저장된 refresh 토큰으로
/// `/auth/refresh` 를 호출해 새 access 토큰을 받은 뒤 원래 요청을 재시도한다.
///
/// refresh 까지 실패하면 토큰을 비우고 인증 상태를 초기화한다(= 로그인 화면으로).
class AuthInterceptor extends Interceptor {
  final FlutterSecureStorage _storage;

  /// 401 재시도 시 원요청을 다시 보낼 dio (인터셉터가 붙은 본체와 동일 인스턴스).
  final Dio _dio;

  /// refresh 까지 실패했을 때 호출 — 토큰 정리/로그아웃 처리는 호출부에서 담당.
  /// 순환 참조를 피하려고 생성 시 주입하지 않고, auth_provider 가 나중에 연결한다.
  Future<void> Function()? onAuthFailure;

  AuthInterceptor({
    required FlutterSecureStorage storage,
    required Dio dio,
  })  : _storage = storage,
        _dio = dio;

  /// refresh 진행 상태. 동시에 401 이 여러 개 떠도 refresh 는 한 번만 돌고,
  /// 나머지 요청은 이 future 의 결과(새 토큰)를 공유한다.
  Completer<String?>? _refreshCompleter;

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _readToken('accessToken');
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final requestOptions = err.requestOptions;

    // 401(인증 만료) 이 아니면 그대로 통과.
    if (err.response?.statusCode != 401) {
      return handler.next(err);
    }

    // refresh 엔드포인트 자체가 401 → 재발급 불가, 바로 실패 처리.
    if (requestOptions.path.contains('/auth/refresh')) {
      await onAuthFailure?.call();
      return handler.next(err);
    }

    // 이미 한 번 재시도한 요청이 또 401 → 무한루프 방지, 실패 처리.
    if (requestOptions.extra['retried'] == true) {
      await onAuthFailure?.call();
      return handler.next(err);
    }

    // 새 access 토큰 확보(동시 401 은 진행 중인 refresh 결과를 공유).
    final newToken = await _refreshToken();
    if (newToken == null) {
      // refresh 실패 → 그냥 실패(원본 401 을 그대로 올림).
      return handler.next(err);
    }

    // 새 토큰으로 원요청 1회 재시도.
    try {
      requestOptions.extra['retried'] = true;
      requestOptions.headers['Authorization'] = 'Bearer $newToken';
      final response = await _dio.fetch(requestOptions);
      return handler.resolve(response);
    } on DioException catch (e) {
      return handler.next(e);
    }
  }

  /// refresh 토큰으로 새 access 토큰을 발급받아 저장하고 반환.
  /// 실패 시 인증 상태를 초기화하고 null 을 반환한다.
  Future<String?> _refreshToken() {
    // 이미 갱신 중이면 그 결과를 함께 기다린다.
    final inFlight = _refreshCompleter;
    if (inFlight != null) {
      return inFlight.future;
    }

    final completer = Completer<String?>();
    _refreshCompleter = completer;
    _doRefresh(completer);
    return completer.future;
  }

  Future<void> _doRefresh(Completer<String?> completer) async {
    try {
      final refreshToken = await _readToken('refreshToken');
      if (refreshToken == null || refreshToken.isEmpty) {
        await onAuthFailure?.call();
        completer.complete(null);
        return;
      }

      // 인터셉터가 없는 raw dio 로 호출해야 refresh 응답이 또 401 인터셉터를
      // 타고 무한루프로 빠지지 않는다.
      final rawDio = Dio(
        BaseOptions(
          baseUrl: Env.apiBaseUrl,
          connectTimeout: const Duration(seconds: 30),
          receiveTimeout: const Duration(seconds: 30),
          contentType: 'application/json',
        ),
      );

      final response = await rawDio.post(
        '/auth/refresh',
        data: {'refreshToken': refreshToken},
      );

      final newAccess = response.data['accessToken'] as String?;
      if (newAccess == null || newAccess.isEmpty) {
        await onAuthFailure?.call();
        completer.complete(null);
        return;
      }

      await _writeToken('accessToken', newAccess);
      completer.complete(newAccess);
    } catch (_) {
      // refresh 토큰 만료/세션 불일치 등 → 실패 처리.
      await onAuthFailure?.call();
      completer.complete(null);
    } finally {
      _refreshCompleter = null;
    }
  }

  /// 토큰 읽기. 웹은 SharedPreferences, 모바일은 SecureStorage.
  Future<String?> _readToken(String key) async {
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(key);
    }
    return _storage.read(key: key);
  }

  /// 토큰 쓰기. auth_provider 의 저장 규칙과 동일하게,
  /// SecureStorage 에 항상 쓰고 웹이면 SharedPreferences 에도 쓴다.
  Future<void> _writeToken(String key, String value) async {
    await _storage.write(key: key, value: value);
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(key, value);
    }
  }
}
