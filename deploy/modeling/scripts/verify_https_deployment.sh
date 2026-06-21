#!/usr/bin/env bash

set -Eeuo pipefail

BASE_URL="${MODELING_API_BASE_URL:-https://modeling.todays-ggini.shop}"
HEALTH_URL="${BASE_URL%/}/health"
DOMAIN="${BASE_URL#*://}"
DOMAIN="${DOMAIN%%/*}"

TEMP_RESPONSE="$(mktemp)"
trap 'rm -f "${TEMP_RESPONSE}"' EXIT

echo "== Modeling deployment verification =="
echo "Base URL: ${BASE_URL}"
echo

echo "[1/3] HTTPS health request"
HTTP_STATUS="$(
  curl \
    --silent \
    --show-error \
    --location \
    --connect-timeout 10 \
    --max-time 30 \
    --output "${TEMP_RESPONSE}" \
    --write-out '%{http_code}' \
    "${HEALTH_URL}"
)"

if [[ "${HTTP_STATUS}" != "200" ]]; then
  echo "ERROR: health endpoint returned HTTP ${HTTP_STATUS}" >&2
  cat "${TEMP_RESPONSE}" >&2
  exit 1
fi

python3 - "${TEMP_RESPONSE}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])

try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except json.JSONDecodeError as error:
    raise SystemExit(f"ERROR: health response is not valid JSON: {error}")

if payload.get("status") != "ok":
    raise SystemExit(
        f"ERROR: unexpected health status: {payload.get('status')!r}"
    )

print("Health response:", payload)
PY

echo
echo "[2/3] HTTP to HTTPS redirect"
REDIRECT_STATUS="$(
  curl \
    --silent \
    --show-error \
    --output /dev/null \
    --write-out '%{http_code}' \
    "http://${DOMAIN}/health"
)"

case "${REDIRECT_STATUS}" in
  301|302|307|308)
    echo "HTTP redirect status: ${REDIRECT_STATUS}"
    ;;
  *)
    echo "ERROR: expected redirect but received HTTP ${REDIRECT_STATUS}" >&2
    exit 1
    ;;
esac

echo
echo "[3/3] TLS certificate"
CERT_INFO="$(
  echo \
    | openssl s_client \
        -servername "${DOMAIN}" \
        -connect "${DOMAIN}:443" \
        2>/dev/null \
    | openssl x509 -noout -subject -issuer -dates
)"

echo "${CERT_INFO}"

echo
echo "SUCCESS: HTTPS deployment verification passed."
