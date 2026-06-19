import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class MealSlotTabs extends StatelessWidget {
  final int slotCount;
  final int selectedSlot;
  final ValueChanged<int> onSlotSelected;

  const MealSlotTabs({
    super.key,
    required this.slotCount,
    required this.selectedSlot,
    required this.onSlotSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.grayLight,
        borderRadius: BorderRadius.circular(12),
      ),
      padding: const EdgeInsets.all(4),
      child: Row(
        children: List.generate(slotCount, (i) {
          final slot = i + 1;
          final isSelected = slot == selectedSlot;

          return Expanded(
            child: GestureDetector(
              onTap: () => onSlotSelected(slot),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  color: isSelected ? Colors.white : Colors.transparent,
                  borderRadius: BorderRadius.circular(10),
                  boxShadow: isSelected
                      ? [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.08),
                            blurRadius: 4,
                            offset: const Offset(0, 2),
                          )
                        ]
                      : null,
                ),
                child: Center(
                  child: Text(
                    '식단 $slot',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: isSelected
                              ? AppColors.textPrimary
                              : AppColors.textSecondary,
                          fontWeight: isSelected
                              ? FontWeight.w600
                              : FontWeight.normal,
                        ),
                  ),
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}