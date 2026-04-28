import '../domain/user_profile.dart';
import 'onboarding_remote_data_source.dart';

/// Domain ↔ Data 변환 담당.
///
/// Presentation 계층은 Repository 만 알면 되고,
/// 백엔드 API 가 바뀌면 이 파일과 [OnboardingRemoteDataSource] 만 수정하면 끝.
class OnboardingRepository {
  OnboardingRepository(this._remote);

  final OnboardingRemoteDataSource _remote;

  /// 슬라이더 입력값을 서버에 저장하고, 저장된 프로필을 반환.
  Future<UserProfile> saveProfile(UserProfile profile) async {
    final raw = await _remote.putProfile(profile.toJson());
    final profileJson = raw['profile'] as Map<String, dynamic>;
    return UserProfile.fromJson(profileJson);
  }
}
