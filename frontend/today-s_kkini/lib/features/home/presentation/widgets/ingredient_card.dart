import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/format.dart';
import '../../domain/menu_detail.dart';

class IngredientCard extends StatelessWidget {
  final int index;
  final Ingredient ingredient;

  const IngredientCard({
    super.key,
    required this.index,
    required this.ingredient,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          height: 70,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // 이미지
              SizedBox(
                width: 50,
                height: 50,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: ingredient.imageUrl == null
                      ? Container(color: AppColors.grayLight)
                      : Image.network(
                          ingredient.imageUrl!,
                          fit: BoxFit.cover,
                        ),
                ),
              ),
              const SizedBox(width: 12),
              // 재료명
              Expanded(
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    ingredient.ingredientName,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ),
              ),
              // 가격
              Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _priceRow(context, '쿠팡', ingredient.prices.coupang,
                      isLowest: ingredient.lowestPrice.market == 'coupang'),
                  _priceRow(context, '컬리', ingredient.prices.marketKurly,
                      isLowest: ingredient.lowestPrice.market == 'market_kurly'),
                  _priceRow(context, '네이버', ingredient.prices.naverShopping,
                      isLowest: ingredient.lowestPrice.market == 'naver_shopping'),
                ],
              ),
            ],
          ),
        ),
        const Divider(height: 3, color: AppColors.border),
      ],
    );
  }

  Widget _priceRow(BuildContext context, String marketName, int? price,
      {required bool isLowest}) {
    final isAvailable = price != null;
    final color = !isAvailable
        ? AppColors.textSecondary
        : isLowest
            ? AppColors.primary
            : AppColors.textPrimary;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 1),
      child: Row(
        children: [
          SizedBox(
            width: 60,
            child: Text(
              marketName,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: color,
                  ),
            ),
          ),
          SizedBox(
            width: 75,
            child: Text(
              isAvailable ? '₩${formatPrice(price)}' : '재고 없음',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: color,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}