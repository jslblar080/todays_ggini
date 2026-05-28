import 'package:dio/dio.dart';
import 'dart:typed_data';

class MyPageRemoteDataSource {
  MyPageRemoteDataSource(this._dio);
  final Dio _dio;

  Future<Map<String, dynamic>> fetchMyProfile() async {
    final response = await _dio.get<Map<String, dynamic>>('/user/me');
    final data = response.data;
    if (data == null) {
      throw Exception('Empty response from /user/me');
    }
    return data;
  }

  Future<Map<String, dynamic>> updateNickname(String nickname) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/user/profile',
      data: {'nickname': nickname},
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> uploadProfileImage(Uint8List bytes, String filename) async {
    final formData = FormData.fromMap({
      'file': MultipartFile.fromBytes(bytes, filename: filename),
    });
    final response = await _dio.post<Map<String, dynamic>>(
      '/user/profile/image',
      data: formData,
    );
    return response.data!;
  }
}