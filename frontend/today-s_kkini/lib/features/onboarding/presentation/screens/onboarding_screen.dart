import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/app_primary_button.dart';
import '../../../../core/widgets/popup.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/onboarding_providers.dart';
import '../widgets/food_selector.dart';
import '../widgets/ingredient_selector.dart';
import '../widgets/allergy_input.dart';
import '../widgets/labeled_slider.dart';
import '../../../mypage/presentation/providers/mypage_provider.dart';

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final _pageController = PageController();
  int _currentPage = 0;
  static const int _totalPages = 4;

  final List<String> _selectedFoods = [];
  final List<String> _selectedIngredient = [];
  final List<String> _allergies = [];
  bool _initialized = false;
  bool _isResetFlow = false; // 마이페이지 재설정하기로 들어온 경우

  static const Map<String, List<String>> _categoryIngredients = {
    '육류': ['소고기', '돼지고기', '닭고기', '양고기', '오리고기', '양갈비', '베이컨', '햄', '소시지'],
    '해산물류': ['새우', '연어', '참치', '오징어', '조개', '게', '굴', '문어', '가리비', '홍합'],
    '채소류': ['양파', '마늘', '당근', '브로콜리', '시금치', '버섯', '감자', '토마토', '양배추', '양상추'],
    '식물성 단백질류': ['두부', '콩', '템페', '병아리콩', '렌틸콩', '에다마메', '검은콩', '두유', '청국장', '낫토'],
    '계란 및 유제품류': ['계란', '우유', '치즈', '버터', '요거트', '크림', '생크림'],
  };

  String? _conflictingCategory() {
    for (final entry in _categoryIngredients.entries) {
      final isCategorySelected = _selectedIngredient.contains(entry.key);
      final allergiesInCategory =
          _allergies.where((a) => entry.value.contains(a)).toSet();
      if (isCategorySelected && allergiesInCategory.length >= 2) {
        return entry.key;
      }
    }
    return null;
  }

  bool _canProceed() {
    switch (_currentPage) {
      case 0:
        return _selectedFoods.isNotEmpty;
      case 1:
        return _selectedIngredient.isNotEmpty;
      case 2:
        return true;
      case 3:
        return true;
      default:
        return false;
    }
  }

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
        _isResetFlow = true;
        _selectedFoods.addAll(List<String>.from(extra['foods'] ?? []));
        _selectedIngredient
            .addAll(List<String>.from(extra['ingredients'] ?? []));
        _allergies.addAll(List<String>.from(extra['allergies'] ?? []));

        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!mounted) return;
          final notifier = ref.read(onboardingNotifierProvider.notifier);
          notifier.setFoods(_selectedFoods);
          notifier.setIngredient(_selectedIngredient);
          notifier.setAllergies(_allergies);
          notifier.setDiversity(extra['diversity'] ?? 2);
          notifier.setCookingSkill(extra['cookingSkill'] ?? 3);
        });
      }
    }
  }

  void _next() {
    if (_currentPage == 2) {
      final conflict = _conflictingCategory();
      if (conflict != null) {
        showAppPopupSingle(
          context: context,
          content: '[$conflict]\n선호 재료와 제외 재료가 많이 겹쳐 식단 생성이 어렵습니다. 설정을 조정해 주세요.',
        );
        return;
      }
    }
    if (_currentPage < _totalPages - 1) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      _onSubmit();
    }
  }

  Future<void> _onSubmit() async {
    final notifier = ref.read(onboardingNotifierProvider.notifier);
    notifier.setFoods(List.from(_selectedFoods));
    notifier.setIngredient(List.from(_selectedIngredient));
    notifier.setAllergies(List.from(_allergies));

    ref.read(submitOnboardingProvider.notifier).state =
        const AsyncValue.loading();
    try {
      final saved = await notifier.submit();
      if (!_isResetFlow) {
        await ref.read(authProvider.notifier).refreshUser();
      }
      ref.read(submitOnboardingProvider.notifier).state =
          AsyncValue.data(saved);
      if (!mounted) return;
      if (_isResetFlow) {
        await ref.read(myPageProvider.notifier).fetchMyProfile();
        if (!mounted) return;
        context.pop();
      } else {
        context.go(AppRoutes.mealStyleSelect);
      }
    } catch (e, st) {
      ref.read(submitOnboardingProvider.notifier).state =
          AsyncValue.error(e, st);
    }
  }

  String _buttonLabel() {
    if (_currentPage == _totalPages - 1) {
      return _isResetFlow ? '설정 저장하기' : '식단 생성하기';
    }
    return '다음';
  }

  @override
  Widget build(BuildContext context) {
    final draft = ref.watch(onboardingNotifierProvider);
    final notifier = ref.read(onboardingNotifierProvider.notifier);
    final submitState = ref.watch(submitOnboardingProvider);
    final isSubmitting = submitState?.isLoading ?? false;

    return Scaffold(
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.fromLTRB(24, 0, 24, 40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.only(top: 5, bottom: 10),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(_totalPages, (index) {
                  final isActive = index == _currentPage;
                  return AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    width: isActive ? 16 : 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: isActive ? AppColors.primary : AppColors.gray,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  );
                }),
              ),
            ),
            if (submitState != null && submitState.hasError)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  '서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.error,
                      ),
                ),
              ),
            AppPrimaryButton(
              text: isSubmitting ? '저장 중...' : _buttonLabel(),
              enabled: _canProceed() && !isSubmitting,
              onPressed: _next,
              topPadding: 0,
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: PageView(
          controller: _pageController,
          physics: const NeverScrollableScrollPhysics(),
          onPageChanged: (index) => setState(() => _currentPage = index),
          children: [
            _StepPage(
              title: '취향을 선택해 주세요',
              child: FoodSelector(
                selectedFoods: _selectedFoods,
                onChanged: (v) {
                  setState(() {
                    _selectedFoods
                      ..clear()
                      ..addAll(v);
                  });
                  notifier.setFoods(v);
                },
              ),
            ),
            _StepPage(
              title: '선호 식재료를 선택해 주세요',
              child: IngredientSelector(
                selectedIngredients: _selectedIngredient,
                onChanged: (v) {
                  setState(() {
                    _selectedIngredient
                      ..clear()
                      ..addAll(v);
                  });
                  notifier.setIngredient(v);
                },
              ),
            ),
            _StepPage(
              title: '알레르기 및 제외 재료를\n입력해 주세요',
              child: AllergyInput(
                allergies: _allergies,
                onChanged: (v) {
                  setState(() {
                    _allergies
                      ..clear()
                      ..addAll(v);
                  });
                  notifier.setAllergies(v);
                },
              ),
            ),
            _StepPage(
              title: '요리 실력과 다양성을\n설정해 주세요',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 60),
                  Text(
                    '요리 실력',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                  const SizedBox(height: 40),
                  LabeledSlider(
                    value: draft.cookingSkill,
                    min: 1,
                    max: 5,
                    divisions: 4,
                    getLabel: (v) {
                      switch (v) {
                        case 1:
                          return '라면 정도는 끓일 수 있어요';
                        case 2:
                          return '간단한 요리는 해요';
                        case 3:
                          return '레시피를 보고 대부분 따라 할 수 있어요';
                        case 4:
                          return '웬만한 요리는 다 해요';
                        case 5:
                          return '요리가 특기예요';
                        default:
                          return '';
                      }
                    },
                    onChanged: notifier.setCookingSkill,
                  ),
                  const SizedBox(height: 100),
                  Text(
                    '다양성',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                  const SizedBox(height: 40),
                  LabeledSlider(
                    value: draft.diversity,
                    min: 1,
                    max: 5,
                    divisions: 4,
                    getLabel: (v) {
                      switch (v) {
                        case 1:
                          return '매일 같은 메뉴도 괜찮아요';
                        case 2:
                          return '가끔 바뀌면 좋겠어요';
                        case 3:
                          return '적당히 다양하게 먹고 싶어요';
                        case 4:
                          return '자주 다양하게 먹고 싶어요';
                        case 5:
                          return '매일 다른 메뉴를 먹고 싶어요';
                        default:
                          return '';
                      }
                    },
                    onChanged: notifier.setDiversity,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StepPage extends StatelessWidget {
  const _StepPage({
    required this.title,
    required this.child,
  });

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(
            title,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                  fontFamily: 'MemomentKkukkukk',
                  fontSize: 30,
                ),
          ),
          const SizedBox(height: 24),
          child,
        ],
      ),
    );
  }
}