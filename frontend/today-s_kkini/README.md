# 오늘의 끼니 — Frontend (Flutter)

스마트 영양 & 예산 플래너 **오늘의 끼니**의 클라이언트 애플리케이션입니다.
사용자의 페르소나·온보딩 정보를 바탕으로 AI가 식단을 추천하고, 식단에 필요한
재료를 장보기 목록으로 묶어 최저가로 안내하는 것을 목표로 합니다.

하나의 코드베이스로 **모바일(iOS/Android)** 과 **Web** 을 함께 빌드하며,
Web 빌드는 Vercel(<https://todays-ggini.vercel.app>)에 배포됩니다.

---

## 기술 스택

| 영역 | 선택 | 비고 |
| --- | --- | --- |
| 프레임워크 | Flutter `3.41.x` / Dart `^3.7` | 단일 코드베이스로 모바일·웹 빌드 |
| 상태관리 | `flutter_riverpod` 3.x | `StateNotifierProvider` 중심 |
| 라우팅 | `go_router` 17.x | 선언형 라우팅, path 파라미터 |
| 네트워크 | `dio` 5.x | 인터셉터 기반 인증/모킹 |
| 토큰 저장 | `flutter_secure_storage`, `shared_preferences` | access/refresh 토큰 보관 |
| 소셜 로그인 | 카카오 / 구글 / 네이버 | `kakao_flutter_sdk_user`, `google_sign_in`, `flutter_web_auth_2` |

---

## 아키텍처 — Feature-first + 레이어 분리

기능(feature) 단위로 폴더를 나누고, 각 feature 내부를 **data / domain / presentation**
3계층으로 구성했습니다. UI는 도메인 모델만 알고, 통신 세부사항은 data 레이어에 격리됩니다.

```
lib/
├── main.dart
├── core/                     # 앱 전역 공통 인프라
│   ├── env/                  # 컴파일타임 환경변수(Env) — dart-define 주입
│   ├── network/              # dio 클라이언트 + 인터셉터
│   │   ├── api_client.dart
│   │   ├── auth_interceptor.dart   # JWT 자동 부착 + 401 재발급/재시도
│   │   └── mock_interceptor.dart   # USE_MOCKS 시 asset JSON 응답
│   ├── router/               # go_router 설정(app_router) + 경로 상수(app_routes)
│   ├── theme/                # 색상·타이포 등 디자인 토큰
│   ├── utils/
│   └── widgets/              # 공용 위젯(버튼 등)
└── features/                 # 화면/기능 단위 모듈
    └── <feature>/
        ├── data/             # remote data source, repository
        ├── domain/           # 모델(엔티티), 비즈니스 규칙
        └── presentation/     # screens, widgets, providers(Riverpod)
```

### 데이터 흐름

```
Screen ──watch/read──▶ Provider(Notifier)
                          │
                          ▼
                      Repository ── 도메인 모델로 매핑
                          │
                          ▼
                  Remote Data Source ── dio 호출(/api/v1/...)
                          │
                          ▼
                   AuthInterceptor / MockInterceptor
```

- **Screen** 은 `Provider` 의 상태(`isLoading / error / data`)만 보고 그립니다.
- **Repository** 가 원격 응답(JSON)을 도메인 모델로 변환해 UI에서 통신 형식을 모르게 합니다.
- **Remote Data Source** 만 엔드포인트 경로와 dio를 직접 다룹니다.

---

## 주요 기능 (features)

| feature | 설명 |
| --- | --- |
| `splash` | 토큰 유효성 확인 후 진입 화면 분기 |
| `auth` | 카카오·구글·네이버 소셜 로그인, 토큰 발급/갱신 |
| `persona_select` | 사용자 페르소나(라이프스타일) 선택 |
| `onboarding` | 가족 구성·예산·식이 정보 등 온보딩 입력 |
| `meal_style_select` | AI가 생성한 3일치 샘플 식단 **스타일 후보** 선택 |
| `meal_plan_loading` | 월간 식단 생성 진행/대기 화면 |
| `calendar` | 월간 식단 캘린더 |
| `meal_detail` | 날짜별 식단 상세 |
| `menu_change` | 개별 메뉴 교체 |
| `ingredient_list` / `ingredient_detail` | 식단에 필요한 재료 목록·상세 |
| `shopping_list` / `shopping_selection` | 장보기 목록·담기, 휴지통 |
| `home` / `mypage` | 홈, 마이페이지(가족 구성원 관리 등) |

### 화면 경로 (go_router)

`/` → `/persona-select` → `/auth` → `/onboarding` → `/meal-style-select`
→ `/meal-plan/loading` → `/calendar` 가 핵심 온보딩~식단 생성 플로우입니다.
이후 `/home`, `/meal-detail/:date`, `/ingredient-list/:mealId`,
`/shopping-list`, `/menu-change/:mealId` 등으로 이동합니다.

---

## 네트워크 / 인증

- **Base URL**: `Env.apiBaseUrl` (기본 `https://api.todays-ggini.shop/api/v1`).
  로컬 개발 시 `--dart-define=API_BASE_URL=http://localhost:8000/api/v1`.
- **AuthInterceptor**
  - 모든 요청에 저장된 access 토큰을 `Authorization: Bearer <token>` 으로 부착.
  - `401` 응답 시 refresh 토큰으로 `/auth/refresh` 를 호출해 새 access 토큰을 받고
    원래 요청을 **자동 재시도**.
  - 동시에 여러 401이 떠도 refresh는 **한 번만** 수행(`Completer` 로 공유),
    재발급까지 실패하면 토큰을 비우고 로그인 화면으로 복귀.
- **MockInterceptor**: `USE_MOCKS=true` 빌드에서 `assets/mocks/**` JSON으로 응답을
  대체해 백엔드 없이 UI를 개발/검증(Mock-first).

---

## 환경변수 (compile-time, `--dart-define`)

웹 빌드는 dart-define 값이 JS 번들에 그대로 박히므로 **시크릿은 절대 주입하지 않습니다**
(네이버 Client Secret 등은 백엔드 전용).

| 키 | 설명 |
| --- | --- |
| `API_BASE_URL` | 백엔드 base URL (`.../api/v1`) |
| `USE_MOCKS` | `true` 시 mock JSON 사용 |
| `KAKAO_JAVASCRIPT_KEY` / `KAKAO_NATIVE_KEY` | 카카오 로그인 키(Web/Native) |
| `NAVER_CLIENT_ID` | 네이버 Client ID (Secret은 미주입) |
| `GOOGLE_WEB_CLIENT_ID` / `GOOGLE_IOS_CLIENT_ID` / `GOOGLE_ANDROID_CLIENT_ID` | 구글 OAuth Client ID |

---

## 실행 방법

```bash
# 의존성 설치
flutter pub get

# 모바일/웹 개발 실행 (로컬 백엔드)
flutter run --dart-define=API_BASE_URL=http://localhost:8000/api/v1

# Android 에뮬레이터에서 로컬 백엔드를 가리킬 때
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1

# 백엔드 없이 mock 으로 UI만 확인
flutter run --dart-define=USE_MOCKS=true
```

### Web 빌드 / 배포

`build.sh` 가 지정 버전의 Flutter를 받아 web 릴리스 번들을 만듭니다.
dart-define 값은 Vercel 프로젝트 환경변수에서 주입됩니다.

```bash
flutter build web --release \
  --dart-define=API_BASE_URL=... \
  --dart-define=KAKAO_JAVASCRIPT_KEY=... # 등
```

- **호스팅**: Vercel (`vercel.json`, `outputDirectory: build/web`, SPA rewrite).
- **소셜 로그인 콜백**: 웹은 `web/auth.html` 을 redirect_uri 콜백으로 사용합니다.
- 전제: 백엔드가 vercel.app origin에 대한 **CORS 허용** + **HTTPS** 제공.

---

## 개발 노트

- **상태관리 컨벤션**: 화면별 `StateNotifier` 가 `{ data, isLoading, error }` 형태의
  불변 상태를 들고, 화면은 그 상태만 보고 로딩/에러/정상 UI를 분기합니다.
- **에러 표면화**: 네트워크 실패는 Provider의 `error` 로 전달되어 각 화면에서
  사용자 친화적 메시지로 노출됩니다.
- **Mock-first 개발**: 백엔드 미구현 구간은 mock asset으로 먼저 UI를 완성한 뒤
  실제 API로 교체하는 방식으로 프론트/백엔드 작업을 병렬화했습니다.
- **디자인**: 화면 레이아웃은 Figma를 기준으로 별도 관리합니다.
