import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/presentation/providers/auth_provider.dart';
import '../../features/auth/presentation/screens/auth_screen.dart';
import '../../features/calendar/presentation/screens/calendar_screen.dart';
import '../../features/meal_detail/presentation/screens/meal_detail_screen.dart';
import '../../features/meal_plan_loading/presentation/screens/meal_plan_loading_screen.dart';
import '../../features/meal_style_select/presentation/screens/meal_style_select_screen.dart';
import '../../features/onboarding/presentation/screens/onboarding_screen.dart';
import '../../features/persona_select/presentation/screens/persona_select_screen.dart';
import '../../features/splash/splash_screen.dart';
import '../../features/mypage/presentation/screens/mypage_screen.dart';
import '../../features/home/presentation/screens/home_screen.dart';
import '../../features/ingredient_list/presentation/screens/ingredient_list_screen.dart';
import '../../features/shopping_list/presentation/screens/shopping_list_screen.dart';
import '../../features/shopping_list/presentation/screens/shopping_trash_screen.dart';
import '../../features/ingredient_detail/presentation/screens/ingredient_detail_screen.dart';
import '../../features/menu_change/presentation/screens/menu_change_screen.dart';
import '../../features/mypage/domain/my_profile.dart';
import '../../features/mypage/presentation/screens/family_members_screen.dart';

import 'app_routes.dart';

/// authState 변화를 GoRouter 의 refreshListenable 에 전달하는 어댑터.
class _AuthChangeNotifier extends ChangeNotifier {
  void bump() => notifyListeners();
}

final routerProvider = Provider<GoRouter>((ref) {
  final authNotifier = _AuthChangeNotifier();

  // authState 변할 때마다 notifyListeners → GoRouter 가 redirect 재평가
  ref.listen(authProvider, (_, __) => authNotifier.bump());

  // ref 가 dispose 될 때 notifier 도 정리
  ref.onDispose(authNotifier.dispose);

  return GoRouter(
    initialLocation: AppRoutes.splash,
    // authNotifier가 authState 변화를 refreshListenable에 전달하는 로직 (빠지면 안됨)
    refreshListenable: authNotifier,
    redirect: (context, state) {
      final container = ProviderScope.containerOf(context);
      final authState = container.read(authProvider);
      final isLoggedIn = authState.isLoggedIn;
      final isOnboarded = authState.user?.isOnboarded ?? false;
      final currentPath = state.uri.path;

      // splash는 자체적으로 처리
      if (currentPath == AppRoutes.splash) {
        return null;
      }

      // 로그인 안 됐으면 → auth로
      if (!isLoggedIn && currentPath != AppRoutes.auth) {
        return AppRoutes.auth;
      }

      // 온보딩 안 했으면 → 페르소나 선택으로
      if (isLoggedIn && !isOnboarded) {
        final onboardingRoutes = [
          AppRoutes.personaSelect,
          AppRoutes.onboarding,
          AppRoutes.mealStyleSelect,
          AppRoutes.mealPlanLoading,
        ];
        if (!onboardingRoutes.contains(currentPath)) {
          return AppRoutes.personaSelect;
        }
      }

      // 온보딩 완료 후 auth 화면 접근 막기
      if (isLoggedIn && isOnboarded && currentPath == AppRoutes.auth) {
        return AppRoutes.home;
      }

      return null;
    },
    routes: [
      GoRoute(path: AppRoutes.splash, builder: (_, __) => const SplashScreen()),
      GoRoute(
        path: AppRoutes.personaSelect,
        builder: (_, state) {
          final initialData = state.extra as Map<String, dynamic>?;
          return PersonaSelectScreen(initialData: initialData);
        },
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
        builder: (context, state) {
          final styleId =
              state.uri.queryParameters['style_id'] ?? 'budget_first';
          return MealPlanLoadingScreen(styleId: styleId);
        },
      ),
      GoRoute(
        path: AppRoutes.calendar,
        builder: (_, __) => const CalendarScreen(),
      ),
      GoRoute(path: AppRoutes.myPage, builder: (_, __) => const MyPageScreen()),
      GoRoute(
        path: AppRoutes.mealDetail,
        builder: (_, state) {
          final dateStr = state.pathParameters['date'] ?? '';
          final date = DateTime.tryParse(dateStr) ?? DateTime.now();
          return MealDetailScreen(date: date);
        },
      ),
      GoRoute(path: AppRoutes.home, builder: (_, __) => const HomeScreen()),
      GoRoute(
        path: AppRoutes.ingredientList,
        builder: (_, state) {
          final mealId = state.pathParameters['mealId'] ?? '';
          final dateStr = state.uri.queryParameters['date'];
          final slotStr = state.uri.queryParameters['slot'];
          final sourceDate =
              dateStr != null ? DateTime.tryParse(dateStr) : null;
          final sourceSlot = slotStr != null ? int.tryParse(slotStr) : null;
          return IngredientListScreen(
            mealId: mealId,
            sourceDate: sourceDate,
            sourceSlot: sourceSlot,
          );
        },
      ),
      GoRoute(
        path: AppRoutes.shoppingList,
        builder: (_, __) => const ShoppingListScreen(),
      ),
      GoRoute(
        path: AppRoutes.shoppingTrash,
        builder: (_, __) => const ShoppingTrashScreen(),
      ),
      GoRoute(
        path: AppRoutes.ingredientDetail,
        builder: (_, state) {
          final ingredientId = state.pathParameters['ingredientId'] ?? '';
          return IngredientDetailScreen(ingredientId: ingredientId);
        },
      ),
      GoRoute(
        path: AppRoutes.menuChange,
        builder: (_, state) {
          final mealId = state.pathParameters['mealId'] ?? '';
          final dateStr = state.uri.queryParameters['date'];
          final slotStr = state.uri.queryParameters['slot'];
          final date =
              dateStr != null
                  ? DateTime.tryParse(dateStr) ?? DateTime.now()
                  : DateTime.now();
          final slot = slotStr != null ? int.tryParse(slotStr) ?? 1 : 1;
          return MenuChangeScreen(mealId: mealId, date: date, slot: slot);
        },
      ),
      GoRoute(
        path: AppRoutes.familyMembers,
        builder: (_, state) {
          final profile = state.extra as MyProfile;
          return FamilyMembersScreen(profile: profile);
        },
      ),
    ],
  );
});
