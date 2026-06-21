import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';
import 'package:kakao_flutter_sdk_user/kakao_flutter_sdk_user.dart' as kakao;
import 'package:google_sign_in/google_sign_in.dart';
import 'package:flutter_web_auth_2/flutter_web_auth_2.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

import '../../../../core/network/api_client.dart';
import '../../../../core/network/auth_interceptor.dart';
import '../../../../core/env/env.dart';
import '../../data/auth_remote_data_source.dart';
import '../../data/auth_repository.dart';
import '../../domain/user.dart';

// Repository Provider
final authRemoteDataSourceProvider = Provider<AuthRemoteDataSource>((ref) {
  return AuthRemoteDataSource(ref.watch(dioProvider));
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(ref.watch(authRemoteDataSourceProvider));
});

// Google Sign In Provider
final googleSignInProvider = Provider<GoogleSignIn>((ref) {
  return GoogleSignIn(
    clientId: kIsWeb ? Env.googleWebClientId : null,
    scopes: ['email', 'profile'],
  );
});

// State 클래스
class AuthState {
  final User? user;
  final bool isLoading;
  final Object? error;

  const AuthState({
    this.user,
    this.isLoading = false,
    this.error,
  });

  bool get isLoggedIn => user != null;
  bool get isGuest => user?.provider == 'guest';

  AuthState copyWith({
    User? user,
    bool? isLoading,
    Object? error,
    bool clearError = false,
  }) {
    return AuthState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

// Notifier 클래스
class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _repository;
  final GoogleSignIn _googleSignIn;
  final FlutterSecureStorage _storage;

  AuthNotifier(this._repository, this._googleSignIn, this._storage)
      : super(const AuthState());

  // 토큰 저장 헬퍼
  Future<void> _saveTokens(User user) async {
    if (user.accessToken != null) {
      await _storage.write(key: 'accessToken', value: user.accessToken);
      if (kIsWeb) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('accessToken', user.accessToken!);
      }
    }
    if (user.refreshToken != null) {
      await _storage.write(key: 'refreshToken', value: user.refreshToken);
      if (kIsWeb) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('refreshToken', user.refreshToken!);
      }
    }
  }

  // 토큰 삭제 헬퍼
  Future<void> _deleteTokens() async {
    await _storage.delete(key: 'accessToken');
    await _storage.delete(key: 'refreshToken');
    if (kIsWeb) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('accessToken');
      await prefs.remove('refreshToken');
    }
  }

  /// 백엔드에서 최신 user 상태를 가져와 authState 갱신.
  Future<void> refreshUser() async {
    final accessToken = await _storage.read(key: 'accessToken');
    if (accessToken == null || accessToken.isEmpty) return;
    final refreshToken = await _storage.read(key: 'refreshToken');
    try {
      final user = await _repository.getCurrentUser(
        accessToken: accessToken,
        refreshToken: refreshToken,
      );
      if (!mounted) return;
      state = state.copyWith(user: user);
    } catch (_) {
      // 무시 - 현재 상태 유지
    }
  }

  // 카카오 SDK → 토큰 받기 → 백엔드 전달
  Future<void> loginWithKakao() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      kakao.OAuthToken token;
      if (await kakao.isKakaoTalkInstalled()) {
        token = await kakao.UserApi.instance.loginWithKakaoTalk();
      } else {
        token = await kakao.UserApi.instance.loginWithKakaoAccount();
      }
      final user = await _repository.loginWithKakao(token.accessToken);
      await _saveTokens(user);
      if (!mounted) return;
      state = state.copyWith(user: user, isLoading: false);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e, isLoading: false);
    }
  }

  // 네이버 웹뷰 → 코드 받기 → 백엔드 전달
  Future<void> loginWithNaver() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      // 웹은 커스텀 스킴(todaysggini://)이 동작하지 않으므로 같은 origin의
      // HTTPS 콜백 페이지(web/auth.html)로 리다이렉트한다. origin 은 런타임에
      // 구해서 vercel 미리보기/프로덕션/커스텀 도메인 어디서든 맞게 동작한다.
      // 네이버 콘솔 Callback URL 에도 이 주소를 등록해야 한다.
      final redirectUri =
          kIsWeb ? '${Uri.base.origin}/auth.html' : 'todaysggini://auth';
      final authUrl = Uri.https('nid.naver.com', '/oauth2.0/authorize', {
        'client_id': Env.naverClientId,
        'response_type': 'code',
        'redirect_uri': redirectUri,
      }).toString();
      final result = await FlutterWebAuth2.authenticate(
        url: authUrl,
        // web 에선 이 값이 redirect 매칭에 쓰이지 않고(콜백 페이지의 postMessage 로
        // 처리), native 에선 todaysggini:// 스킴 매칭에 쓰인다.
        callbackUrlScheme: 'todaysggini',
      );
      final code = Uri.parse(result).queryParameters['code'] ?? '';
      final user = await _repository.loginWithNaver(code, redirectUri);
      await _saveTokens(user);
      if (!mounted) return;
      state = state.copyWith(user: user, isLoading: false);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e, isLoading: false);
    }
  }

  // 구글 SDK → 토큰 받기 → 백엔드 전달
  Future<void> loginWithGoogle() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final account = await _googleSignIn.signIn();
      if (account == null) {
        state = state.copyWith(isLoading: false);
        return;
      }
      final auth = await account.authentication;
      final accessToken = auth.accessToken ?? '';
      final user = await _repository.loginWithGoogle(accessToken);
      await _saveTokens(user);
      if (!mounted) return;
      state = state.copyWith(user: user, isLoading: false);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e, isLoading: false);
    }
  }

  Future<void> loginAsGuest() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final accessToken = await _repository.initGuestSession();
      await _storage.write(key: 'accessToken', value: accessToken);
      if (kIsWeb) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('accessToken', accessToken);
      }
      final user = await _repository.getCurrentUser(
        accessToken: accessToken,
        refreshToken: null,
      );
      if (!mounted) return;
      state = state.copyWith(user: user, isLoading: false);
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e, isLoading: false);
    }
  }

  void markOnboarded() {
    if (state.user != null) {
      state = state.copyWith(
        user: User(
          id: state.user!.id,
          provider: state.user!.provider,
          nickname: state.user!.nickname,
          email: state.user!.email,
          accessToken: state.user!.accessToken,
          refreshToken: state.user!.refreshToken,
          isOnboarded: true,
        ),
      );
    }
  }

  /// 토큰 만료/refresh 실패 등으로 세션이 끊겼을 때 호출.
  /// 백엔드 호출 없이(이미 토큰이 죽었으므로) 로컬 토큰만 비우고 상태를 초기화한다.
  /// authState 가 비워지면 라우터가 자동으로 /auth 로 보낸다.
  Future<void> forceLogout() async {
    await _deleteTokens();
    if (!mounted) return;
    state = const AuthState();
  }

  Future<void> logout() async {
    state = state.copyWith(isLoading: true, clearError: true);
    // 서버 로그아웃/구글 signOut은 best-effort — 실패해도 로컬 로그아웃은 무조건 진행한다.
    // (서버 호출 성공 여부에 로컬 세션 정리를 묶으면, 서버가 죽었을 때 로그아웃이 안 됨)
    try {
      await _repository.logout();
    } catch (_) {}
    try {
      await _googleSignIn.signOut();
    } catch (_) {}
    await _deleteTokens();
    if (!mounted) return;
    state = const AuthState();
  }

  // 게스트 계정 완전 삭제
  Future<void> unregister() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      await _repository.unregister();
      await _deleteTokens();
      if (!mounted) return;
      state = const AuthState();
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e, isLoading: false);
    }
  }
}

// Provider
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final notifier = AuthNotifier(
    ref.watch(authRepositoryProvider),
    ref.watch(googleSignInProvider),
    ref.watch(secureStorageProvider),
  );

  // 401 → refresh 실패 시 세션을 비우도록 인터셉터에 콜백 연결.
  // (dioProvider 가 authProvider 를 직접 참조하면 순환 참조가 되므로 여기서 주입)
  final dio = ref.read(dioProvider);
  for (final interceptor in dio.interceptors) {
    if (interceptor is AuthInterceptor) {
      interceptor.onAuthFailure = notifier.forceLogout;
    }
  }

  return notifier;
});