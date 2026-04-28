import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/auth_screen.dart';
import '../../features/bulk_purchase/bulk_purchase_screen.dart';
import '../../features/calendar/calendar_screen.dart';
import '../../features/meal_plan_loading/meal_plan_loading_screen.dart';
import '../../features/meal_style_select/meal_style_select_screen.dart';
import '../../features/onboarding/presentation/screens/onboarding_screen.dart';
import '../../features/persona_select/persona_select_screen.dart';
import '../../features/recipe_detail/recipe_detail_screen.dart';
import '../../features/splash/splash_screen.dart';
import 'app_routes.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: AppRoutes.splash,
    routes: [
      GoRoute(path: AppRoutes.splash, builder: (_, __) => const SplashScreen()),
      GoRoute(
        path: AppRoutes.personaSelect,
        builder: (_, __) => const PersonaSelectScreen(),
      ),
      GoRoute(path: AppRoutes.auth, builder: (_, __) => const AuthScreen()),
      GoRoute(
        path: AppRoutes.onboarding,
        builder: (_, __) => const OnboardingScreen(),
      ),
      GoRoute(
        path: AppRoutes.mealStyleSelect,
        builder: (_, __) => const MealStyleSelectScreen(),
      ),
      GoRoute(
        path: AppRoutes.mealPlanLoading,
        builder: (_, __) => const MealPlanLoadingScreen(),
      ),
      GoRoute(
        path: AppRoutes.calendar,
        builder: (_, __) => const CalendarScreen(),
      ),
      GoRoute(
        path: AppRoutes.recipeDetail,
        builder:
            (_, state) => RecipeDetailScreen(
              recipeId: state.pathParameters['recipeId'] ?? '',
            ),
      ),
      GoRoute(
        path: AppRoutes.bulkPurchase,
        builder: (_, __) => const BulkPurchaseScreen(),
      ),
    ],
  );
});
