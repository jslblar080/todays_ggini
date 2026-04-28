/// 환경변수. compile-time 주입.
///
/// 사용 예:
///   flutter run --dart-define=USE_MOCKS=true
///   flutter run --dart-define=USE_MOCKS=false --dart-define=API_BASE_URL=https://...
class Env {
  const Env._();

  /// true 이면 mock JSON 응답을 사용 (백엔드 미구현 시).
  static const bool useMocks = bool.fromEnvironment(
    'USE_MOCKS',
    defaultValue: true,
  );

  /// 백엔드 base URL.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:3000/v1',
  );
}
