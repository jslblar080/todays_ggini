import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/network/api_client.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/app_primary_button.dart';
import '../../domain/persona_input.dart';
import '../providers/persona_select_provider.dart';
import '../widgets/step1_household.dart';
import '../widgets/step2_basic_info.dart';
import '../widgets/step3_diet_info.dart';
import '../widgets/step4_cooking_goal.dart';
import '../widgets/step5_activity_level.dart';
import '../widgets/step6_persona_result.dart';
import '../../../mypage/presentation/providers/mypage_provider.dart';

class PersonaSelectScreen extends ConsumerStatefulWidget {
  final Map<String, dynamic>? initialData;

  const PersonaSelectScreen({super.key, this.initialData});

  @override
  ConsumerState<PersonaSelectScreen> createState() =>
      _PersonaSelectScreenState();
}

class _PersonaSelectScreenState extends ConsumerState<PersonaSelectScreen> {
  final _pageController = PageController();
  int _currentStep = 0;
  static const int _totalSteps = 6;

  @override
  void initState() {
    super.initState();
    final data = widget.initialData;
    if (data != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        final rawMembers = data['familyMembers'] as List<dynamic>? ?? [];
        final familyMembers = rawMembers.map((m) {
          if (m is FamilyMember) return m;
          // MyProfile 쪽 FamilyMemberInfo 등 다른 타입으로 넘어온 경우 대비
          final dynamic d = m;
          return FamilyMember(
            nickname: d.nickname as String,
            gender: d.gender as String,
            age: d.age as int,
            height: (d.height as num).toDouble(),
            weight: (d.weight as num).toDouble(),
          );
        }).toList();

        ref.read(personaSelectProvider.notifier).initializeWith(
              PersonaInput(
                householdType: data['householdType'] as String? ?? '',
                familyCount: data['familyCount'] as int? ?? 1,
                mealsPerDay: data['mealsPerDay'] as int? ?? 3,
                monthlyBudget: data['monthlyBudget'] as int? ?? 0,
                purpose: List<String>.from(data['purpose'] ?? []),
                activityLevel: data['activityLevel'] as int? ?? 0,
                familyMembers: familyMembers,
                personaName: data['personaName'] as String?,
              ),
            );
      });
    }
  }

  bool _canProceed() {
    final input = ref.read(personaSelectProvider);
    switch (_currentStep) {
      case 0:
        return input.householdType.isNotEmpty &&
            (input.householdType == '1인 가구' || input.familyCount >= 2);
      case 1:
        return input.familyMembers.isNotEmpty &&
            input.familyMembers.every((m) =>
                m.gender.isNotEmpty &&
                m.age > 0 &&
                m.height > 0 &&
                m.weight > 0);
      case 2:
        return input.monthlyBudget >= 300000 &&
            input.monthlyBudget % 50000 == 0;
      case 3:
        return input.purpose.isNotEmpty;
      case 4:
        return input.activityLevel > 0;
      case 5:
        return input.personaName != null && input.personaName!.isNotEmpty;
      default:
        return false;
    }
  }

  Future<void> _next() async {
    if (_currentStep == 4) {
      final input = ref.read(personaSelectProvider);
      final dio = ref.read(dioProvider);
      try {
        await dio.put('/user/persona-setting', data: input.toJson());
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('저장 중 오류가 발생했어요: $e')),
        );
        return;
      }
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else if (_currentStep < _totalSteps - 1) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      _submit();
    }
  }

  Future<void> _submit() async {
    final input = ref.read(personaSelectProvider);
    await ref.read(submitPersonaProvider(input).future);
    if (!mounted) return;
    if (widget.initialData != null) {
      // 마이페이지에서 재설정하기로 들어온 경우 → 마이페이지로 복귀
      await ref.read(myPageProvider.notifier).fetchMyProfile();
      if (!mounted) return;
      context.pop();
    } else {
      context.go(AppRoutes.onboarding);
    }
  }

  String _buttonLabel() {
    if (_currentStep == _totalSteps - 1) return '이 프로필로 시작하기';
    if (_currentStep == 3) return '나만의 끼니 생성하기';
    return '다음';
  }

  @override
  Widget build(BuildContext context) {
    final input = ref.watch(personaSelectProvider);

    return Scaffold(
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.fromLTRB(24, 0, 24, 40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (_currentStep < 5)
              Padding(
                padding: const EdgeInsets.only(top: 10, bottom: 10),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(5, (index) {
                    final isActive = index == _currentStep;
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
            if (_currentStep == 5) const SizedBox(height: 5),
            AppPrimaryButton(
              text: _buttonLabel(),
              enabled: _canProceed(),
              onPressed: _next,
              topPadding: 5,
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: PageView(
          controller: _pageController,
          physics: const NeverScrollableScrollPhysics(),
          onPageChanged: (i) => setState(() => _currentStep = i),
          children: [
            Step1Household(
              selected: input.householdType,
              familyCount: input.familyCount,
              onChanged: (v) {
                ref.read(personaSelectProvider.notifier).setHouseholdType(v);
                if (v == '1인 가구') {
                  ref.read(personaSelectProvider.notifier).setFamilyCount(1);
                }
              },
              onFamilyCountChanged: (v) =>
                  ref.read(personaSelectProvider.notifier).setFamilyCount(v),
            ),
            Step2BasicInfo(
              householdType: input.householdType,
              members: input.familyMembers,
              onChanged: (v) => ref
                  .read(personaSelectProvider.notifier)
                  .setFamilyMembers(v),
            ),
            Step3DietInfo(
              mealsPerDay: input.mealsPerDay,
              monthlyBudget: input.monthlyBudget,
              onMealsChanged: (v) =>
                  ref.read(personaSelectProvider.notifier).setMealsPerDay(v),
              onBudgetChanged: (v) => ref
                  .read(personaSelectProvider.notifier)
                  .setMonthlyBudget(v),
            ),
            Step4CookingGoal(
              selected: input.purpose,
              onChanged: (v) =>
                  ref.read(personaSelectProvider.notifier).setPurpose(v),
            ),
            Step5ActivityLevel(
              selected: input.activityLevel,
              onChanged: (v) => ref
                  .read(personaSelectProvider.notifier)
                  .setActivityLevel(v),
            ),
            Step6PersonaResult(
              selectedPersonaName: input.personaName,
              onSelected: (name) => ref
                  .read(personaSelectProvider.notifier)
                  .setPersonaName(name),
            ),
          ],
        ),
      ),
    );
  }
}