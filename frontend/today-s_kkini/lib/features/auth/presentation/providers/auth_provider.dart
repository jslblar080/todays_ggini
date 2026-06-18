import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';
import 'package:kakao_flutter_sdk_user/kakao_flutter_sdk_user.dart' as kakao;
import 'package:google_sign_in/google_sign_in.dart';
import 'package:flutter_web_auth_2/flutter_web_auth_2.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

import '../../../../core/network/api_client.dart';
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
      final result = await FlutterWebAuth2.authenticate(
        url: 'https://nid.naver.com/oauth2.0/authorize'
            '?client_id=${Env.naverClientId}'
            '&response_type=code'
            '&redirect_uri=todaysggini://auth',
        callbackUrlScheme: 'todaysggini',
      );
      final code = Uri.parse(result).queryParameters['code'] ?? '';
      final user = await _repository.loginWithNaver(code);
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

  Future<void> logout() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      await _googleSignIn.signOut();
      await _repository.logout();
      await _deleteTokens();
      if (!mounted) return;
      state = const AuthState();
    } catch (e) {
      if (!mounted) return;
      state = state.copyWith(error: e, isLoading: false);
    }
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
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (ref) => AuthNotifier(
    ref.watch(authRepositoryProvider),
    ref.watch(googleSignInProvider),
    ref.watch(secureStorageProvider),
  ),
);