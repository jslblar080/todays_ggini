import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class WeekHeader extends StatelessWidget {
  final int year;
  final int month;
  final int weekNumber;
  final VoidCallback onPrevWeek;
  final VoidCallback onNextWeek;

  const WeekHeader({
    super.key,
    required this.year,
    required this.month,
    required this.weekNumber,
    required this.onPrevWeek,
    required this.onNextWeek,
  });

  static const _weekLabels = ['첫째', '둘째', '셋째', '넷째', '다섯째'];

  String get _label {
    final w = weekNumber.clamp(1, 5) - 1;
    return '$year년 $month월 ${_weekLabels[w]} 주';
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          IconButton(
            icon: const Icon(Icons.chevron_left),
            color: AppColors.textPrimary,
            iconSize: 32,
            onPressed: onPrevWeek,
          ),
          const Spacer(),
          Text(
            _label,
            style: Theme.of(context).textTheme.headlineLarge,
          ),
          const Spacer(),
          IconButton(
            icon: const Icon(Icons.chevron_right),
            color: AppColors.textPrimary,
            iconSize: 32,
            onPressed: onNextWeek,
          ),
        ],
      ),
    );
  }
}