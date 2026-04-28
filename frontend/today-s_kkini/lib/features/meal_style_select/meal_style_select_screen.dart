import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_routes.dart';

/// Placeholder: 추천 식단 스타일 (피그마 #5).
/// TODO: UI 구현. 현재는 다음 화면으로 넘어가는 버튼만 있음.
class MealStyleSelectScreen extends StatelessWidget {
  const MealStyleSelectScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('추천 식단 스타일')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text(
                '추천 식단 스타일\n(아직 구현 안 됨)',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 18),
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: () => context.go(AppRoutes.mealPlanLoading),
                child: const Text('이 스타일로 결정하기'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
