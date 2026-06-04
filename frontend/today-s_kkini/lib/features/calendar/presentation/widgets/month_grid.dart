import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart'; // ← 추가
import '../../domain/monthly_meal_plan.dart';
import 'day_cell.dart';

// 연/월/일이 같은 날짜인지 비교 (시각 무시)
bool _sameYmd(DateTime a, DateTime b) =>
    a.year == b.year && a.month == b.month && a.day == b.day;

class MonthGrid extends StatelessWidget {
  final int year;
  final int month;
  final MonthlyMealPlan plan;
  final void Function(DateTime date) onDayTap;

  // 드래그-앤-드롭 식단 교환: from(끌어온 날)을 to(놓은 날)에 떨어뜨림
  final void Function(DateTime from, DateTime to)? onSwap;

  const MonthGrid({
    super.key,
    required this.year,
    required this.month,
    required this.plan,
    required this.onDayTap,
    this.onSwap,
  });

  bool _isToday(int year, int month, int day) {
    final now = DateTime.now();
    return now.year == year && now.month == month && now.day == day;
  }

  @override
  Widget build(BuildContext context) {
    final dayMap = <int, DayEntry>{for (final d in plan.days) d.date.day: d};

    final firstDay = DateTime(year, month, 1);
    final firstWeekday = firstDay.weekday;
    final daysInMonth = DateTime(year, month + 1, 0).day;

    final leadingEmpty = firstWeekday - 1;
    final totalCells = ((leadingEmpty + daysInMonth + 6) ~/ 7) * 7;
    final trailingEmpty = totalCells - leadingEmpty - daysInMonth;

    // 한 날짜 셀: 식단 있는 날은 끌 수 있고(LongPressDraggable),
    // 식단 있는 날끼리 서로 드롭 대상(DragTarget)이 된다.
    Widget buildDay(int d) {
      final entry = dayMap[d];
      final cellDate = DateTime(year, month, d);
      final hasPlan = entry?.hasMealPlan == true;

      return DragTarget<DateTime>(
        // 식단 있는 날에, 자기 자신이 아닌 날을 떨어뜨릴 때만 수락
        onWillAcceptWithDetails: (details) =>
            hasPlan && !_sameYmd(details.data, cellDate),
        onAcceptWithDetails: (details) => onSwap?.call(details.data, cellDate),
        builder: (context, candidate, rejected) {
          final highlight = candidate.isNotEmpty; // 드롭 가능한 셀 위에 떠 있음
          final cell = DayCell(
            day: entry,
            isToday: _isToday(year, month, d),
            highlight: highlight,
            onTap: hasPlan ? () => onDayTap(cellDate) : null, // 탭=상세 이동
          );

          // 식단 없는 날은 끌 수 없음 (드롭 대상으로도 거절)
          if (!hasPlan) return cell;

          return LongPressDraggable<DateTime>(
            data: cellDate,
            feedback: _dragFeedback(context, entry!),
            childWhenDragging: Opacity(opacity: 0.3, child: cell),
            child: cell,
          );
        },
      );
    }

    final cells = <Widget>[
      for (var i = 0; i < leadingEmpty; i++) const DayCell(day: null),
      for (var d = 1; d <= daysInMonth; d++) buildDay(d),
      for (var i = 0; i < trailingEmpty; i++) const DayCell(day: null),
    ];

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: Column(
        children: [
          _weekdayHeader(context),
          Container(
            decoration: const BoxDecoration(
              border: Border(
                left: BorderSide(color: AppColors.border, width: 1), 
              ),
            ),
            child: GridView.count(
              crossAxisCount: 7,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              childAspectRatio: 0.55,
              children: cells,
            ),
          ),
        ],
      ),
    );
  }

  // 드래그 중 손가락을 따라다니는 미리보기 카드
  Widget _dragFeedback(BuildContext context, DayEntry entry) {
    return Material(
      color: Colors.transparent,
      child: Container(
        width: 92,
        padding: const EdgeInsets.all(6),
        decoration: BoxDecoration(
          color: AppColors.primary.withValues(alpha: 0.92),
          borderRadius: BorderRadius.circular(6),
          boxShadow: const [
            BoxShadow(color: Colors.black26, blurRadius: 6, offset: Offset(0, 2)),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${entry.date.day}일',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 11,
                fontWeight: FontWeight.bold,
              ),
            ),
            ...entry.meals.take(2).map(
                  (m) => Text(
                    m.menuName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.white, fontSize: 10),
                  ),
                ),
          ],
        ),
      ),
    );
  }

  Widget _weekdayHeader(BuildContext context) {
    const labels = ['월', '화', '수', '목', '금', '토', '일'];
    return Row(
      children:
          labels
              .map(
                (l) => Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    decoration: const BoxDecoration(
                      border: Border(
                        bottom: BorderSide(color: AppColors.border, width: 1),
                      ),
                    ),
                    child: Center(
                      child: Text(
                        l,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ),
                  ),
                ),
              )
              .toList(),
    );
  }
}
