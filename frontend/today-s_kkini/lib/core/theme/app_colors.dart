import 'package:flutter/material.dart';

/// 끼니픽 색상 팔레트. 피그마 모킹업에서 추출.
class AppColors {
  const AppColors._();

  // Brand greens (sage / olive)
  static const Color primary = Color(0xFF3EB440); // main 녹색
  static const Color primaryLight = Color(0xFFEDF5EB); // 항목 선택 시 배경


  // Background / surfaces
  static const Color grayLight = Color(0xFFF0F0F0); // 회색 배경
  static const Color gray = Color(0xFFD9D9D9); // 회색 테두리
  static const Color background = Color(0xFFFFFFFF); // 흰색

  // Text (warm dark brown 계열)
  static const Color textPrimary = Color(0xFF000000); // 기본 글씨 색
  static const Color textSecondary = Color(0xFF807769); // 보조 글씨 색
  static const Color border = Color(0xFFDFD3C4); // 경계선, 구분선
  
  // Semantic
  static const Color error = Color(0xFFD64545); // 오류 메시지, 경고 등
}


