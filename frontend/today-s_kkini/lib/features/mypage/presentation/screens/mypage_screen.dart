import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/bottom_nav_bar.dart';
import '../providers/mypage_provider.dart';
import '../widgets/profile_section.dart';
import '../../../../core/widgets/popup.dart';
import '../../domain/my_profile.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../onboarding/presentation/providers/onboarding_providers.dart';

class MyPageScreen extends ConsumerStatefulWidget {
  const MyPageScreen({super.key});

  @override
  ConsumerState<MyPageScreen> createState() => _MyPageScreenState();
}

class _MyPageScreenState extends ConsumerState<MyPageScreen> {
  bool _personaExpanded = false;
  bool _onboardingExpanded = false;
  bool _generalExpanded = false;

  @override
  void initState() {
    super.initState();
    Future.microtask(
        () => ref.read(myPageProvider.notifier).fetchMyProfile());
  }

  String _diversityLabel(String level) {
    switch (level) {
      case '낮음':
        return '한 가지 음식만 먹어도 괜찮아요';
      case '보통':
        return '적당히 다양하게 먹고 싶어요';
      case '높음':
        return '매일 다른 음식을 먹고 싶어요';
      default:
        return level;
    }
  }

  String _cookingSkillLabel(int level) {
    switch (level) {
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
  }

  String _diversityDescription(int level) {
    switch (level) {
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
  }

  String _formatList(List<String> list) {
    if (list.isEmpty) return '없음';
    return list.join(', ');
  }

  void _showPersonaStatusPopup(MyProfile profile) {
    showAppPopupWidget(
      context: context,
      title: '[페르소나 설정]',
      contentWidget: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _StatusRow(
            label: '가구원',
            value: '${profile.householdType} · ${profile.familyCount}인',
            trailing: GestureDetector(
              onTap: () {
                Navigator.pop(context);
                context.push(AppRoutes.familyMembers, extra: profile);
              },
              child: Text(
                '가구원 정보 확인하기',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      decoration: TextDecoration.underline,
                    ),
              ),
            ),
          ),
          _StatusRow(label: '식사 수', value: '${profile.mealsPerDay}끼'),
          _StatusRow(
            label: '한달 예산',
            value: '${(profile.monthlyBudget / 10000).round()}만원',
          ),
          _StatusRow(label: '요리 목적', value: _formatList(profile.purpose)),
        ],
      ),
      leftButtonText: '확인',
      rightButtonText: '재설정하기',
      leftButtonColor: AppColors.textPrimary,
      rightButtonColor: AppColors.textPrimary,
      onLeftTap: () => Navigator.pop(context),
      onRightTap: () => _goToPersonaSelectWithProfile(profile),
    );
  }

  void _showOnboardingStatusPopup(MyProfile profile) {
    final cookingSkill = profile.cookingSkill;
    final diversityInt = diversityToInt(profile.diversityLevel);

    showAppPopupWidget(
      context: context,
      title: '[온보딩 설정]',
      contentWidget: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _StatusRow(
              label: '취향', value: _formatList(profile.preferredCategories)),
          _StatusRow(
              label: '선호 식재료',
              value: _formatList(profile.preferredIngredients)),
          _StatusRow(
              label: '제외 식재료',
              value: _formatList(profile.excludedIngredients)),
          _StatusRow(
            label: '요리 실력',
            value: '$cookingSkill단계 - ${_cookingSkillLabel(cookingSkill)}',
          ),
          _StatusRow(
            label: '다양성',
            value: '$diversityInt단계 - ${_diversityDescription(diversityInt)}',
          ),
        ],
      ),
      leftButtonText: '확인',
      rightButtonText: '재설정하기',
      leftButtonColor: AppColors.textSecondary,
      rightButtonColor: AppColors.primary,
      onLeftTap: () => Navigator.pop(context),
      onRightTap: () => _goToOnboardingWithProfile(profile),
    );
  }

  void _goToPersonaSelectWithProfile(MyProfile profile) {
    if (Navigator.canPop(context)) Navigator.pop(context);
    context.push(AppRoutes.personaSelect, extra: {
      'householdType': profile.householdType,
      'familyCount': profile.familyCount,
      'mealsPerDay': profile.mealsPerDay,
      'monthlyBudget': profile.monthlyBudget,
      'purpose': profile.purpose,
      'activityLevel': profile.activityLevel,
      'familyMembers': profile.familyMembers,
      'personaName': profile.personaName,
    });
  }

  void _goToOnboardingWithProfile(MyProfile profile) {
    if (Navigator.canPop(context)) Navigator.pop(context);
    context.push(AppRoutes.onboarding, extra: {
      'foods': profile.preferredCategories,
      'ingredients': profile.preferredIngredients,
      'allergies': profile.excludedIngredients,
      'diversity': diversityToInt(profile.diversityLevel),
      'cookingSkill': profile.cookingSkill,
    });
  }

  void _showLogoutDialog(BuildContext context) {
    final router = GoRouter.of(context);
    final isGuest = ref.read(authProvider).isGuest;

    showAppPopup(
      context: context,
      content: isGuest
          ? '게스트 계정은 로그아웃 시\n모든 정보가 삭제됩니다.\n정말 로그아웃 하시겠어요?'
          : '정말 로그아웃 하시겠어요?',
      leftButtonText: '취소',
      rightButtonText: '로그아웃',
      onLeftTap: () => Navigator.pop(context),
      onRightTap: () async {
        Navigator.pop(context);
        if (isGuest) {
          await ref.read(authProvider.notifier).unregister();
        } else {
          await ref.read(authProvider.notifier).logout();
        }
        router.go(AppRoutes.auth);
      },
      rightButtonColor: AppColors.textSecondary,
    );
  }

  void _showDeleteAccountDialog(BuildContext context) {
    final router = GoRouter.of(context);
    showAppPopup(
      context: context,
      content: '정말 탈퇴하시겠어요?\n모든 데이터가 삭제됩니다.',
      leftButtonText: '취소',
      rightButtonText: '탈퇴하기',
      onLeftTap: () => Navigator.pop(context),
      onRightTap: () async {
        Navigator.pop(context);
        await ref.read(authProvider.notifier).unregister();
        router.go(AppRoutes.auth);
      },
      rightButtonColor: AppColors.error,
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(myPageProvider);

    if (state.isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
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
                onPressed: () =>
                    ref.read(myPageProvider.notifier).fetchMyProfile(),
                child: const Text('다시 시도'),
              ),
            ],
          ),
        ),
      );
    }

    final profile = state.profile;
    if (profile == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            children: [
              ProfileSection(
                name: profile.nickname ?? '',
                imageUrl: profile.imageUrl,
                persona: profile.personaName ?? '',
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
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Column(
                  children: [
                    _AccordionSection(
                      title: '페르소나 설정',
                      expanded: _personaExpanded,
                      onToggle: () => setState(
                          () => _personaExpanded = !_personaExpanded),
                      content: _PersonaIconsBox(
                        onIconTap: () => _showPersonaStatusPopup(profile),
                        onResetTap: () =>
                            _goToPersonaSelectWithProfile(profile),
                      ),
                    ),
                    const SizedBox(height: 12),
                    _AccordionSection(
                      title: '온보딩 설정',
                      expanded: _onboardingExpanded,
                      onToggle: () => setState(
                          () => _onboardingExpanded = !_onboardingExpanded),
                      content: _OnboardingIconsBox(
                        onIconTap: () => _showOnboardingStatusPopup(profile),
                        onResetTap: () =>
                            _goToOnboardingWithProfile(profile),
                      ),
                    ),
                    const SizedBox(height: 12),
                    _AccordionSection(
                      title: '일반 설정',
                      expanded: _generalExpanded,
                      onToggle: () => setState(
                          () => _generalExpanded = !_generalExpanded),
                      content: _GeneralSettingsBox(
                        onLogout: () => _showLogoutDialog(context),
                        onDeleteAccount: () =>
                            _showDeleteAccountDialog(context),
                      ),
                    ),
                    const SizedBox(height: 40),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const BottomNavBar(currentIndex: 3),
    );
  }
}

class _AccordionSection extends StatelessWidget {
  final String title;
  final bool expanded;
  final VoidCallback onToggle;
  final Widget content;

  const _AccordionSection({
    required this.title,
    required this.expanded,
    required this.onToggle,
    required this.content,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.border, width: 3),
        borderRadius: BorderRadius.circular(10),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(7), // 바깥 radius(10) - border width(3)
        child: Column(
          children: [
            InkWell(
              onTap: onToggle,
              child: Container(
                color: Colors.white,
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                child: Row(
                  children: [
                    const SizedBox(width: 24),
                    Expanded(
                      child: Text(
                        title,
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ),
                    Icon(
                      expanded
                          ? Icons.keyboard_arrow_up
                          : Icons.keyboard_arrow_down,
                      color: AppColors.textPrimary,
                    ),
                  ],
                ),
              ),
            ),
            if (expanded)
              Container(
                width: double.infinity,
                color: AppColors.border,
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
                child: content,
              ),
          ],
        ),
      ),
    );
  }
}

class _PersonaIconsBox extends StatelessWidget {
  final VoidCallback onIconTap;
  final VoidCallback onResetTap;

  const _PersonaIconsBox({
    required this.onIconTap,
    required this.onResetTap,
  });

  @override
  Widget build(BuildContext context) {
    const items = [
      ('assets/images/mypage_household.png', '가구원'),
      ('assets/images/mypage_meals.png', '식사 수'),
      ('assets/images/mypage_budget.png', '한달 예산'),
      ('assets/images/mypage_purpose.png', '요리 목적'),
    ];

    return Column(
      children: [
        GestureDetector(
          onTap: onIconTap,
          child: Row(
            children: items
                .map(
                  (item) => Expanded(
                    child: Column(
                      children: [
                        Image.asset(item.$1, width: 36, height: 36),
                        const SizedBox(height: 6),
                        Text(
                          item.$2,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppColors.textPrimary,
                          )
                        ),
                      ],
                    ),
                  ),
                )
                .toList(),
          ),
        ),
        const SizedBox(height: 16),
        _ResetButton(onTap: onResetTap),
      ],
    );
  }
}

class _OnboardingIconsBox extends StatelessWidget {
  final VoidCallback onIconTap;
  final VoidCallback onResetTap;

  const _OnboardingIconsBox({
    required this.onIconTap,
    required this.onResetTap,
  });

  @override
  Widget build(BuildContext context) {
    const firstRow = [
      ('assets/images/mypage_taste.png', '취향'),
      ('assets/images/mypage_preferred.png', '선호 식재료'),
      ('assets/images/mypage_excluded.png', '제외 식재료'),
      ('assets/images/mypage_cooking.png', '요리 실력'),
    ];
    const secondRow = [
      ('assets/images/mypage_variety.png', '다양성'),
    ];

    return Column(
      children: [
        GestureDetector(
          onTap: onIconTap,
          child: Column(
            children: [
              Row(
                children: firstRow
                    .map(
                      (item) => Expanded(
                        child: Column(
                          children: [
                            Image.asset(item.$1, width: 36, height: 36),
                            const SizedBox(height: 6),
                            Text(
                              item.$2,
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: AppColors.textPrimary,
                              )
                            ),
                          ],
                        ),
                      ),
                    )
                    .toList(),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  ...secondRow.map(
                    (item) => Expanded(
                      child: Column(
                        children: [
                          Image.asset(item.$1, width: 36, height: 36),
                          const SizedBox(height: 6),
                          Text(
                            item.$2,
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: AppColors.textPrimary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  ...List.generate(
                    4 - secondRow.length,
                    (_) => const Expanded(child: SizedBox()),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        _ResetButton(onTap: onResetTap),
      ],
    );
  }
}

class _ResetButton extends StatelessWidget {
  final VoidCallback onTap;

  const _ResetButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: AppColors.grayLight,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Center(
          child: Text(
            '재설정하기',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ),
      ),
    );
  }
}

class _GeneralSettingsBox extends StatefulWidget {
  final VoidCallback onLogout;
  final VoidCallback onDeleteAccount;

  const _GeneralSettingsBox({
    required this.onLogout,
    required this.onDeleteAccount,
  });

  @override
  State<_GeneralSettingsBox> createState() => _GeneralSettingsBoxState();
}

class _GeneralSettingsBoxState extends State<_GeneralSettingsBox> {
  bool _notificationOn = true;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Column(
            children: [
              Switch(
                value: _notificationOn,
                onChanged: (v) => setState(() => _notificationOn = v),
                activeThumbColor: AppColors.primary,
              ),
              const SizedBox(height: 4),
              Text('알림', style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppColors.textPrimary,
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: GestureDetector(
            onTap: widget.onLogout,
            child: Column(
              children: [
                Image.asset('assets/images/mypage_logout.png',
                    width: 36, height: 36),
                const SizedBox(height: 6),
                Text(
                  '로그아웃',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppColors.textPrimary,
                          ),
                ),
              ],
            ),
          ),
        ),
        Expanded(
          child: GestureDetector(
            onTap: widget.onDeleteAccount,
            child: Column(
              children: [
                Image.asset('assets/images/mypage_delete.png',
                    width: 36, height: 36),
                const SizedBox(height: 6),
                Text(
                  '회원탈퇴',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.error,
                      ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _StatusRow extends StatelessWidget {
  final String label;
  final String value;
  final Widget? trailing;

  const _StatusRow({
    required this.label,
    required this.value,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                if (trailing != null) ...[
                  const SizedBox(height: 4),
                  trailing!,
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}