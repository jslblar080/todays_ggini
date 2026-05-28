import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/bottom_nav_bar.dart';
import '../providers/mypage_provider.dart';
import '../widgets/profile_section.dart';
import '../widgets/section_title.dart';
import '../widgets/setting_item.dart';
import '../../../../core/widgets/popup.dart';
import '../widgets/mypage_slider.dart';
import '../widgets/mypage_budget_slider.dart';
import '../../domain/my_profile.dart';

class MyPageScreen extends ConsumerStatefulWidget {
  const MyPageScreen({super.key});

  @override
  ConsumerState<MyPageScreen> createState() => _MyPageScreenState();
}

class _MyPageScreenState extends ConsumerState<MyPageScreen> {

  final List<String> _goalOptions = [
    '식비 절약', '영양 균형', '다이어트', '고단백', '간편식', '맛 중심',
  ];
  final List<String> _foodOptions = [
    '한식', '중식', '일식', '양식', '분식', '패스트푸드', '샐러드/건강식', '다 좋아요',
  ];
  final List<String> _ingredientOptions = [
    '육류', '해산물류', '채소류', '식물성 단백질류', '계란 및 유제품류',
  ];

  @override
  void initState() {
    super.initState();
    Future.microtask(() =>
        ref.read(myPageProvider.notifier).fetchMyProfile());
  }

  String _formatList(List<String> list) {
    if (list.isEmpty) return '없음';
    if (list.length <= 2) return list.join(', ');
    return '${list.take(2).join(', ')}, ...';
  }

  String _personaLabel(int id) {
    switch (id) {
      case 1: return '가성비 자취생';
      case 2: return '우리가족 영양사';
      case 3: return '내 몸이 곧 재산';
      case 4: return '퇴근 후 맥주한잔';
      default: return '알 수 없음';
    }
  }

  String _diversityLabel(String level) {
    switch (level) {
      case '낮음': return '한 가지 음식만 먹어도 괜찮아요';
      case '보통': return '적당히 다양하게 먹고 싶어요';
      case '높음': return '매일 다른 음식을 먹고 싶어요';
      default: return level;
    }
  }

  int _diversityToInt(String level) {
    switch (level) {
      case '낮음': return 1;
      case '보통': return 2;
      case '높음': return 3;
      default: return 2;
    }
  }

  Widget _buildChipRow(BuildContext context, List<String> items, List<String> selected) {
    return Row(
      children: items.asMap().entries.map((entry) {
        final index = entry.key;
        final option = entry.value;
        final isSelected = selected.contains(option);
        return Expanded(
          child: Container(
            margin: EdgeInsets.only(right: index < items.length - 1 ? 8 : 0),
            padding: const EdgeInsets.symmetric(vertical: 8),
            decoration: BoxDecoration(
              color: isSelected ? AppColors.primary : AppColors.buttonGray,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: FittedBox(
                fit: BoxFit.scaleDown,
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: Text(
                    option,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: isSelected ? Colors.white : AppColors.textPrimary,
                    ),
                  ),
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildChips(BuildContext context, List<String> options, List<String> selected) {
    if (options.length <= 4) {
      return _buildChipRow(context, options, selected);
    } else if (options.length <= 6) {
      final half = (options.length / 2).ceil();
      return Column(
        children: [
          _buildChipRow(context, options.sublist(0, half), selected),
          const SizedBox(height: 8),
          _buildChipRow(context, options.sublist(half), selected),
        ],
      );
    } else {
      return Column(
        children: [
          _buildChipRow(context, options.sublist(0, 5), selected),
          const SizedBox(height: 8),
          _buildChipRow(context, options.sublist(5), selected),
        ],
      );
    }
  }

  void _goToOnboardingWithProfile() {
    Navigator.pop(context);
    final profile = ref.read(myPageProvider).profile;
    if (profile != null) {
      context.go(AppRoutes.onboarding, extra: {
        'goals': profile.purpose,
        'foods': profile.preferredCategories,
        'ingredients': profile.preferredIngredients,
        'allergies': profile.excludedIngredients,
        'diversity': _diversityToInt(profile.diversityLevel),
        'cookingSkill': profile.cookingSkill,
        'mealCount': profile.mealsPerDay,
        'monthlyBudget': profile.monthlyBudget,
      });
    } else {
      context.go(AppRoutes.onboarding);
    }
  }

  void _showChipDialog(String title, List<String> options, List<String> selected) {
    showAppPopupWidget(
      context: context,
      title: '[$title]',
      contentWidget: _buildChips(context, options, selected),
      leftButtonText: '재설정하기',
      rightButtonText: '확인',
      leftButtonColor: AppColors.primary,
      rightButtonColor: AppColors.textSecondary,
      onLeftTap: () => _goToOnboardingWithProfile(),
      onRightTap: () => Navigator.pop(context),
    );
  }

  void _showSliderDialog(String title, int value, int min, int max, String Function(int) getLabel) {
    showAppPopupWidget(
      context: context,
      title: '[$title]',
      contentWidget: MyPageSlider(
        value: value,
        min: min,
        max: max,
        label: getLabel(value),
      ),
      leftButtonText: '재설정하기',
      rightButtonText: '확인',
      leftButtonColor: AppColors.textSecondary,
      rightButtonColor: AppColors.primary,
      onLeftTap: () => _goToOnboardingWithProfile(),
      onRightTap: () => Navigator.pop(context),
    );
  }

  void _showBudgetDialog(int budget) {
    showAppPopupWidget(
      context: context,
      title: '[한달 식비 예산]',
      contentWidget: MyPageBudgetSlider(value: budget),
      leftButtonText: '재설정하기',
      rightButtonText: '확인',
      leftButtonColor: AppColors.primary,
      rightButtonColor: AppColors.textSecondary,
      onLeftTap: () => _goToOnboardingWithProfile(),
      onRightTap: () => Navigator.pop(context),
    );
  }

  void _showAllergyDialog(List<String> allergies) {
    showAppPopupWidget(
      context: context,
      title: '[제외 재료]',
      contentWidget: _buildChipRow(context, allergies, allergies),
      leftButtonText: '재설정하기',
      rightButtonText: '확인',
      leftButtonColor: AppColors.primary,
      rightButtonColor: AppColors.textSecondary,
      onLeftTap: () => _goToOnboardingWithProfile(),
      onRightTap: () => Navigator.pop(context),
    );
  }

  void _showLogoutDialog(BuildContext context) {
    showAppPopup(
      context: context,
      content: '정말 로그아웃 하시겠어요?',
      leftButtonText: '취소',
      rightButtonText: '로그아웃',
      onLeftTap: () => Navigator.pop(context),
      onRightTap: () => Navigator.pop(context),
      rightButtonColor: AppColors.textSecondary,
    );
  }

  void _showDeleteAccountDialog(BuildContext context) {
    showAppPopup(
      context: context,
      content: '정말 탈퇴하시겠어요?\n모든 데이터가 삭제됩니다.',
      leftButtonText: '취소',
      rightButtonText: '탈퇴하기',
      onLeftTap: () => Navigator.pop(context),
      onRightTap: () => Navigator.pop(context),
      rightButtonColor: AppColors.error,
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(myPageProvider);

    if (state.isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (state.error != null) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text('프로필을 불러오지 못했어요.'),
              const SizedBox(height: 12),
              ElevatedButton(
                onPressed: () => ref.read(myPageProvider.notifier).fetchMyProfile(),
                child: const Text('다시 시도'),
              ),
            ],
          ),
        ),
      );
    }

    final profile = state.profile;
    if (profile == null) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            children: [
              ProfileSection(
                name: profile.nickname,
                imageUrl: profile.imageUrl,
                persona: _personaLabel(profile.personaId),
                onNameChanged: (newName) async {
                  final repo = ref.read(myPageRepositoryProvider);
                  final saved = await repo.updateNickname(newName);
                  ref.read(myPageProvider.notifier).fetchMyProfile();
                  return saved;
                },
                onImageChanged: (bytes, filename) async {
                  final repo = ref.read(myPageRepositoryProvider);
                  final url = await repo.uploadProfileImage(bytes, filename);
                  ref.read(myPageProvider.notifier).fetchMyProfile();
                  return url;
                },
              ),
              const SizedBox(height: 24),
              const SectionTitle(title: '내 설정'),
              SettingItem(
                emoji: '😊',
                title: '페르소나',
                value: _personaLabel(profile.personaId),
                onTap: () {},
              ),
              SettingItem(
                emoji: '✅',
                title: '목적',
                value: _formatList(profile.purpose),
                onTap: () => _showChipDialog('목적', _goalOptions, profile.purpose),
              ),
              SettingItem(
                emoji: '🥨',
                title: '취향',
                value: _formatList(profile.preferredCategories),
                onTap: () => _showChipDialog('취향', _foodOptions, profile.preferredCategories),
              ),
              SettingItem(
                emoji: '🥦',
                title: '선호 식재료',
                value: _formatList(profile.preferredIngredients),
                onTap: () => _showChipDialog('선호 식재료', _ingredientOptions, profile.preferredIngredients),
              ),
              SettingItem(
                emoji: '🫙',
                title: '제외 재료',
                value: _formatList(profile.excludedIngredients),
                onTap: () => _showAllergyDialog(profile.excludedIngredients),
              ),
              SettingItem(
                emoji: '🍱',
                title: '다양성',
                value: profile.diversityLevel,
                onTap: () => _showSliderDialog(
                  '다양성',
                  _diversityToInt(profile.diversityLevel),
                  1, 3,
                  (v) => _diversityLabel(profile.diversityLevel),
                ),
              ),
              SettingItem(
                emoji: '🍳',
                title: '요리 실력',
                value: '${profile.cookingSkill}단계',
                onTap: () => _showSliderDialog('요리 실력', profile.cookingSkill, 1, 5, (v) {
                  switch (v) {
                    case 1: return '라면도 태워요';
                    case 2: return '간단한 요리는 해요';
                    case 3: return '레시피를 보고 대부분 따라 할 수 있어요';
                    case 4: return '웬만한 요리는 다 해요';
                    case 5: return '요리가 특기예요';
                    default: return '';
                  }
                }),
              ),
              SettingItem(
                emoji: '🍚',
                title: '식사 수',
                value: '${profile.mealsPerDay}끼',
                onTap: () => _showSliderDialog('식사 수', profile.mealsPerDay, 1, 5, (v) {
                  switch (v) {
                    case 1: return '하루에 한 끼 먹어요';
                    case 2: return '하루에 두 끼 먹어요';
                    case 3: return '하루에 세 끼 먹어요';
                    case 4: return '하루에 네 끼 먹어요';
                    case 5: return '하루에 다섯 끼 먹어요';
                    default: return '';
                  }
                }),
              ),
              SettingItem(
                emoji: '💰',
                title: '한달 식비 예산',
                value: '${(profile.monthlyBudget / 10000).round()}만원',
                onTap: () => _showBudgetDialog(profile.monthlyBudget),
              ),
              const SizedBox(height: 12),
              Divider(color: AppColors.border, thickness: 2),
              const SizedBox(height: 12),
              const SectionTitle(title: '앱 설정'),
              SettingItem(
                emoji: '🔔',
                title: '알림 설정',
                value: '',
                onTap: () {},
                showToggle: true,
                showArrow: false,
              ),
              const SizedBox(height: 12),
              Divider(color: AppColors.border, thickness: 2),
              const SizedBox(height: 12),
              const SectionTitle(title: '계정 설정'),
              SettingItem(
                emoji: '🚪',
                title: '로그아웃',
                value: '',
                onTap: () => _showLogoutDialog(context),
                showArrow: false,
              ),
              SettingItem(
                emoji: '⚠️',
                title: '회원탈퇴',
                value: '',
                titleColor: AppColors.error,
                onTap: () => _showDeleteAccountDialog(context),
                showArrow: false,
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const BottomNavBar(currentIndex: 3),
    );
  }
}