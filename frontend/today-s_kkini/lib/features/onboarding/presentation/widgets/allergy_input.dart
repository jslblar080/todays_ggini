import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class AllergyInput extends StatefulWidget {
  final List<String> allergies;
  final ValueChanged<List<String>> onChanged;

  const AllergyInput({
    super.key,
    required this.allergies,
    required this.onChanged,
  });

  @override
  State<AllergyInput> createState() => _AllergyInputState();
}

class _AllergyInputState extends State<AllergyInput> {
  final _controller = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 입력창 + 추가 버튼
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    decoration: BoxDecoration(
                      color: AppColors.grayLight,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: _error != null ? AppColors.error : Colors.transparent,
                      ),
                    ),
                    child: TextField(
                      controller: _controller,
                      style: Theme.of(context).textTheme.bodyMedium,
                      decoration: InputDecoration(
                        hintText: '알레르기 및 제외 재료',
                        hintStyle: Theme.of(context).textTheme.bodyLarge?.copyWith(
                              color: AppColors.textSecondary,
                            ),
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(
                            horizontal: 16, vertical: 14),
                      ),
                    ),
                  ),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 6, left: 4),
                      child: Text(
                        _error!,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: AppColors.error,
                            ),
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            SizedBox(
              height: 48,
              child: ElevatedButton(
                onPressed: () {
                  if (_controller.text.isNotEmpty) {
                    if (widget.allergies.contains(_controller.text)) {
                      setState(() => _error = '이미 입력된 재료입니다.');
                      Future.delayed(const Duration(seconds: 2), () {
                        if (mounted) setState(() => _error = null);
                      });
                    } else {
                      final newList = List<String>.from(widget.allergies)
                        ..add(_controller.text);
                      _controller.clear();
                      setState(() => _error = null);
                      widget.onChanged(newList);
                    }
                  }
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  elevation: 0,
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                  minimumSize: Size.zero,
                ),
                child: Text(
                  '추가',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: Colors.white,
                      ),
                ),
              ),
            ),
          ],
        ),

        const SizedBox(height: 12),

        // 추가된 항목 리스트
        ...widget.allergies.map((allergy) {
          return Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.gray, width: 3),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    allergy,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                ),
                GestureDetector(
                  onTap: () {
                    final newList = List<String>.from(widget.allergies)
                      ..remove(allergy);
                    widget.onChanged(newList);
                  },
                  child: const Icon(
                    Icons.close,
                    size: 20,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }
}