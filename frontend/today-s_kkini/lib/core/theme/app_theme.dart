import 'package:flutter/material.dart';
import 'app_colors.dart';

class AppTheme {
  const AppTheme._();

  static ThemeData light() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: AppColors.primary,
      primary: AppColors.primary,
      onPrimary: Colors.white,
      surface: AppColors.gray,
      onSurface: AppColors.textPrimary,
      error: AppColors.error,
      brightness: Brightness.light,
    );

    return ThemeData(
      useMaterial3: true,
      fontFamily: 'Pretendard',
      colorScheme: colorScheme,
      scaffoldBackgroundColor: AppColors.background,
      textTheme: const TextTheme(
        headlineLarge: TextStyle(
          fontSize: 24,        // 제목
          color: AppColors.textPrimary,
        ),
        headlineMedium: TextStyle(
          fontSize: 22,        // 부제목
          color: AppColors.textPrimary,
        ),
        bodyLarge: TextStyle(
          fontSize: 20,        // 본문 크게
          color: AppColors.textPrimary,
        ),
        bodyMedium: TextStyle(
          fontSize: 18,        // 본문 보통
          color: AppColors.textPrimary,
        ),
        bodySmall: TextStyle(
          fontSize: 16,        // 본문 작게
          color: AppColors.textSecondary,
        ),
        labelLarge: TextStyle(
          fontSize: 18,        // 버튼 글씨
          color: Colors.white,
        ),
      ),
      sliderTheme: SliderThemeData(
        activeTrackColor: AppColors.primary,
        inactiveTrackColor: AppColors.primaryLight,
        thumbColor: AppColors.primary,
        overlayColor: AppColors.primary.withValues(alpha: 0.16),
        trackHeight: 4,
      ),
    );
  }
}