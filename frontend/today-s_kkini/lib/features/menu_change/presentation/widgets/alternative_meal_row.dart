import 'package:flutter/material.dart';
import 'package:auto_size_text/auto_size_text.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/format.dart';
import '../../domain/menu_alternatives.dart';

class AlternativeMealRow extends StatelessWidget {
  final AlternativeMeal meal;
  final bool isDisabled;
  final VoidCallback onChange;

  const AlternativeMealRow({
    super.key,
    required this.meal,
    required this.isDisabled,
    required this.onChange,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              _Thumbnail(imageUrl: meal.imageUrl),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AutoSizeText(
                      meal.menuName,
                      maxLines: 1,
                      minFontSize: 10,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${formatPrice(meal.calories)} kcal · ₩${formatPrice(meal.price)}',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppColors.textPrimary,
                          ),
                    ),
                  ],
                ),
              ),
              GestureDetector(
                onTap: isDisabled ? null : onChange,
                child: Container(
                  width: 90,
                  height: 34,
                  decoration: const BoxDecoration(
                    color: AppColors.grayLight,
                    borderRadius: BorderRadius.zero,
                  ),
                  child: Center(
                    child: Text(
                      '메뉴 변경',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: isDisabled
                                ? AppColors.primary
                                : AppColors.textPrimary,
                          ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
        const Divider(height: 3, color: AppColors.border),
      ],
    );
  }
}

class _Thumbnail extends StatelessWidget {
  final String? imageUrl;

  const _Thumbnail({this.imageUrl});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 56,
      height: 56,
      decoration: BoxDecoration(
        color: AppColors.grayLight,
        borderRadius: BorderRadius.circular(10),
      ),
      child: imageUrl == null
          ? null
          : ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: Image.network(
                imageUrl!,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) => const SizedBox(),
              ),
            ),
    );
  }
}