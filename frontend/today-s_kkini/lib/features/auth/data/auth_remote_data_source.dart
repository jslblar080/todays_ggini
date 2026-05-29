import 'package:dio/dio.dart';

class AuthRemoteDataSource {
  final Dio _dio;
  AuthRemoteDataSource(this._dio);

  Future<Map<String, dynamic>> loginWithKakao(String accessToken) async {
    final response = await _dio.post(
      '/auth/kakao',
      data: {'accessToken': accessToken},
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> loginWithNaver(String code) async {
    final response = await _dio.post('/auth/naver', data: {'code': code});
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> loginWithGoogle(String accessToken) async {
    final response = await _dio.post(
      '/auth/google',
      data: {'accessToken': accessToken},
    );
    return response.data as Map<String, dynamic>;
  }

  Future<void> logout() async {
    await _dio.post('/auth/logout');
  }

  /// 백엔드에 게스트 세션 생성 요청 → JWT 받음
  Future<Map<String, dynamic>> initGuestSession() async {
    final response = await _dio.post('/auth/guest/init');
    return response.data as Map<String, dynamic>;
  }

  /// 저장된 JWT 로 본인 정보 조회
  Future<Map<String, dynamic>> getMe() async {
    final response = await _dio.get('/user/me');
    return response.data as Map<String, dynamic>;
  }

  /// 회원 탈퇴
  Future<void> unregister() async {
    await _dio.delete('/auth/unregister');
  }
}
