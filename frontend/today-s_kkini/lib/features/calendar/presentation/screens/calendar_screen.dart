import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/bottom_nav_bar.dart';
import '../providers/calendar_provider.dart';
import '../widgets/month_grid.dart';
import '../widgets/month_header.dart';
import '../widgets/summary_card.dart';

class CalendarScreen extends ConsumerWidget {
  const CalendarScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(calendarProvider);
    final notifier = ref.read(calendarProvider.notifier);

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: _buildBody(context, state, notifier),
      ),
      bottomNavigationBar: const BottomNavBar(currentIndex: 1),
    );
  }

  Widget _buildBody(
    BuildContext context,
    CalendarState state,
    CalendarNotifier notifier,
  ) {
    if (state.error != null && state.currentPlan == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            '캘린더를 불러오지 못했습니다.\n${state.error}',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: AppColors.error,
          ),
          ),
        ),
      );
    }

    if (state.currentPlan == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final plan = state.currentPlan!;

    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            MonthHeader(
              year: state.currentYear,
              month: state.currentMonth,
              onPrevMonth: notifier.goToPrevMonth,
              onNextMonth: notifier.goToNextMonth,
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.border, width: 3.0),
                borderRadius: BorderRadius.circular(8),
              ),
              child: SummaryCard(
                month: state.currentMonth,
                totalPrice: plan.totalPricePerMonth,
                averageCalories: plan.averageCaloriesPerMonth,
              ),
            ),
            const SizedBox(height: 8),
            MonthGrid(
              year: state.currentYear,
              month: state.currentMonth,
              plan: plan,
              onDayTap: (date) {
                context.push(AppRoutes.mealDetailPath(date));
              },
              onSwap: (from, to) => _handleSwap(context, notifier, from, to),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  // 드롭 시: 즉시 교환 → "교환했어요 [실행취소]" SnackBar.
  // 실행취소는 같은 두 날짜를 다시 교환하면 원래대로 돌아간다.
  Future<void> _handleSwap(
    BuildContext context,
    CalendarNotifier notifier,
    DateTime from,
    DateTime to,
  ) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      await notifier.swapDates(from, to);
      messenger
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: const Text('식단을 교환했어요.'),
            action: SnackBarAction(
              label: '실행취소',
              onPressed: () => notifier.swapDates(to, from),
            ),
          ),
        );
    } catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text('교환에 실패했어요: $e')),
      );
    }
  }
}
