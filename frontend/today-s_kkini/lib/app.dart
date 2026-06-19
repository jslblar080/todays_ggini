import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';

class KkiniPickApp extends ConsumerWidget {
  const KkiniPickApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: '오늘의 끼니', // 앱 이름
      theme: AppTheme.light(), // 앱의 밝은 테마 적용
      routerConfig: router, // 화면 이동 설정 적용
      debugShowCheckedModeBanner: false, // 오른쪽 위 DEBUG 배너 숨김
      builder: (context, child) {
        return GestureDetector(
          onTap: () => FocusScope.of(context).unfocus(),
          behavior: HitTestBehavior.translucent,
          child: child,
        );
      },
    );
  }
}