import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/app_primary_button.dart';
import '../providers/meal_style_select_provider.dart';
import '../widgets/meal_style_card.dart';

class MealStyleSelectScreen extends ConsumerStatefulWidget {
  const MealStyleSelectScreen({super.key});

  @override
  ConsumerState<MealStyleSelectScreen> createState() =>
      _MealStyleSelectScreenState();
}

class _MealStyleSelectScreenState
    extends ConsumerState<MealStyleSelectScreen> {
  int? _selectedIndex;

  @override
  void initState() {
    super.initState();
    Future.microtask(() =>
        ref.read(mealStyleSelectProvider.notifier).fetchCandidates());
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(mealStyleSelectProvider);

    return Scaffold(
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.fromLTRB(24, 0, 24, 40),
        child: AppPrimaryButton(
          text: '이 스타일로 결정하기',
          enabled: _selectedIndex != null,
          onPressed: () => context.go(AppRoutes.mealPlanLoading),
          topPadding: 10,
        ),
      ),
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 24, 24, 16),
              child: Text(
                '이런 스타일은 어떠세요?',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                      fontFamily: 'MemomentKkukkukk',
                      fontSize: 34,
                    ),
              ),
            ),

            if (state.error != null)
              Expanded(
                child: Center(
                  child: Text(
                    '식단 생성을 완료하지 못했어요.',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: AppColors.error,
                        ),
                  ),
                ),
              )
            else if (state.isLoading)
              const Expanded(
                child: Center(child: CircularProgressIndicator()),
              )
            else
              Expanded(
                child: ListView.separated(
                  padding: const EdgeInsets.fromLTRB(24, 0, 24, 16),
                  itemCount: state.candidates.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    return MealStyleCard(
                      style: state.candidates[index],
                      isSelected: _selectedIndex == index,
                      onTap: () {
                        setState(() => _selectedIndex = index);
                        ref
                            .read(mealStyleSelectProvider.notifier)
                            .selectStyle(state.candidates[index]);
                      },
                    );
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }
}