import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/mascot_speech.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/onboarding_providers.dart';
import '../widgets/goal_selector.dart';
import '../widgets/food_selector.dart';
import '../widgets/ingredient_selector.dart';
import '../widgets/allergy_input.dart';
import '../widgets/diversity_slider.dart';
import '../widgets/labeled_slider.dart';
import '../widgets/budget_slider.dart';

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final _pageController = PageController();
  int _currentPage = 0;

  final List<String> _selectedGoals = [];
  final List<String> _selectedFoods = [];
  final List<String> _selectedIngredient = [];
  final List<String> _allergies = [];
  bool _initialized = false;

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_initialized) {
      _initialized = true;
      final extra = GoRouterState.of(context).extra as Map<String, dynamic>?;
      if (extra != null) {
        _selectedGoals.addAll(List<String>.from(extra['goals'] ?? []));
        _selectedFoods.addAll(List<String>.from(extra['foods'] ?? []));
        _selectedIngredient.addAll(List<String>.from(extra['ingredients'] ?? []));
        _allergies.addAll(List<String>.from(extra['allergies'] ?? []));

        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!mounted) return;
          final notifier = ref.read(onboardingNotifierProvider.notifier);
          notifier.setGoals(_selectedGoals);
          notifier.setFoods(_selectedFoods);
          notifier.setIngredient(_selectedIngredient);
          notifier.setAllergies(_allergies);
          notifier.setDiversity(extra['diversity'] ?? 2);
          notifier.setCookingSkill(extra['cookingSkill'] ?? 3);
          notifier.setMealCount(extra['mealCount'] ?? 3);
          notifier.setMonthlyBudget(extra['monthlyBudget'] ?? 300000);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final draft = ref.watch(onboardingNotifierProvider);
    final notifier = ref.read(onboardingNotifierProvider.notifier);
    final submitState = ref.watch(submitOnboardingProvider);
    final isSubmitting = submitState?.isLoading ?? false;

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const MascotSpeech(message: '나의 취향은?'),
            const SizedBox(height: 16),
            Expanded(
              child: PageView(
                controller: _pageController,
                physics: const NeverScrollableScrollPhysics(),
                onPageChanged: (index) => setState(() => _currentPage = index),
                children: [
                  _buildPage1(notifier),
                  _buildPage2(context, ref, draft, notifier, isSubmitting, submitState),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPage1(OnboardingNotifier notifier) {
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 0, 24, 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                GoalSelector(
                  selectedGoals: _selectedGoals,
                  onChanged: (v) {
                    setState(() {
                      _selectedGoals..clear()..addAll(v);
                    });
                    notifier.setGoals(v);
                  },
                ),
                const SizedBox(height: 32),
                FoodSelector(
                  selectedFoods: _selectedFoods,
                  onChanged: (v) {
                    setState(() {
                      _selectedFoods..clear()..addAll(v);
                    });
                    notifier.setFoods(v);
                  },
                ),
                const SizedBox(height: 32),
                IngredientSelector(
                  selectedIngredients: _selectedIngredient,
                  onChanged: (v) {
                    setState(() {
                      _selectedIngredient..clear()..addAll(v);
                    });
                    notifier.setIngredient(v);
                  },
                ),
                const SizedBox(height: 32),
                AllergyInput(
                  allergies: _allergies,
                  onChanged: (v) {
                    setState(() {
                      _allergies..clear()..addAll(v);
                    });
                    notifier.setAllergies(v);
                  },
                ),
              ],
            ),
          ),
        ),
        // Padding(
        //   padding: const EdgeInsets.fromLTRB(24, 0, 24, 8),
        //   child: Center(
        //     child: Text(
        //       '상세 설정은 나중에 마이페이지에서 변경 가능해요',
        //       style: Theme.of(context).textTheme.bodySmall,
        //     ),
        //   ),
        // ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _selectedGoals.isEmpty || _selectedFoods.isEmpty || _selectedIngredient.isEmpty
                  ? null
                  : () {
                      _pageController.nextPage(
                        duration: const Duration(milliseconds: 300),
                        curve: Curves.easeInOut,
                      );
                    },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                disabledBackgroundColor: AppColors.buttonGray,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(32),
                ),
              ),
              child: Text(
                '다음',
                style: Theme.of(context).textTheme.labelLarge,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPage2(
    BuildContext context,
    WidgetRef ref,
    OnboardingDraft draft,
    OnboardingNotifier notifier,
    bool isSubmitting,
    AsyncValue<dynamic>? submitState,
  ) {
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 0, 24, 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                GestureDetector(
                  onTap: () {
                    _pageController.previousPage(
                      duration: const Duration(milliseconds: 300),
                      curve: Curves.easeInOut,
                    );
                  },
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.arrow_back_ios, size: 16, color: AppColors.textSecondary),
                      Text(
                        '이전',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  '[다양성]',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                const SizedBox(height: 15),
                DiversitySlider(
                  value: draft.diversity,
                  onChanged: notifier.setDiversity,
                ),
                const SizedBox(height: 32),
                Text(
                  '[요리 실력]',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                const SizedBox(height: 15),
                LabeledSlider(
                  value: draft.cookingSkill,
                  min: 1,
                  max: 5,
                  divisions: 4,
                  getLabel: (v) {
                    switch (v) {
                      case 1: return '라면 정도는 끓일 수 있어요';
                      case 2: return '간단한 요리는 해요';
                      case 3: return '레시피를 보고 대부분 따라 할 수 있어요';
                      case 4: return '웬만한 요리는 다 해요';
                      case 5: return '요리가 특기예요';
                      default: return '';
                    }
                  },
                  onChanged: notifier.setCookingSkill,
                ),
                const SizedBox(height: 32),
                Text(
                  '[식사 수]',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                const SizedBox(height: 15),
                LabeledSlider(
                  value: draft.mealCount,
                  min: 1,
                  max: 5,
                  divisions: 4,
                  getLabel: (v) {
                    switch (v) {
                      case 1: return '하루에 한 끼 먹어요';
                      case 2: return '하루에 두 끼 먹어요';
                      case 3: return '하루에 세 끼 먹어요';
                      case 4: return '하루에 네 끼 먹어요';
                      case 5: return '하루에 다섯 끼 먹어요';
                      default: return '';
                    }
                  },
                  onChanged: notifier.setMealCount,
                ),
                const SizedBox(height: 32),
                Text(
                  '[한달 식비 예산]',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                const SizedBox(height: 15),
                BudgetSlider(
                  value: draft.monthlyBudget,
                  onChanged: notifier.setMonthlyBudget,
                ),
              ],
            ),
          ),
        ),
        if (submitState != null && submitState.hasError)
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 0, 24, 4),
            child: Text(
              '서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.error,
              ),
            ),
          ),
        // Padding(
        //   padding: const EdgeInsets.fromLTRB(24, 0, 24, 8),
        //   child: Center(
        //     child: Text(
        //       '상세 설정은 나중에 마이페이지에서 변경 가능해요',
        //       style: Theme.of(context).textTheme.bodySmall,
        //     ),
        //   ),
        // ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed:
                  isSubmitting ? null : () => _onSubmit(context, ref, notifier),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                disabledBackgroundColor: AppColors.buttonGray,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(32),
                ),
              ),
              child: isSubmitting
                  ? const SizedBox(
                      height: 22,
                      width: 22,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : Text(
                      '나만의 맞춤 식단 시작하기',
                      style: Theme.of(context).textTheme.labelLarge,
                    ),
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _onSubmit(
    BuildContext context,
    WidgetRef ref,
    OnboardingNotifier notifier,
  ) async {
    notifier.setGoals(List.from(_selectedGoals));
    notifier.setFoods(List.from(_selectedFoods));
    notifier.setIngredient(List.from(_selectedIngredient));
    notifier.setAllergies(List.from(_allergies));

    ref.read(submitOnboardingProvider.notifier).state = const AsyncValue.loading();
    try {
      final saved = await notifier.submit();

      // 백엔드의 is_onboarded=true 를 프론트 authState 에 반영
      await ref.read(authProvider.notifier).refreshUser();
      ref.read(submitOnboardingProvider.notifier).state = AsyncValue.data(
        saved,
      );
      if (context.mounted) {
        context.go(AppRoutes.mealStyleSelect);
      }
    } catch (e, st) {
      ref.read(submitOnboardingProvider.notifier).state = AsyncValue.error(e, st);
    }
  }
}
