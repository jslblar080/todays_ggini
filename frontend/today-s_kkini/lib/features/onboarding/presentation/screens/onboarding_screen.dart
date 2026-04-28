import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../providers/onboarding_providers.dart';
import '../widgets/labeled_slider.dart';

/// 온보딩 슬라이더 화면 (피그마 #4 / 1 of 1).
/// 4개 슬라이더 + 식비 슬라이더 + 시작하기 버튼.
class OnboardingScreen extends ConsumerWidget {
  const OnboardingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final draft = ref.watch(onboardingNotifierProvider);
    final notifier = ref.read(onboardingNotifierProvider.notifier);
    final submitState = ref.watch(submitOnboardingProvider);
    final isSubmitting = submitState?.isLoading ?? false;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 8),
              Text(
                '나에게 딱 맞게 설정하기',
                style: Theme.of(context).textTheme.headlineLarge,
              ),
              const SizedBox(height: 24),
              LabeledSlider(
                title: '내 요리실력',
                leftLabel: '초보 (라면)',
                rightLabel: '고수 (일류쉐프)',
                value: draft.cookingSkill,
                onChanged: notifier.setCookingSkill,
              ),
              const SizedBox(height: 24),
              LabeledSlider(
                title: '식재료 선호도 (채소 ↔ 육류)',
                leftLabel: '채소',
                rightLabel: '육류',
                value: draft.vegMeatPreference,
                onChanged: notifier.setVegMeatPreference,
              ),
              const SizedBox(height: 24),
              LabeledSlider(
                title: '식재료 선호도 (냉동 ↔ 신선)',
                leftLabel: '냉동',
                rightLabel: '신선',
                value: draft.freshFrozenPreference,
                onChanged: notifier.setFreshFrozenPreference,
              ),
              const SizedBox(height: 24),
              LabeledSlider(
                title: '평소 식사 스타일',
                leftLabel: '건강식 / 일상식',
                rightLabel: '술안주 / 즐거움',
                value: draft.mealStyle,
                onChanged: notifier.setMealStyle,
              ),
              const SizedBox(height: 24),
              _BudgetSlider(
                value: draft.monthlyBudget,
                onChanged: notifier.setMonthlyBudget,
              ),
              const SizedBox(height: 32),
              if (submitState != null && submitState.hasError)
                Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Text(
                    '저장 실패: ${submitState.error}',
                    style: const TextStyle(color: AppColors.error),
                  ),
                ),
              ElevatedButton(
                onPressed:
                    isSubmitting
                        ? null
                        : () => _onSubmit(context, ref, notifier),
                child:
                    isSubmitting
                        ? const SizedBox(
                          height: 22,
                          width: 22,
                          child: CircularProgressIndicator(
                            strokeWidth: 2.5,
                            valueColor: AlwaysStoppedAnimation<Color>(
                              Colors.white,
                            ),
                          ),
                        )
                        : const Text('나만의 맞춤 식단 시작하기'),
              ),
              const SizedBox(height: 12),
              const Center(
                child: Text(
                  '상세 설정은 나중에 마이페이지에서 변경 가능해요',
                  style: TextStyle(fontSize: 13, color: AppColors.textHint),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _onSubmit(
    BuildContext context,
    WidgetRef ref,
    OnboardingNotifier notifier,
  ) async {
    ref.read(submitOnboardingProvider.notifier).state =
        const AsyncValue.loading();
    try {
      final saved = await notifier.submit();
      ref.read(submitOnboardingProvider.notifier).state = AsyncValue.data(
        saved,
      );
      if (context.mounted) {
        context.go(AppRoutes.mealStyleSelect);
      }
    } catch (e, st) {
      ref.read(submitOnboardingProvider.notifier).state = AsyncValue.error(
        e,
        st,
      );
    }
  }
}

class _BudgetSlider extends StatelessWidget {
  const _BudgetSlider({required this.value, required this.onChanged});

  final int value;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    final formatter = NumberFormat('#,##0', 'ko_KR');
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '[한달 식비 예산]',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 8),
        Slider(
          value: value.toDouble(),
          min: 100000,
          max: 1000000,
          divisions: 18, // 5만원 단위
          label: '${formatter.format(value)}원',
          onChanged: (v) => onChanged(v.round()),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                '10만원',
                style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
              ),
              Text(
                '${formatter.format(value)}원',
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppColors.primaryDark,
                ),
              ),
              const Text(
                '100만원 이상',
                style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        const Center(
          child: Text(
            '이 예산 내에서 최적의 식단을 짜드려요!',
            style: TextStyle(fontSize: 13, color: AppColors.textHint),
          ),
        ),
      ],
    );
  }
}
