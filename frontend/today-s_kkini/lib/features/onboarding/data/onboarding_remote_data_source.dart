import 'package:dio/dio.dart';

/// `PUT /users/me/profile` 호출만 담당.
/// HTTP 의 raw JSON 입출력만 다루고, domain 으로의 변환은 Repository 가 처리.
class OnboardingRemoteDataSource {
  OnboardingRemoteDataSource(this._dio);

  final Dio _dio;

  Future<Map<String, dynamic>> putProfile(Map<String, dynamic> body) async {
    final response = await _dio.put<Map<String, dynamic>>(
      '/users/me/profile',
      data: body,
    );
    final data = response.data;
    if (data == null) {
      throw Exception('Empty response from /users/me/profile');
    }
    return data;
  }
}
