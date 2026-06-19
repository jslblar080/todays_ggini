import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';

class AppPrimaryButton extends StatelessWidget {
  const AppPrimaryButton({
    super.key,
    required this.text,
    required this.onPressed,
    this.enabled = true,
    this.topPadding = 0,
  });

  final String text;
  final VoidCallback onPressed;
  final bool enabled;
  final double topPadding;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (topPadding > 0)
          Container(
            height: topPadding,
            color: Colors.white,
          ),
        SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: enabled ? onPressed : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: enabled ? AppColors.primary : AppColors.gray,
              foregroundColor: Colors.white,
              disabledBackgroundColor: AppColors.gray,
              disabledForegroundColor: Colors.white,
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(30),
              ),
              textStyle: const TextStyle(
                fontSize: 20,
                fontFamily: 'Pretendard',
                fontWeight: FontWeight.w600,
              ),
            ),
            child: Text(text),
          ),
        ),
      ],
    );
  }
}