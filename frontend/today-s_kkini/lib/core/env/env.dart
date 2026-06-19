/// 환경변수. compile-time 주입.
///
/// 사용 예 (플랫폼별):
///   # Web / iOS sim
///   flutter run --dart-define=API_BASE_URL=http://localhost:8000
///   # Android emulator
///   flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
class Env {
  const Env._();

  /// true 이면 mock JSON 응답을 사용 (백엔드 미구현 시).
  static const bool useMocks = bool.fromEnvironment(
    'USE_MOCKS',
    defaultValue: false,
  );

  /// 백엔드 base URL. 경로 prefix(/api/v1) 는 호출부에 있으므로 호스트까지만.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );

  /// 카카오 네이티브 앱 키 (Ios/Android).
  static const String kakaoNativeKey = String.fromEnvironment(
    'KAKAO_NATIVE_KEY',
    defaultValue: '',
  );

  /// 카카오 JavaScript 키 (Web).
  static const String kakaoJavaScriptKey = String.fromEnvironment(
    'KAKAO_JAVASCRIPT_KEY',
    defaultValue: '',
  );

  /// 네이버 Client ID.
  static const String naverClientId = String.fromEnvironment(
    'NAVER_CLIENT_ID',
    defaultValue: '',
  );

  /// 네이버 Client Secret.
  static const String naverClientSecret = String.fromEnvironment(
    'NAVER_CLIENT_SECRET',
    defaultValue: '',
  );

  /// 구글 OAuth Client ID — Web 용. Google Cloud Console에서 "Web application" 타입.
  static const String googleWebClientId = String.fromEnvironment(
    'GOOGLE_WEB_CLIENT_ID',
    defaultValue: '',
  );

  /// 구글 OAuth Client ID — iOS 용. Google Cloud Console에서 "iOS" 타입.
  static const String googleIosClientId = String.fromEnvironment(
    'GOOGLE_IOS_CLIENT_ID',
    defaultValue: '',
  );

  /// 구글 OAuth Client ID — Android 용.
  /// Google Cloud Console에서 "Android" 타입으로 패키지명+SHA-1 등록.
  /// 보통 Android에서는 코드가 아니라 OS 가 자동으로 매칭하므로 비워둬도 됨.
  static const String googleAndroidClientId = String.fromEnvironment(
    'GOOGLE_ANDROID_CLIENT_ID',
    defaultValue: '',
  );
}
