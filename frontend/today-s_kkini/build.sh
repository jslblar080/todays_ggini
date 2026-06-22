#!/usr/bin/env bash
# Vercel 빌드용 스크립트.
# Vercel 빌드 컨테이너엔 Flutter가 없으므로, 로컬과 동일한 버전을 고정 설치한 뒤
# web 번들을 빌드한다. dart-define 값들은 Vercel 프로젝트 환경변수에서 주입하며,
# 미설정 시 아래 기본값을 사용한다(소셜 키는 비워둠 → 해당 로그인만 비활성).
#
# 주의: NAVER_CLIENT_SECRET 등 시크릿은 절대 web 빌드에 dart-define 하지 않는다.
# Flutter web은 dart-define 값이 JS 번들에 그대로 박혀 누구나 볼 수 있다(=유출).
# 네이버 code→token 교환은 백엔드만 수행하므로 시크릿은 백엔드 환경변수로만 둔다.
set -euo pipefail

# 로컬 빌드 버전과 일치시켜 "로컬은 되는데 Vercel은 깨짐"을 예방한다.
FLUTTER_VERSION="3.41.9"

if [ ! -d "_flutter" ]; then
  git clone https://github.com/flutter/flutter.git \
    --depth 1 --branch "$FLUTTER_VERSION" _flutter
fi
export PATH="$PWD/_flutter/bin:$PATH"

flutter --version
flutter config --enable-web
flutter pub get

flutter build web --release \
  --dart-define=USE_MOCKS="${USE_MOCKS:-false}" \
  --dart-define=API_BASE_URL="${API_BASE_URL:-https://api.todays-ggini.shop/api/v1}" \
  --dart-define=KAKAO_JAVASCRIPT_KEY="${KAKAO_JAVASCRIPT_KEY:-}" \
  --dart-define=KAKAO_NATIVE_KEY="${KAKAO_NATIVE_KEY:-}" \
  --dart-define=NAVER_CLIENT_ID="${NAVER_CLIENT_ID:-}" \
  --dart-define=GOOGLE_WEB_CLIENT_ID="${GOOGLE_WEB_CLIENT_ID:-}" \
  --dart-define=GOOGLE_IOS_CLIENT_ID="${GOOGLE_IOS_CLIENT_ID:-}" \
  --dart-define=GOOGLE_ANDROID_CLIENT_ID="${GOOGLE_ANDROID_CLIENT_ID:-}"
