import 'dart:typed_data';
import '../domain/my_profile.dart';
import 'mypage_remote_data_source.dart';

class MyPageRepository {
  MyPageRepository(this._remote);
  final MyPageRemoteDataSource _remote;

  Future<MyProfile> fetchMyProfile() async {
    final raw = await _remote.fetchMyProfile();
    return MyProfile.fromJson(raw);
  }

  Future<String> updateNickname(String nickname) async {
    final data = await _remote.updateNickname(nickname);
    return data['nickname'] as String;
  }

  Future<String> uploadProfileImage(Uint8List bytes, String filename) async {
    final data = await _remote.uploadProfileImage(bytes, filename);
    return data['imageUrl'] as String;
  }
}