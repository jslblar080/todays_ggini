import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../providers/persona_select_provider.dart';

class Step6PersonaResult extends ConsumerWidget {
  const Step6PersonaResult({
    super.key,
    required this.selectedPersonaName,
    required this.onSelected,
  });

  final String? selectedPersonaName;
  final void Function(String name, String personaId) onSelected;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recommended = ref.watch(recommendedPersonasProvider);

    return recommended.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(
        child: Text('추천 정보를 불러오지 못했어요.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.error)),
      ),
      data: (personas) => SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Text(
              '페르소나를 선택해 주세요',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                    fontFamily: 'MemomentKkukkukk',
                    fontSize: 34,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              '분석된 정보를 바탕으로 추천드려요',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 24),

            GridView.count(
              crossAxisCount: 2,
              crossAxisSpacing: 20,
              mainAxisSpacing: 20,
              childAspectRatio: 0.65,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              children: personas.map((persona) {
                final isSelected = selectedPersonaName == persona.name;
                return _PersonaCard(
                  persona: persona,
                  isSelected: isSelected,
                  onSelected: () => onSelected(persona.name, persona.personaId),
                );
              }).toList(),
            ),

            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}

class _PersonaCard extends StatefulWidget {
  const _PersonaCard({
    required this.persona,
    required this.isSelected,
    required this.onSelected,
  });

  final RecommendedPersona persona;
  final bool isSelected;
  final VoidCallback onSelected;

  @override
  State<_PersonaCard> createState() => _PersonaCardState();
}

class _PersonaCardState extends State<_PersonaCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;
  bool _isFlipped = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 400),
      vsync: this,
    );
    _animation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _flip() {
    if (_isFlipped) {
      _controller.reverse();
    } else {
      _controller.forward();
    }
    setState(() => _isFlipped = !_isFlipped);
  }

  String _imagePath(String personaId) {
    const images = {
      // 1인 가구
      'persona_single_budget_saver': 'assets/images/persona_single_budget_saver.png',
      'persona_single_diet_light': 'assets/images/persona_single_diet_light.png',
      'persona_single_high_protein': 'assets/images/persona_single_high_protein.png',
      'persona_single_easy_cooking': 'assets/images/persona_single_easy_cooking.png',
      'persona_single_balanced_routine': 'assets/images/persona_single_balanced_routine.png',
      'persona_single_taste_focused': 'assets/images/persona_single_taste_focused.png',
      'persona_single_diet_protein': 'assets/images/persona_single_diet_protein.png',
      'persona_single_budget_easy': 'assets/images/persona_single_budget_easy.png',
      'persona_single_diet_easy': 'assets/images/persona_single_diet_easy.png',
      'persona_single_variety_seeker': 'assets/images/persona_single_variety_seeker.png',
      // 다인 가구
      'persona_multi_budget_planner': 'assets/images/persona_multi_budget_planner.png',
      'persona_multi_balanced_family': 'assets/images/persona_multi_balanced_family.png',
      'persona_multi_easy_shared_meal': 'assets/images/persona_multi_easy_shared_meal.png',
      'persona_multi_high_protein_family': 'assets/images/persona_multi_high_protein_family.png',
      'persona_multi_diet_support': 'assets/images/persona_multi_diet_support.png',
      'persona_multi_taste_balance': 'assets/images/persona_multi_taste_balance.png',
      'persona_multi_budget_balance': 'assets/images/persona_multi_budget_balance.png',
      'persona_multi_budget_easy': 'assets/images/persona_multi_budget_easy.png',
      'persona_multi_health_routine': 'assets/images/persona_multi_health_routine.png',
      'persona_multi_variety_table': 'assets/images/persona_multi_variety_table.png',
    };
    return images[personaId] ?? 'assets/images/persona_default.png';
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: _flip,
      child: AnimatedBuilder(
        animation: _animation,
        builder: (context, child) {
          final angle = _animation.value * 3.14159;
          final isShowingBack = angle > 1.5708;

          return Transform(
            alignment: Alignment.center,
            transform: Matrix4.identity()
              ..setEntry(3, 2, 0.001)
              ..rotateY(angle),
            child: isShowingBack
                ? Transform(
                    alignment: Alignment.center,
                    transform: Matrix4.identity()..rotateY(3.14159),
                    child: _BackSide(
                      persona: widget.persona,
                      isSelected: widget.isSelected,
                      onSelected: widget.onSelected,
                    ),
                  )
                : _FrontSide(
                    persona: widget.persona,
                    isSelected: widget.isSelected,
                    imagePath: _imagePath(widget.persona.personaId),
                  ),
          );
        },
      ),
    );
  }
}

class _FrontSide extends StatelessWidget {
  const _FrontSide({
    required this.persona,
    required this.isSelected,
    required this.imagePath,
  });

  final RecommendedPersona persona;
  final bool isSelected;
  final String imagePath;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: isSelected ? AppColors.primaryLight : Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isSelected ? AppColors.primary : AppColors.gray,
          width: isSelected ? 3 : 3,
        ),
      ),
      child: Column(
        children: [
          Expanded(
            child: ClipRRect(
              borderRadius:
                  const BorderRadius.vertical(top: Radius.circular(10)),
              child: Image.asset(
                imagePath,
                width: double.infinity,
                fit: BoxFit.cover,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 10),
            child: Text(
              persona.name,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: isSelected
                        ? AppColors.primary
                        : AppColors.textPrimary,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _BackSide extends StatelessWidget {
  const _BackSide({
    required this.persona,
    required this.isSelected,
    required this.onSelected,
  });

  final RecommendedPersona persona;
  final bool isSelected;
  final VoidCallback onSelected;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isSelected ? AppColors.primaryLight : Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isSelected ? AppColors.primary : AppColors.gray,
          width: isSelected ? 3 : 3,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(
            persona.name,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: isSelected
                      ? AppColors.primary
                      : AppColors.textPrimary,
                ),
          ),
          const SizedBox(height: 5),
          Expanded(
            child: Text(
              persona.summary,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
              )
            ),
          ),
          if (persona.rank == 1) ...[
            const SizedBox(height: 4),
            Text(
              '추천 1순위 페르소나',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.primary,
                  ),
            ),
          ],
          const SizedBox(height: 8),
          GestureDetector(
            onTap: onSelected,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 8),
              decoration: BoxDecoration(
                color: isSelected ? AppColors.primary : AppColors.gray,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '페르소나 선택하기',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.white,
                    ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}