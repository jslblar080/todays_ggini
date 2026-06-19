import 'package:dio/dio.dart';

class OnboardingRemoteDataSource {
  OnboardingRemoteDataSource(this._dio);
  final Dio _dio;

  Future<Map<String, dynamic>> postOnboarding(Map<String, dynamic> body) async {
    final response = await _dio.put<Map<String, dynamic>>(
      '/user/onboarding-setting',
      data: body,
    );
    final data = response.data;
    if (data == null) {
      throw Exception('Empty response from /api/v1/user/onboarding-setting');
    }
    return data;
  }
}