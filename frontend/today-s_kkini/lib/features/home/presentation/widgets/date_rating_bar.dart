import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/popup.dart';
import '../providers/home_provider.dart';

class DateRatingBar extends ConsumerStatefulWidget {
  const DateRatingBar({super.key});

  @override
  ConsumerState<DateRatingBar> createState() => _DateRatingBarState();
}

class _DateRatingBarState extends ConsumerState<DateRatingBar> {
  final DateTime _today = DateTime.now();
  final Map<int, int> _ratings = {};
  late final PageController _pageController;
  late final DateTime _baseWeekStart; // 기준 주(오늘 포함)
  int _currentPage = 500; // 충분히 큰 중간값

  static const _weekdayLabels = ['월', '화', '수', '목', '금', '토', '일'];

  @override
  void initState() {
    super.initState();
    final todayWeekday = _today.weekday;
    _baseWeekStart = DateTime(
      _today.year,
      _today.month,
      _today.day - (todayWeekday - 1),
    );
    _pageController = PageController(initialPage: _currentPage);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  DateTime _weekStartFor(int page) {
    final offset = page - 500;
    return _baseWeekStart.add(Duration(days: offset * 7));
  }

  List<DateTime> _weekDaysFor(DateTime weekStart) =>
      List.generate(7, (i) => weekStart.add(Duration(days: i)));

  bool _isToday(DateTime date) =>
      date.year == _today.year &&
      date.month == _today.month &&
      date.day == _today.day;

  bool _isPast(DateTime date) => date.isBefore(_today) || _isToday(date);

  String _starImage(int rating) => 'assets/images/star$rating.png';

  Future<void> _onDateTap(DateTime date) async {
    final repository = ref.read(homeRepositoryProvider);
    try {
      final plan = await repository.fetchDailyMealPlan(date);
      if (plan.meals.isEmpty) {
        if (!mounted) return;
        showAppPopupSingle(
          context: context,
          content: '해당 날짜의 식단이 존재하지 않습니다.',
        );
        return;
      }
      if (!mounted) return;
      await ref.read(homeProvider.notifier).loadDate(date);
    } catch (e) {
      if (!mounted) return;
      showAppPopupSingle(
        context: context,
        content: '해당 날짜의 식단이 존재하지 않습니다.',
      );
    }
  }

  void _showRatingDialog(DateTime date) {
    int selectedRating = _ratings[date.millisecondsSinceEpoch] ?? 0;
    List<String> selectedReasons = [];

    const reasons = ['다양성', '예산', '칼로리', '취향', '요리 난이도', '목적'];

    showAppPopupWidget(
      context: context,
      title: '오늘의 식단은 어떠셨나요?',
      contentWidget: StatefulBuilder(
        builder: (ctx, setDialogState) => Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 별점
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(5, (i) {
                final star = i + 1;
                return GestureDetector(
                  onTap: () => setDialogState(() => selectedRating = star),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    child: Icon(
                      star <= selectedRating ? Icons.star : Icons.star_border,
                      color:
                          star <= selectedRating ? Colors.amber : AppColors.gray,
                      size: 36,
                    ),
                  ),
                );
              }),
            ),

            // 피드백 선택 (별점 2 이하일 때)
            if (selectedRating > 0 && selectedRating <= 2) ...[
              const SizedBox(height: 16),
              Text(
                '해당 별점을 남긴 이유를 선택해 주세요.',
                style: Theme.of(ctx).textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: reasons.map((reason) {
                  final isSelected = selectedReasons.contains(reason);
                  return GestureDetector(
                    onTap: () {
                      setDialogState(() {
                        if (isSelected) {
                          selectedReasons.remove(reason);
                        } else {
                          selectedReasons.add(reason);
                        }
                      });
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: isSelected ? AppColors.primary : Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color:
                              isSelected ? AppColors.primary : AppColors.gray,
                        ),
                      ),
                      child: Text(
                        reason,
                        style: Theme.of(ctx).textTheme.bodySmall?.copyWith(
                              color: isSelected
                                  ? Colors.white
                                  : AppColors.textPrimary,
                            ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ],
          ],
        ),
      ),
      leftButtonText: '취소',
      rightButtonText: '확인',
      onLeftTap: () => Navigator.pop(context),
      onRightTap: () {
        if (selectedRating > 0) {
          setState(() {
            _ratings[date.millisecondsSinceEpoch] = selectedRating;
          });
          // TODO: API 저장 (selectedReasons 포함)
        }
        Navigator.pop(context);
      },
    );
  }

  Widget _buildWeek(BuildContext context, DateTime weekStart) {
    final weekDays = _weekDaysFor(weekStart);
    final selectedDate = ref.watch(homeProvider.select((s) => s.selectedDate));

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: List.generate(7, (i) {
        final date = weekDays[i];
        final isToday = _isToday(date);
        final isPast = _isPast(date);
        final isSelected = selectedDate != null &&
            selectedDate.year == date.year &&
            selectedDate.month == date.month &&
            selectedDate.day == date.day;
        final rating = _ratings[date.millisecondsSinceEpoch];

        return SizedBox(
          width: 40,
          child: Column(
            children: [
              Text(
                _weekdayLabels[i],
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppColors.textSecondary,
                    ),
              ),
              const SizedBox(height: 4),
              GestureDetector(
                onTap: () => _onDateTap(date),
                child: Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: isToday
                        ? AppColors.primary
                        : isSelected
                            ? AppColors.primaryLight
                            : Colors.transparent,
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      '${date.day}',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: isToday ? Colors.white : AppColors.textPrimary,
                          ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 4),
              if (isPast)
                GestureDetector(
                  onTap: () => _showRatingDialog(date),
                  child: rating != null
                      ? Image.asset(
                          _starImage(rating),
                          width: 28,
                          height: 28,
                          fit: BoxFit.contain,
                        )
                      : const Icon(
                          Icons.star,
                          size: 24,
                          color: AppColors.gray,
                        ),
                )
              else
                const SizedBox(height: 28),
            ],
          ),
        );
      }),
    );
  }

  @override
  Widget build(BuildContext context) {
    final weekStart = _weekStartFor(_currentPage);

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Text(
            '${weekStart.year}년 ${weekStart.month}월',
            style: Theme.of(context).textTheme.headlineLarge,
          ),
        ),
        const SizedBox(height: 20),
        SizedBox(
          height: 90,
          child: PageView.builder(
            controller: _pageController,
            onPageChanged: (page) => setState(() => _currentPage = page),
            itemBuilder: (context, page) {
              final ws = _weekStartFor(page);
              return _buildWeek(context, ws);
            },
          ),
        ),
      ],
    );
  }
}