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
  static const myPage = '/my-page';
  static const home = '/home';
  static const mealDetail = '/meal-detail/:date';
  static const ingredientList = '/ingredient-list/:mealId';
  static const shoppingList = '/shopping-list';
  static const shoppingTrash = '/shopping-list/trash';

  static String recipe(String recipeId) => '/recipe/$recipeId';
  static String mealDetailPath(DateTime date) =>
      '/meal-detail/${date.toIso8601String().substring(0, 10)}';
  static String ingredientListPath(String mealId) =>
      '/ingredient-list/$mealId'; 

  static const ingredientDetail = '/ingredient-detail/:ingredientId';
  static String ingredientDetailPath(String ingredientId) =>
    '/ingredient-detail/$ingredientId';
  static const menuChange = '/menu-change/:mealId';
  static String menuChangePath({
    required String mealId,
    required DateTime date,
    required int slot,
  }) {
    final dateStr = date.toIso8601String().substring(0, 10);
    return '/menu-change/$mealId?date=$dateStr&slot=$slot';
  }
}