import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:auto_size_text/auto_size_text.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/widgets/app_primary_button.dart';
import '../../../../core/widgets/bottom_nav_bar.dart';
import '../../domain/menu_detail.dart';
import '../providers/home_provider.dart';
import '../widgets/date_rating_bar.dart';
import '../widgets/ingredient_card.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(homeProvider);

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [Expanded(child: _buildBody(context, ref, state))],
        ),
      ),
      bottomNavigationBar: const BottomNavBar(currentIndex: 0),
    );
  }

  Widget _buildBody(BuildContext context, WidgetRef ref, HomeState state) {
    if (state.error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            '식단을 불러오지 못했습니다.\n${state.error}',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.error,
                ),
          ),
        ),
      );
    }

    if (state.dailyPlan == null) {
      return const Center(child: CircularProgressIndicator());
    }

    return Column(
      children: [
        const Padding(
          padding: EdgeInsets.only(top: 10, bottom: 5),
          child: DateRatingBar(),
        ),

        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            child: Column(
              children: [
                _buildMenuCard(context, ref, state),
                const SizedBox(height: 20),
                if (state.selectedMenu != null) ...[
                  const Divider(height: 3, color: AppColors.border),
                  ...List.generate(
                    state.selectedMenu!.ingredients.length,
                    (i) => IngredientCard(
                      index: i + 1,
                      ingredient: state.selectedMenu!.ingredients[i],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),

        Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 16),
          child: AppPrimaryButton(
            text: '재료 선택 및 메뉴 변경',
            enabled: state.selectedMenu != null,
            onPressed: () {
              context.push(AppRoutes.mealDetailPath(DateTime.now()));
            },
          ),
        ),
      ],
    );
  }

  Widget _buildMenuCard(BuildContext context, WidgetRef ref, HomeState state) {
    final plan = state.dailyPlan!;

    return Column(
      children: [
        // 탭 부분 (별도 Row)
        Row(
          children: List.generate(plan.meals.length, (i) {
            final slot = i + 1;
            final isSelected = slot == state.selectedSlot;
            return Expanded(
              child: GestureDetector(
                onTap: () => ref.read(homeProvider.notifier).selectSlot(slot),
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? AppColors.border
                        : AppColors.grayLight,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(10),
                    ),
                  ),
                  child: Center(
                    child: Text(
                      '식단 $slot',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            color: isSelected
                                ? AppColors.textPrimary
                                : AppColors.textSecondary,
                          ),
                    ),
                  ),
                ),
              ),
            );
          }),
        ),

        // 컨텐츠 박스 (별도 Container)
        Container(
          width: double.infinity,
          decoration: const BoxDecoration(
            color: AppColors.border,
            borderRadius: BorderRadius.only(
              bottomLeft: Radius.circular(10),
              bottomRight: Radius.circular(10),
            ),
          ),
          padding: const EdgeInsets.all(12),
          child: state.isLoadingMenu || state.selectedMenu == null
              ? const Padding(
                  padding: EdgeInsets.symmetric(vertical: 60),
                  child: Center(child: CircularProgressIndicator()),
                )
              : _buildMenuDetail(context, state.selectedMenu!),
        ),
      ],
    );
  }

  Widget _buildMenuDetail(BuildContext context, MenuDetail menu) {
    return Column(
      children: [
        AutoSizeText(
          menu.menuName,
          maxLines: 1,
          minFontSize: 14,
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontFamily: 'MemomentKkukkukk',
              ),
        ),
        const SizedBox(height: 12),

        AspectRatio(
          aspectRatio: 16 / 9,
          child: Container(
            decoration: BoxDecoration(
              color: AppColors.background,
              borderRadius: BorderRadius.circular(10),
            ),
            child: menu.imageUrl != null
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(10),
                    child: Image.network(
                      menu.imageUrl!,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => const Center(
                        child: Icon(Icons.image_not_supported,
                            color: AppColors.grayLight),
                      ),
                    ),
                  )
                : const SizedBox(),
          ),
        ),

        const SizedBox(height: 12),

        GestureDetector(
          onTap: () async {
            if (menu.videoUrl == null) return;
            final uri = Uri.parse(menu.videoUrl!);
            if (await canLaunchUrl(uri)) {
              await launchUrl(uri, mode: LaunchMode.externalApplication);
            }
          },
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 28,
                height: 20,
                decoration: BoxDecoration(
                  color: Colors.red,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Icon(Icons.play_arrow,
                    color: Colors.white, size: 16),
              ),
              const SizedBox(width: 8),
              Text(
                '레시피 보러 가기',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ],
    );
  }
}