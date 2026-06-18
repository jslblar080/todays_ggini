import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../../core/router/app_routes.dart';
import '../../../../../core/theme/app_colors.dart';
import '../../../../../core/widgets/popup.dart';
import '../providers/auth_provider.dart';
import 'social_button.dart';
import '../../../../../core/widgets/app_primary_button.dart';

class SocialLoginSheet extends ConsumerWidget {
  const SocialLoginSheet({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifier = ref.read(authProvider.notifier);

    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: Container(
        padding: const EdgeInsets.fromLTRB(24, 24, 24, 40),
        color: AppColors.background,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 핸들바
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(5),
              ),
            ),

            const SizedBox(height: 24),

            // 소셜 버튼들
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                SocialButton(
                  label: '카카오',
                  imagePath: 'assets/images/kakao.png',
                  color: const Color(0xFFFFE812),
                  onTap: () async {
                    await notifier.loginWithKakao();
                    if (!context.mounted) return;
                    Navigator.pop(context);
                  },
                ),
                SocialButton(
                  label: '네이버',
                  imagePath: 'assets/images/naver.png',
                  color: const Color(0xFF03C75A),
                  labelColor: Colors.white,
                  onTap: () async {
                    await notifier.loginWithNaver();
                    if (!context.mounted) return;
                    Navigator.pop(context);
                  },
                ),
                SocialButton(
                  label: '구글',
                  imagePath: 'assets/images/google.png',
                  color: Colors.white,
                  border: true,
                  onTap: () async {
                    await notifier.loginWithGoogle();
                    if (!context.mounted) return;
                    Navigator.pop(context);
                  },
                ),
              ],
            ),

            const SizedBox(height: 16),

            // 구분선
            Row(
              children: [
                const Expanded(child: Divider(thickness: 2)),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: Text(
                    '또는',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
                const Expanded(child: Divider(thickness: 2)),
              ],
            ),

            const SizedBox(height: 16),

            // 로그인 없이 시작하기 버튼
            AppPrimaryButton(
              text: '로그인 없이 시작하기',
              onPressed: () {
                showAppPopup(
                  context: context,
                  content: '로그인 없이 시작할 시,\n어플리케이션을 삭제하면\n저장된 정보가 모두 삭제됩니다.',
                  leftButtonText: '로그인하기',
                  rightButtonText: '확인',
                  onLeftTap: () => Navigator.pop(context),
                  onRightTap: () async {
                    await notifier.loginAsGuest();
                    if (!context.mounted) return;
                    context.go(AppRoutes.personaSelect);
                  },
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}