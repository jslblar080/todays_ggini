import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_routes.dart';

/// Placeholder: 월간 캘린더 (피그마 #7).
/// TODO: UI 구현. 현재는 다음 화면으로 넘어가는 버튼만 있음.
class CalendarScreen extends StatelessWidget {
  const CalendarScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('월간 캘린더')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text(
                '월간 캘린더\n(아직 구현 안 됨)',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 18),
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed:
                    () => context.go(AppRoutes.recipe('recipe_namul_bibimbap')),
                child: const Text('레시피 상세'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
