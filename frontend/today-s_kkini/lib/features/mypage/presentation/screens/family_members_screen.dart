import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/network/api_client.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/app_primary_button.dart';
import '../../../persona_select/domain/persona_input.dart';
import '../../domain/my_profile.dart';
import '../providers/mypage_provider.dart';

// 마이페이지 → "가구원 정보 확인하기"에서 진입하는 화면.
// 이미 저장된 가구원 정보를 페이지 단위(좌우 화살표)로 넘기며 보고,
// 가구원 추가/삭제, 개별 정보(성별/나이/키/체중) 수정이 가능하다.
// 저장 시 PUT /user/persona-setting 으로 family_members를 갱신한다.
class FamilyMembersScreen extends ConsumerStatefulWidget {
  final MyProfile profile;

  const FamilyMembersScreen({super.key, required this.profile});

  @override
  ConsumerState<FamilyMembersScreen> createState() =>
      _FamilyMembersScreenState();
}

class _FamilyMembersScreenState extends ConsumerState<FamilyMembersScreen> {
  late List<_MemberForm> _forms;
  final _pageController = PageController();
  int _currentIndex = 0;
  bool _isSaving = false;

  late int _maxFamilyCount;

  @override
  void initState() {
    super.initState();
    _maxFamilyCount = widget.profile.familyCount;

    final existing = widget.profile.familyMembers;
    if (existing.isEmpty) {
      _forms = [_MemberForm(nickname: '대표자')];
    } else {
      _forms = existing.map((m) => _MemberForm.fromInfo(m)).toList();
    }
  }

  @override
  void dispose() {
    _pageController.dispose();
    for (final f in _forms) {
      f.dispose();
    }
    super.dispose();
  }

  bool get _canAdd => _forms.length < _maxFamilyCount;
  bool get _canRemove => _forms.length > 1;

  void _addMember() {
    if (!_canAdd) return;
    setState(() {
        _forms.add(_MemberForm(nickname: ''));
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
        _pageController.animateToPage(
        _forms.length - 1,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
        );
    });
}

  void _removeMember() {
    if (!_canRemove) return;
    final removeIndex = _currentIndex;
    setState(() {
      _forms[removeIndex].dispose();
      _forms.removeAt(removeIndex);
      if (_currentIndex >= _forms.length) {
        _currentIndex = _forms.length - 1;
      }
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _pageController.jumpToPage(_currentIndex);
    });
  }

  void _prevPage() {
    _pageController.previousPage(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  void _nextPage() {
    _pageController.nextPage(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  bool get _allValid => _forms.every((f) =>
      f.gender.isNotEmpty &&
      (int.tryParse(f.ageCtrl.text) ?? 0) > 0 &&
      (double.tryParse(f.heightCtrl.text) ?? 0) > 0 &&
      (double.tryParse(f.weightCtrl.text) ?? 0) > 0);

  Future<void> _save() async {
    if (!_allValid) return;
    setState(() => _isSaving = true);

    final members = _forms.map((f) => f.toJson()).toList();
    final dio = ref.read(dioProvider);

    try {
      await dio.put('/user/persona-setting', data: {
        'household_type': widget.profile.householdType,
        'family_count': widget.profile.familyCount,
        'monthly_budget': widget.profile.monthlyBudget,
        'meals_per_day': widget.profile.mealsPerDay,
        'purpose': widget.profile.purpose,
        'persona_name': widget.profile.personaName,
        'activity_level': widget.profile.activityLevel,
        'family_members': members,
      });
      if (!mounted) return;
      await ref.read(myPageProvider.notifier).fetchMyProfile();
      if (!mounted) return;
      context.pop();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('저장 중 오류가 발생했어요: $e')),
      );
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(context),
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                itemCount: _forms.length,
                onPageChanged: (i) => setState(() => _currentIndex = i),
                itemBuilder: (context, i) => SingleChildScrollView(
                    padding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
                    child: Column(
                    children: [
                        _buildPageIndicatorRow(context),
                        const SizedBox(height: 16),
                        _MemberFormContent(
                        form: _forms[i],
                        onChanged: () => setState(() {}),
                        ),
                    ],
                    ),
                ),
                ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 8, 24, 16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (_canAdd)
                    TextButton(
                      onPressed: _addMember,
                      child: Text(
                        '+ 구성원 추가하기',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                  if (_canAdd && _canRemove)
                    Text('              ', style: Theme.of(context).textTheme.bodySmall),
                  if (_canRemove)
                    TextButton(
                      onPressed: _removeMember,
                      child: Text(
                        '- 구성원 삭제하기',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
              child: AppPrimaryButton(
                text: '저장하기',
                enabled: _allValid && !_isSaving,
                onPressed: _save,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.chevron_left, size: 32),
            color: AppColors.textPrimary,
            onPressed: () => context.pop(),
          ),
          Expanded(
            child: Text(
              '구성원 정보를 입력해 주세요',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.headlineLarge,
            ),
          ),
          const SizedBox(width: 48),
        ],
      ),
    );
  }

  Widget _buildPageIndicatorRow(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        IconButton(
          icon: const Icon(Icons.chevron_left),
          color: _currentIndex > 0 ? AppColors.textPrimary : AppColors.gray,
          onPressed: _currentIndex > 0 ? _prevPage : null,
        ),
        Text(
          '${_currentIndex + 1}/${_forms.length}',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        IconButton(
          icon: const Icon(Icons.chevron_right),
          color: _currentIndex < _forms.length - 1
              ? AppColors.textPrimary
              : AppColors.gray,
          onPressed: _currentIndex < _forms.length - 1 ? _nextPage : null,
        ),
      ],
    );
  }
}

class _MemberForm {
  String nickname;
  String gender;
  final TextEditingController nicknameCtrl;
  final TextEditingController ageCtrl;
  final TextEditingController heightCtrl;
  final TextEditingController weightCtrl;

  _MemberForm({required this.nickname})
      : gender = '',
        nicknameCtrl = TextEditingController(),
        ageCtrl = TextEditingController(),
        heightCtrl = TextEditingController(),
        weightCtrl = TextEditingController() {
    nicknameCtrl.text = nickname;
  }

  factory _MemberForm.fromInfo(FamilyMemberInfo m) {
    final f = _MemberForm(nickname: m.nickname);
    f.gender = m.gender;
    f.ageCtrl.text = m.age > 0 ? m.age.toString() : '';
    f.heightCtrl.text = m.height > 0 ? m.height.toString() : '';
    f.weightCtrl.text = m.weight > 0 ? m.weight.toString() : '';
    return f;
  }

  void dispose() {
    nicknameCtrl.dispose();
    ageCtrl.dispose();
    heightCtrl.dispose();
    weightCtrl.dispose();
  }

  FamilyMember toMember() => FamilyMember(
        nickname: nicknameCtrl.text,
        gender: gender,
        age: int.tryParse(ageCtrl.text) ?? 0,
        height: double.tryParse(heightCtrl.text) ?? 0,
        weight: double.tryParse(weightCtrl.text) ?? 0,
      );

  Map<String, dynamic> toJson() => toMember().toJson();
}

class _MemberFormContent extends StatefulWidget {
  const _MemberFormContent({
    required this.form,
    required this.onChanged,
  });

  final _MemberForm form;
  final VoidCallback onChanged;

  @override
  State<_MemberFormContent> createState() => _MemberFormContentState();
}

class _MemberFormContentState extends State<_MemberFormContent> {
  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          decoration: BoxDecoration(
            color: AppColors.grayLight,
            borderRadius: BorderRadius.circular(10),
          ),
          child: TextField(
            controller: widget.form.nicknameCtrl,
            onChanged: (_) => widget.onChanged(),
            textAlign: TextAlign.center,
            decoration: InputDecoration(
              border: InputBorder.none,
              isDense: true,
              hintText: '별명을 입력해 주세요',
              hintStyle: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            ),
          ),
        ),
        const SizedBox(height: 16),
        Text(
          '성별',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            {'gender': '남', 'image': 'assets/images/man.png'},
            {'gender': '여', 'image': 'assets/images/woman.png'},
          ].map((item) {
            final g = item['gender']!;
            final image = item['image']!;
            final isSelected = widget.form.gender == g;
            return Expanded(
              child: GestureDetector(
                onTap: () {
                  setState(() => widget.form.gender = g);
                  widget.onChanged();
                },
                child: Container(
                  margin: EdgeInsets.only(right: g == '남' ? 8 : 0),
                  decoration: BoxDecoration(
                    color: isSelected ? AppColors.primaryLight : Colors.white,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: isSelected ? AppColors.primary : AppColors.gray,
                      width: 2,
                    ),
                  ),
                  child: Column(
                    children: [
                      const SizedBox(height: 10),
                      ClipRRect(
                        borderRadius:
                            const BorderRadius.vertical(top: Radius.circular(10)),
                        child: Image.asset(
                          image,
                          width: double.infinity,
                          height: 200,
                          fit: BoxFit.contain,
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        child: Text(
                          g == '남' ? '남자' : '여자',
                          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                color: isSelected
                                    ? AppColors.primary
                                    : AppColors.textPrimary,
                              ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 20),
        _InfoField(
          label: '나이',
          unit: '세',
          controller: widget.form.ageCtrl,
          onChanged: (_) => widget.onChanged(),
        ),
        _InfoField(
          label: '키',
          unit: 'cm',
          controller: widget.form.heightCtrl,
          onChanged: (_) => widget.onChanged(),
          isDecimal: true,
        ),
        _InfoField(
          label: '체중',
          unit: 'kg',
          controller: widget.form.weightCtrl,
          onChanged: (_) => widget.onChanged(),
          isDecimal: true,
        ),
      ],
    );
  }
}

class _InfoField extends StatelessWidget {
  const _InfoField({
    required this.label,
    required this.unit,
    required this.controller,
    required this.onChanged,
    this.isDecimal = false,
  });

  final String label;
  final String unit;
  final TextEditingController controller;
  final ValueChanged<String> onChanged;
  final bool isDecimal;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          SizedBox(
            width: 48,
            child: Text(
              label,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
              decoration: BoxDecoration(
                color: AppColors.grayLight,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: controller,
                      keyboardType: isDecimal
                          ? const TextInputType.numberWithOptions(decimal: true)
                          : TextInputType.number,
                      inputFormatters: [
                        isDecimal
                            ? FilteringTextInputFormatter.allow(
                                RegExp(r'^\d*\.?\d*'))
                            : FilteringTextInputFormatter.digitsOnly,
                      ],
                      onChanged: onChanged,
                      decoration: const InputDecoration(
                        border: InputBorder.none,
                        isDense: true,
                      ),
                    ),
                  ),
                  Text(
                    unit,
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}