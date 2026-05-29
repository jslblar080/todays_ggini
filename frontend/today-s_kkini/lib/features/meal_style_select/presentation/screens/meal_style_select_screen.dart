import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/mascot_speech.dart';
import '../../domain/meal_style.dart';
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
    // 화면 진입 시 자동으로 후보 불러오기
    Future.microtask(() =>
        ref.read(mealStyleSelectProvider.notifier).fetchCandidates());
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(mealStyleSelectProvider);

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const MascotSpeech(message: '이런 스타일은\n어떠세요?'),
            const SizedBox(height: 16),

            // 에러일 때: 메시지 + 다시 시도만
            if (state.error != null)
              Expanded(
                child: Column(
                  children: [
                    Expanded(
                      child: Center(
                        child: Padding(
                          padding: const EdgeInsets.all(24),
                          child: Text(
                            '식단 생성을 완료하지 못했어요.',
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: AppColors.error,
                            ),
                          ),
                        ),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                      child: SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: () => ref
                              .read(mealStyleSelectProvider.notifier)
                              .fetchCandidates(),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(32),
                            ),
                          ),
                          child: Text(
                            '다시 시도',
                            style: Theme.of(context).textTheme.labelLarge,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              )

            // 로딩 중
            else if (state.isLoading)
              const Expanded(
                child: Center(child: CircularProgressIndicator()),
              )

            // 데이터
            else ...[
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
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 0, 24, 8),
                child: Center(
                  child: Text(
                    '위 식단은 예시 샘플 식단입니다.',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                child: SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _selectedIndex == null
                        ? null
                        : () => context.go(AppRoutes.mealPlanLoading),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      disabledBackgroundColor: AppColors.buttonGray,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(32),
                      ),
                    ),
                    child: Text(
                      '이 스타일로 결정하기',
                      style: Theme.of(context).textTheme.labelLarge,
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}