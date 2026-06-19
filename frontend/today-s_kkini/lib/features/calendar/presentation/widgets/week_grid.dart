import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/format.dart';
import '../../../../core/widgets/popup.dart';
import '../../domain/monthly_meal_plan.dart';

bool _sameYmd(DateTime a, DateTime b) =>
    a.year == b.year && a.month == b.month && a.day == b.day;

class WeekGrid extends StatefulWidget {
  final List<DateTime> weekDays;
  final MonthlyMealPlan? Function(DateTime) planFor;
  final void Function(DateTime) onDayTap;
  final void Function(DateTime from, DateTime to)? onSwap;

  const WeekGrid({
    super.key,
    required this.weekDays,
    required this.planFor,
    required this.onDayTap,
    this.onSwap,
  });

  @override
  State<WeekGrid> createState() => _WeekGridState();
}

class _WeekGridState extends State<WeekGrid> {
  DateTime? _hoveredDate; // 드래그 중 올려진 날짜

  static const _weekdayLabels = ['월', '화', '수', '목', '금', '토', '일'];

  DayEntry? _entryFor(DateTime date) {
    final plan = widget.planFor(date);
    if (plan == null) return null;
    for (final d in plan.days) {
      if (_sameYmd(d.date, date)) return d;
    }
    return null;
  }

  bool _isToday(DateTime date) => _sameYmd(date, DateTime.now());

  @override
  Widget build(BuildContext context) {
    return Column(
      children: List.generate(7, (i) {
        final date = widget.weekDays[i];
        final entry = _entryFor(date);
        final hasPlan = entry?.hasMealPlan == true;
        final isToday = _isToday(date);
        final highlight = _hoveredDate != null && _sameYmd(_hoveredDate!, date);

        Widget cell = _WeekDayRow(
          date: date,
          entry: entry,
          isToday: isToday,
          weekdayLabel: _weekdayLabels[i],
          onTap: hasPlan ? () => widget.onDayTap(date) : null,
          highlight: highlight,
        );

        return DragTarget<DateTime>(
          onWillAcceptWithDetails: (details) =>
              hasPlan && !_sameYmd(details.data, date),
          onMove: (details) {
            if (hasPlan && !_sameYmd(details.data, date)) {
              setState(() => _hoveredDate = date);
            }
          },
          onLeave: (_) {
            if (_hoveredDate != null && _sameYmd(_hoveredDate!, date)) {
              setState(() => _hoveredDate = null);
            }
          },
          onAcceptWithDetails: (details) {
            setState(() => _hoveredDate = null);
            final from = details.data;
            final to = date;
            const weekdays = ['월', '화', '수', '목', '금', '토', '일'];
            showAppPopup(
              context: context,
              content:
                  '${from.month}/${from.day}(${weekdays[from.weekday - 1]})과 '
                  '${to.month}/${to.day}(${weekdays[to.weekday - 1]})의\n식단을 교환하시겠습니까?',
              leftButtonText: '네',
              rightButtonText: '아니요',
              onLeftTap: () {
                Navigator.pop(context);
                widget.onSwap?.call(from, to);
              },
              onRightTap: () => Navigator.pop(context),
              leftButtonColor: AppColors.primary,
              rightButtonColor: AppColors.textPrimary,
            );
          },
          builder: (context, candidate, rejected) {
            if (!hasPlan) return cell;
            return LongPressDraggable<DateTime>(
              data: date,
              feedback: _dragFeedback(context, entry!),
              childWhenDragging: Opacity(opacity: 0.3, child: cell),
              child: cell,
            );
          },
        );
      }),
    );
  }

  Widget _dragFeedback(BuildContext context, DayEntry entry) {
    return Material(
      color: Colors.transparent,
      child: Container(
        width: 140,
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: AppColors.primary.withValues(alpha: 0.92),
          borderRadius: BorderRadius.circular(8),
          boxShadow: const [
            BoxShadow(
                color: Colors.black26, blurRadius: 6, offset: Offset(0, 2)),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${entry.date.month}/${entry.date.day}(${_weekdayLabels[entry.date.weekday - 1]})',
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18),
            ),
            ...entry.meals.take(3).map(
                  (m) => Text(
                    m.menuName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ),
          ],
        ),
      ),
    );
  }
}

class _WeekDayRow extends StatelessWidget {
  final DateTime date;
  final DayEntry? entry;
  final bool isToday;
  final String weekdayLabel;
  final VoidCallback? onTap;
  final bool highlight;

  const _WeekDayRow({
    required this.date,
    required this.entry,
    required this.isToday,
    required this.weekdayLabel,
    required this.highlight,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final hasPlan = entry?.hasMealPlan == true;
    final meals = entry?.meals ?? [];
    final isMany = meals.length >= 4;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: highlight
              ? AppColors.primary.withValues(alpha: 0.1)
              : isToday
                  ? AppColors.primaryLight
                  : AppColors.grayLight,
          borderRadius: BorderRadius.circular(8),
          border: highlight
              ? Border.all(color: AppColors.primary, width: 2)
              : null,
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            SizedBox(
              width: 20,
              child: Text(
                weekdayLabel,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      color: isToday
                          ? AppColors.primary
                          : AppColors.textPrimary,
                    ),
              ),
            ),
            const SizedBox(width: 20),
            if (!hasPlan)
              Expanded(
                child: Text(
                  '식단 없음',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
              )
            else if (!isMany)
              Expanded(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: meals
                            .map(
                              (m) => Text(
                                m.menuName,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: Theme.of(context).textTheme.bodyMedium,
                              ),
                            )
                            .toList(),
                      ),
                    ),
                    const SizedBox(width: 8),
                    _caloriePriceColumn(context),
                  ],
                ),
              )
            else
              Expanded(
                child: IntrinsicHeight(
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // 왼쪽 3개
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: meals
                              .take(3)
                              .map(
                                (m) => Text(
                                  m.menuName,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: Theme.of(context).textTheme.bodyMedium,
                                ),
                              )
                              .toList(),
                        ),
                      ),
                      const SizedBox(width: 8),
                      // 오른쪽 나머지 + 칼로리
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: meals.skip(3).map(
                                    (m) => Text(
                                      m.menuName,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: Theme.of(context).textTheme.bodyMedium,
                                    ),
                                  ).toList(),
                            ),
                            Align(
                              alignment: Alignment.centerRight,
                              child: _caloriePriceColumn(context),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _caloriePriceColumn(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (entry?.caloriesPerDay != null)
          Text(
            '${formatPrice(entry!.caloriesPerDay!)} kcal · ₩${formatPrice(entry!.pricePerDay!)}',
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: AppColors.textSecondary),
          ),
      ],
    );
  }
}