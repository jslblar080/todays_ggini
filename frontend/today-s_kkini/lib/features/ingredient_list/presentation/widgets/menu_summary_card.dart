import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/format.dart';
import '../../../home/domain/menu_detail.dart';
import 'package:auto_size_text/auto_size_text.dart';

class MenuSummaryCard extends StatelessWidget {
  final MenuDetail menu;
  final DateTime? sourceDate;
  final int? sourceSlot;

  const MenuSummaryCard({
    super.key,
    required this.menu,
    this.sourceDate,
    this.sourceSlot,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.border, width: 3),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 70,
            height: 70,
            decoration: BoxDecoration(
              color: AppColors.border,
              borderRadius: BorderRadius.circular(6),
            ),
            child:
                menu.imageUrl == null
                    ? Center(
                      child: Text(
                        '이미지',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    )
                    : ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: Image.network(menu.imageUrl!, fit: BoxFit.cover),
                    ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 3),
                AutoSizeText(
                  menu.menuName,
                  maxLines: 1,
                  minFontSize: 12,
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                const SizedBox(height: 4),
                Text(
                  '${formatPrice(menu.calories)} kcal',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                if (sourceDate != null || sourceSlot != null) ...[
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
