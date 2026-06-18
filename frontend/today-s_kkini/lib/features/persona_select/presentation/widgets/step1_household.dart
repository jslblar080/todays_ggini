import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../../core/theme/app_colors.dart';

class Step1Household extends StatefulWidget {
  const Step1Household({
    super.key,
    required this.selected,
    required this.onChanged,
    required this.familyCount, 
    required this.onFamilyCountChanged,
  });

  final String selected;
  final ValueChanged<String> onChanged;
  final int familyCount;
  final ValueChanged<int> onFamilyCountChanged;

  @override
  State<Step1Household> createState() => _Step1HouseholdState();
}

class _Step1HouseholdState extends State<Step1Household> {
  late final TextEditingController _countCtrl;

  @override
  void initState() {
    super.initState();
    _countCtrl = TextEditingController(
      text: widget.familyCount > 1 ? widget.familyCount.toString() : '',
    );
  }

  @override
  void dispose() {
    _countCtrl.dispose();
    super.dispose();
  }

  static const _options = ['1인 가구', '다인 가구'];
  static const _images = [
    'assets/images/household_single.png',
    'assets/images/household_multi.png',
  ];

  @override
  Widget build(BuildContext context) {
    return ScrollConfiguration(
      behavior: ScrollConfiguration.of(context).copyWith(scrollbars: false),
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Text(
              '어떤 가구 형태인가요?',
              style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                    fontFamily: 'MemomentKkukkukk',
                    fontSize: 30,
                  ),
            ),
            const SizedBox(height: 24),
            ...List.generate(_options.length, (i) {
              final isSelected = widget.selected == _options[i];
              final isMultiSelected = isSelected && _options[i] == '다인 가구';

              return GestureDetector(
                onTap: () => widget.onChanged(_options[i]),
                child: Container(
                  width: double.infinity,
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? AppColors.primaryLight
                        : AppColors.background,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: isSelected ? AppColors.primary : AppColors.gray,
                      width: 3,
                    ),
                  ),
                  child: Column(
                    children: [
                      ClipRRect(
                        borderRadius: const BorderRadius.vertical(
                            top: Radius.circular(10)),
                        child: Image.asset(
                          _images[i],
                          width: double.infinity,
                          height: 200,
                          fit: BoxFit.cover,
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(
                            vertical: 12, horizontal: 16),
                        child: isMultiSelected
                            ? Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text(
                                    '총 ',
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodyLarge
                                        ?.copyWith(color: AppColors.primary),
                                  ),
                                  SizedBox(
                                    width: 20,
                                    child: TextField(
                                      controller: _countCtrl,
                                      keyboardType: TextInputType.number,
                                      inputFormatters: [
                                        FilteringTextInputFormatter.digitsOnly,
                                      ],
                                      textAlign: TextAlign.center,
                                      style: Theme.of(context)
                                          .textTheme
                                          .bodyLarge
                                          ?.copyWith(
                                            color: AppColors.primary,
                                          ),
                                      decoration: const InputDecoration(
                                        isDense: true,
                                        enabledBorder: UnderlineInputBorder(
                                          borderSide: BorderSide(
                                              color: AppColors.primary, width: 2),
                                        ),
                                        focusedBorder: UnderlineInputBorder(
                                          borderSide: BorderSide(
                                              color: AppColors.primary, width: 2),
                                        ),
                                      ),
                                      onChanged: (v) {
                                        final parsed = int.tryParse(v);
                                        if (parsed != null && parsed >= 2) {
                                          widget.onFamilyCountChanged(parsed);
                                        }
                                      },
                                    ),
                                  ),
                                  Text(
                                    '인 가구',
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodyLarge
                                        ?.copyWith(color: AppColors.primary),
                                  ),
                                ],
                              )
                            : Text(
                                _options[i],
                                style: Theme.of(context)
                                    .textTheme
                                    .bodyLarge
                                    ?.copyWith(
                                      color: isSelected
                                          ? AppColors.primary
                                          : AppColors.textPrimary,
                                    ),
                              ),
                      ),
                    ],
                  ),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}