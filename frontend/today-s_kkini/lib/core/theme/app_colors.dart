import 'package:flutter/material.dart';

/// 끼니픽 색상 팔레트. 피그마 모킹업에서 추출.
class AppColors {
  const AppColors._();

  // Brand greens (sage / olive)
  static const Color primary = Color(0xFF7FA968);
  static const Color primaryDark = Color(0xFF5A8B4A);
  static const Color primaryLight = Color(0xFFC4DAB1);

  // Background / surfaces
  static const Color background = Color(0xFFF7F2E8); // 따뜻한 크림
  static const Color surface = Color(0xFFFFFFFF);
  static const Color surfaceDim = Color(0xFFEEE9DD);

  // Text (warm dark brown 계열)
  static const Color textPrimary = Color(0xFF4A3F35);
  static const Color textSecondary = Color(0xFF8B7E6F);
  static const Color textHint = Color(0xFFB7AB99);

  // Accent (K coin yellow)
  static const Color accent = Color(0xFFF4C842);

  // Semantic
  static const Color error = Color(0xFFD64545);
  static const Color border = Color(0xFFD9CFBE);
}
