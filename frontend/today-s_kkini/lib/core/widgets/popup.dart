import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class AppPopup extends StatelessWidget {
  final String? content;
  final Widget? contentWidget;
  final String? title;
  final String? leftButtonText;
  final String? rightButtonText;
  final VoidCallback? onLeftTap;
  final VoidCallback? onRightTap;
  final Color? leftButtonColor;
  final Color? rightButtonColor;
  // 단일 버튼용
  final String? singleButtonText;
  final VoidCallback? onSingleTap;

  const AppPopup({
    super.key,
    this.content,
    this.contentWidget,
    this.title,
    this.leftButtonText,
    this.rightButtonText,
    this.onLeftTap,
    this.onRightTap,
    this.leftButtonColor,
    this.rightButtonColor,
    this.singleButtonText,
    this.onSingleTap,
  });

  @override
  Widget build(BuildContext context) {
    final isSingle = singleButtonText != null;

    return AlertDialog(
      backgroundColor: AppColors.background,
      scrollable: true,
      insetPadding: const EdgeInsets.symmetric(horizontal: 24),
      contentPadding: const EdgeInsets.fromLTRB(24, 32, 24, 20),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
      ),
      title: title != null
        ? Center(
            child: Text(
              title!,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
          )
        : null,
      content: SizedBox(
        width: MediaQuery.of(context).size.width * 0.75,
        child: contentWidget ??
            Text(
              content ?? '',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
      ),
      actionsPadding: EdgeInsets.zero,
      actions: [
        Column(
          children: [
            Divider(height: 1, color: AppColors.border, thickness: 2),
            if (isSingle)
              Row(
                children: [
                  Expanded(
                    child: SizedBox(
                      height: 48,
                      child: TextButton(
                        onPressed: onSingleTap,
                        child: Text(
                          singleButtonText!,
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppColors.primary,
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              )
            else
              Row(
                children: [
                  Expanded(
                    child: TextButton(
                      onPressed: onLeftTap,
                      child: Text(
                        leftButtonText ?? '',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: leftButtonColor ?? AppColors.primary,
                        ),
                      ),
                    ),
                  ),
                  Container(width: 2, height: 48, color: AppColors.border),
                  Expanded(
                    child: TextButton(
                      onPressed: onRightTap,
                      child: Text(
                        rightButtonText ?? '',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: rightButtonColor ?? AppColors.textPrimary,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
          ],
        ),
      ],
    );
  }
}

// 기존 함수 (그대로 동작)
void showAppPopup({
  required BuildContext context,
  required String content,
  required String leftButtonText,
  required String rightButtonText,
  required VoidCallback onLeftTap,
  required VoidCallback onRightTap,
  Color? leftButtonColor,
  Color? rightButtonColor,
}) {
  showDialog(
    context: context,
    builder: (dialogContext) => AppPopup(
      content: content,
      leftButtonText: leftButtonText,
      rightButtonText: rightButtonText,
      onLeftTap: onLeftTap,
      onRightTap: onRightTap,
      leftButtonColor: leftButtonColor,
      rightButtonColor: rightButtonColor,
    ),
  );
}

// 단일 버튼용 함수 (새로 추가)
void showAppPopupSingle({
  required BuildContext context,
  required String content,
  String buttonText = '확인',
  VoidCallback? onTap,
}) {
  showDialog(
    context: context,
    builder: (dialogContext) => AppPopup(
      content: content,
      singleButtonText: buttonText,
      onSingleTap: onTap ?? () => Navigator.of(dialogContext).pop(),
    ),
  );
}

// 위젯 content용 함수 (기존 그대로)
void showAppPopupWidget({
  required BuildContext context,
  String? title,
  required Widget contentWidget,
  required String leftButtonText,
  required String rightButtonText,
  required VoidCallback onLeftTap,
  required VoidCallback onRightTap,
  Color? leftButtonColor,
  Color? rightButtonColor,
}) {
  showDialog(
    context: context,
    builder: (dialogContext) => AppPopup(
      title: title,
      contentWidget: contentWidget,
      leftButtonText: leftButtonText,
      rightButtonText: rightButtonText,
      onLeftTap: onLeftTap,
      onRightTap: onRightTap,
      leftButtonColor: leftButtonColor,
      rightButtonColor: rightButtonColor,
    ),
  );
}
