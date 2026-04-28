/// 라우트 path 상수. 화면 전환 시 매직스트링 방지.
class AppRoutes {
  const AppRoutes._();

  static const splash = '/';
  static const personaSelect = '/persona-select';
  static const auth = '/auth';
  static const onboarding = '/onboarding';
  static const mealStyleSelect = '/meal-style-select';
  static const mealPlanLoading = '/meal-plan/loading';
  static const calendar = '/calendar';
  static const recipeDetail = '/recipe/:recipeId';
  static const bulkPurchase = '/bulk-purchase';

  static String recipe(String recipeId) => '/recipe/$recipeId';
}
