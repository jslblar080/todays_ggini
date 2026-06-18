import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../../core/theme/app_colors.dart';
import '../../domain/persona_input.dart';

class Step2BasicInfo extends StatefulWidget {
  const Step2BasicInfo({
    super.key,
    required this.householdType,
    required this.members,
    required this.onChanged,
  });

  final String householdType;
  final List<FamilyMember> members;
  final ValueChanged<List<FamilyMember>> onChanged;

  @override
  State<Step2BasicInfo> createState() => _Step2BasicInfoState();
}

class _Step2BasicInfoState extends State<Step2BasicInfo> {
  late List<_MemberForm> _forms;
  final _pageController = PageController();
  int _currentMember = 0;

  @override
  void initState() {
    super.initState();
    if (widget.members.isEmpty) {
      _forms = [_MemberForm(nickname: '')];
    } else {
      _forms = widget.members.map((m) => _MemberForm.fromMember(m)).toList();
    }
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _notify() {
    widget.onChanged(_forms.map((f) => f.toMember()).toList());
  }

  void _addMember() {
    setState(() {
      _forms.add(_MemberForm(nickname: ''));
    });
    _notify();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _pageController.animateToPage(
        _forms.length - 1,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    });
  }

  void _prevMember() {
    _pageController.previousPage(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  void _nextMember() {
    _pageController.nextPage(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  @override
  Widget build(BuildContext context) {
    final isMulti = widget.householdType == '다인 가구';

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(
            isMulti ? '대표자 정보를 입력해 주세요' : '기본 정보를 입력해 주세요',
            style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                  fontFamily: 'MemomentKkukkukk',
                  fontSize: 30,
                ),
          ),
          if (isMulti) ...[
            const SizedBox(height: 8),
            Text(
              '구성원 정보는 나중에 추가할 수 있어요.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            ),
          ],
          const SizedBox(height: 24),

          // 항상 1명만 표시
          _MemberFormContent(
            form: _forms[0],
            onChanged: () {
              setState(() {});
              _notify();
            },
            showNickname: false,
          ),

          const SizedBox(height: 24),
        ],
      ),
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

  factory _MemberForm.fromMember(FamilyMember m) {
    final f = _MemberForm(nickname: m.nickname);
    f.gender = m.gender;
    f.ageCtrl.text = m.age.toString();
    f.heightCtrl.text = m.height.toString();
    f.weightCtrl.text = m.weight.toString();
    return f;
  }

  FamilyMember toMember() => FamilyMember(
        nickname: nicknameCtrl.text,
        gender: gender,
        age: int.tryParse(ageCtrl.text) ?? 0,
        height: double.tryParse(heightCtrl.text) ?? 0,
        weight: double.tryParse(weightCtrl.text) ?? 0,
      );
}

class _MemberFormContent extends StatefulWidget {
  const _MemberFormContent({
    required this.form,
    required this.onChanged,
    this.showNickname = true,
  });

  final _MemberForm form;
  final VoidCallback onChanged;
  final bool showNickname;

  @override
  State<_MemberFormContent> createState() => _MemberFormContentState();
}

class _MemberFormContentState extends State<_MemberFormContent> {
  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (widget.showNickname) ...[
          // 별명 입력
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
        ],

        // 성별 라벨
        Text(
          '성별',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        const SizedBox(height: 8),

        // 성별 선택
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