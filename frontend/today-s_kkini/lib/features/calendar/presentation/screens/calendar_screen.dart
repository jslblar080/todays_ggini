import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/bottom_nav_bar.dart';
import '../providers/calendar_provider.dart';
import '../widgets/week_grid.dart';
import '../widgets/week_header.dart';
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
            style: Theme.of(context)
                .textTheme
                .bodyMedium
                ?.copyWith(color: AppColors.error),
          ),
        ),
      );
    }

    final label = state.weekLabel;

    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            WeekHeader(
              year: label.year,
              month: label.month,
              weekNumber: label.weekNumber,
              onPrevWeek: notifier.goToPrevWeek,
              onNextWeek: notifier.goToNextWeek,
            ),
            const SizedBox(height: 8),
            Container(
              padding:
                  const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.border, width: 3.0),
                borderRadius: BorderRadius.circular(10),
              ),
              child: state.currentPlan == null
                  ? const Center(child: CircularProgressIndicator())
                  : SummaryCard(
                      month: label.month,
                      totalPrice: state.currentPlan!.totalPricePerMonth,
                      averageCalories:
                          state.currentPlan!.averageCaloriesPerMonth,
                    ),
            ),
            const SizedBox(height: 8),
            WeekGrid(
              weekDays: state.currentWeekDays,
              planFor: state.planFor,
              onDayTap: (date) => context.push(AppRoutes.mealDetailPath(date)),
              onSwap: (from, to) async {
                await notifier.swapDates(from, to);
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}