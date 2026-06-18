import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthInterceptor extends Interceptor {
  final FlutterSecureStorage _storage;

  AuthInterceptor(this._storage);

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    String? token;

    if (kIsWeb) {
      // 웹에서는 SharedPreferences 사용
      final prefs = await SharedPreferences.getInstance();
      token = prefs.getString('accessToken');
    } else {
      // 모바일에서는 FlutterSecureStorage 사용
      token = await _storage.read(key: 'accessToken');
    }

    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }

    handler.next(options);
  }
}