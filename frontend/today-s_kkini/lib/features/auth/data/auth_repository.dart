import '../domain/user.dart';
import 'auth_remote_data_source.dart';

class AuthRepository {
  final AuthRemoteDataSource _remote;
  AuthRepository(this._remote);

  Future<User> loginWithKakao(String accessToken) async {
    final raw = await _remote.loginWithKakao(accessToken);
    return User.fromJson(raw, 'kakao');
  }

  Future<User> loginWithNaver(String code) async {
    final raw = await _remote.loginWithNaver(code);
    return User.fromJson(raw, 'naver');
  }

  Future<User> loginWithGoogle(String accessToken) async {
    final raw = await _remote.loginWithGoogle(accessToken);
    return User.fromJson(raw, 'google');
  }

  Future<void> logout() async {
    await _remote.logout();
  }

  /// 게스트 세션 생성 → JWT 받음
  Future<String> initGuestSession() async {
    final tokenData = await _remote.initGuestSession();
    return tokenData['accessToken'] as String;
  }

  /// JWT 가 secure storage 에 저장된 상태에서 /me 호출
  Future<User> getCurrentUser({
    required String accessToken,
    String? refreshToken,
  }) async {
    final raw = await _remote.getMe();
    return User(
      id: raw['id'].toString(),
      provider: raw['provider'] as String,
      email: raw['email'] as String?,
      accessToken: accessToken,
      refreshToken: refreshToken,
      isOnboarded: raw['is_onboarded'] as bool? ?? false,
    );
  }

  Future<void> unregister() async {
    await _remote.unregister();
  }
}
