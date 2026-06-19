import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import 'package:flutter/services.dart'; 

class Step3DietInfo extends StatelessWidget {
  const Step3DietInfo({
    super.key,
    required this.mealsPerDay,
    required this.monthlyBudget,
    required this.onMealsChanged,
    required this.onBudgetChanged,
  });

  final int mealsPerDay;
  final int monthlyBudget;
  final ValueChanged<int> onMealsChanged;
  final ValueChanged<int> onBudgetChanged;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Text(
              '식단 정보를 입력해 주세요',
              style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                    fontFamily: 'MemomentKkukkukk',
                    fontSize: 34,
                  ),
            ),
          ),
          const SizedBox(height: 100),

          // 하루 몇 끼
          Text(
            '하루에 몇끼 드시나요?',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              GestureDetector(
                onTap: mealsPerDay > 1
                    ? () => onMealsChanged(mealsPerDay - 1)
                    : null,
                child: Icon(
                  Icons.remove,
                  size: 20,
                  color: mealsPerDay > 1
                      ? AppColors.textPrimary
                      : AppColors.gray,
                ),
              ),
              const SizedBox(width: 32),
              Column(
                children: [
                  Text(
                    '$mealsPerDay',
                    style: Theme.of(context)
                        .textTheme
                        .bodyLarge,
                  ),
                  Container(
                    width: 100,
                    height: 1,
                    color: AppColors.textPrimary,
                  ),
                ],
              ),
              const SizedBox(width: 32),
              GestureDetector(
                onTap: mealsPerDay < 5
                    ? () => onMealsChanged(mealsPerDay + 1)
                    : null,
                child: Icon(
                  Icons.add,
                  size: 20,
                  color: mealsPerDay < 5
                      ? AppColors.textPrimary
                      : AppColors.gray,
                ),
              ),
            ],
          ),

          const SizedBox(height: 100),

          // 한달 예산
          Text(
            '한달 예산은 얼마인가요?',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 4),
          Text(
            '최소 30만원부터, 5만원 단위로 입력해 주세요.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 16),
          _BudgetField(
            value: monthlyBudget,
            onChanged: onBudgetChanged,
          ),
        ],
      ),
    );
  }
}

class _BudgetField extends StatefulWidget {
  const _BudgetField({required this.value, required this.onChanged});

  final int value;
  final ValueChanged<int> onChanged;

  @override
  State<_BudgetField> createState() => _BudgetFieldState();
}

class _BudgetFieldState extends State<_BudgetField> {
  late final TextEditingController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(
      text: widget.value == 0 ? '' : (widget.value ~/ 10000).toString(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
      decoration: BoxDecoration(
        color: AppColors.grayLight,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _ctrl,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              onChanged: (v) {
                final parsed = int.tryParse(v);
                if (parsed != null) widget.onChanged(parsed * 10000);
              },
              decoration: const InputDecoration(
                border: InputBorder.none,
                isDense: true,
              ),
            ),
          ),
          Text(
            '만원',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: AppColors.textSecondary,
                ),
          ),
        ],
      ),
    );
  }
}