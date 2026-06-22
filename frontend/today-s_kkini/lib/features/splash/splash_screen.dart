import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_routes.dart';
import '../../../../features/auth/presentation/providers/auth_provider.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    // 저장된 토큰으로 세션 복원 (웹=SharedPreferences / 모바일=SecureStorage).
    // 복원이 되면 authState.user 가 채워져 isLoggedIn 이 true 가 된다.
    await ref.read(authProvider.notifier).refreshUser();

    // 스플래시 최소 2초 노출
    await Future.delayed(const Duration(milliseconds: 2000));

    if (!mounted) return;

    final loggedIn = ref.read(authProvider).isLoggedIn;
    // 로그인 상태면 홈으로(라우터가 온보딩 미완 시 personaSelect 로 다시 보냄),
    // 아니면 로그인 화면으로.
    context.go(loggedIn ? AppRoutes.home : AppRoutes.auth);
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Image(
              image: AssetImage('assets/images/start.png'),
              width: 300,
            ),
            SizedBox(height: 10),
          ],
        ),
      ),
    );
  }
}
