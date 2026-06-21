#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(
    cd "$(dirname "${BASH_SOURCE[0]}")"
    pwd
)"

DEPLOY_SCRIPT="${SCRIPT_DIR}/deploy_from_ghcr.sh"

TEST_ROOT="$(
    mktemp -d
)"

PROJECT_DIR="${TEST_ROOT}/project"
FAKE_BIN_DIR="${TEST_ROOT}/fake-bin"
STATE_DIR="${TEST_ROOT}/state"

NEW_IMAGE="ghcr.io/hekim-cse/todays-ggini-modeling:main-new1234"
PREVIOUS_IMAGE="todays-ggini-modeling:manual"

cleanup() {
    rm -rf "${TEST_ROOT}"
}

trap cleanup EXIT

mkdir -p \
    "${PROJECT_DIR}/deploy/modeling" \
    "${FAKE_BIN_DIR}" \
    "${STATE_DIR}"

cat > "${PROJECT_DIR}/deploy/modeling/docker-compose.ec2.yml" <<'YAML'
services:
  modeling-api:
    image: ${MODELING_IMAGE:?MODELING_IMAGE is required}
    container_name: todays-ggini-modeling
YAML

cat > "${PROJECT_DIR}/deploy/modeling/.env.modeling.prod" <<'ENV'
MODELING_API_KEY=test-key
ENV

printf '%s\n' "${PREVIOUS_IMAGE}" \
    > "${STATE_DIR}/current-image"

cat > "${FAKE_BIN_DIR}/docker" <<'EOF_DOCKER'
#!/usr/bin/env bash

set -Eeuo pipefail

STATE_DIR="${TEST_STATE_DIR:?TEST_STATE_DIR is required}"
DOCKER_LOG="${STATE_DIR}/docker.log"

printf 'docker %s\n' "$*" >> "${DOCKER_LOG}"

if [ "${1:-}" = "pull" ]; then
    exit 0
fi

if [ "${1:-}" = "inspect" ]; then
    cat "${STATE_DIR}/current-image"
    exit 0
fi

if [ "${1:-}" != "compose" ]; then
    echo "unexpected docker command: $*" >&2
    exit 1
fi

shift

if printf '%s\n' "$*" | grep -q 'ps -q modeling-api'; then
    printf '%s\n' "fake-container-id"
    exit 0
fi

if printf '%s\n' "$*" | grep -q 'config --quiet'; then
    exit 0
fi

if printf '%s\n' "$*" | grep -q 'up -d'; then
    printf '%s\n' "${MODELING_IMAGE:?MODELING_IMAGE is required}" \
        > "${STATE_DIR}/current-image"

    exit 0
fi

if printf '%s\n' "$*" | grep -q 'logs --tail=200'; then
    printf '%s\n' "fake container logs"
    exit 0
fi

if printf '%s\n' "$*" | grep -q 'ps'; then
    printf '%s\n' "modeling-api running"
    exit 0
fi

echo "unexpected docker compose command: $*" >&2
exit 1
EOF_DOCKER

cat > "${FAKE_BIN_DIR}/curl" <<'EOF_CURL'
#!/usr/bin/env bash

set -Eeuo pipefail

STATE_DIR="${TEST_STATE_DIR:?TEST_STATE_DIR is required}"
CURL_LOG="${STATE_DIR}/curl.log"

printf 'curl %s\n' "$*" >> "${CURL_LOG}"

MODE="${TEST_HEALTH_MODE:-success}"
CURRENT_IMAGE="$(
    cat "${STATE_DIR}/current-image"
)"

case "${MODE}" in
    success)
        exit 0
        ;;

    fail-new-image)
        if [ "${CURRENT_IMAGE}" = "${TEST_NEW_IMAGE}" ]; then
            exit 22
        fi

        exit 0
        ;;

    *)
        echo "unknown TEST_HEALTH_MODE: ${MODE}" >&2
        exit 1
        ;;
esac
EOF_CURL

chmod +x \
    "${FAKE_BIN_DIR}/docker" \
    "${FAKE_BIN_DIR}/curl"

assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="$3"

    if [ "${expected}" != "${actual}" ]; then
        printf 'FAIL: %s\n' "${message}" >&2
        printf '  expected: %s\n' "${expected}" >&2
        printf '  actual:   %s\n' "${actual}" >&2
        exit 1
    fi
}

assert_contains() {
    local file="$1"
    local expected="$2"
    local message="$3"

    if ! grep -Fq "${expected}" "${file}"; then
        printf 'FAIL: %s\n' "${message}" >&2
        printf '  missing: %s\n' "${expected}" >&2
        printf '  file: %s\n' "${file}" >&2
        exit 1
    fi
}

reset_state() {
    printf '%s\n' "${PREVIOUS_IMAGE}" \
        > "${STATE_DIR}/current-image"

    : > "${STATE_DIR}/docker.log"
    : > "${STATE_DIR}/curl.log"
}

run_deploy() {
    local health_mode="$1"

    PATH="${FAKE_BIN_DIR}:${PATH}" \
    PROJECT_DIR="${PROJECT_DIR}" \
    TEST_STATE_DIR="${STATE_DIR}" \
    TEST_HEALTH_MODE="${health_mode}" \
    TEST_NEW_IMAGE="${NEW_IMAGE}" \
    HEALTH_ATTEMPTS=1 \
    HEALTH_INTERVAL_SECONDS=0 \
    INTERNAL_HEALTH_URL="http://internal.test/health" \
    EXTERNAL_HEALTH_URL="https://external.test/health" \
    bash "${DEPLOY_SCRIPT}" "${NEW_IMAGE}"
}

test_successful_deployment() {
    printf '\n[test] 정상 배포\n'

    reset_state

    run_deploy success

    local deployed_image
    deployed_image="$(
        cat "${STATE_DIR}/current-image"
    )"

    assert_equals \
        "${NEW_IMAGE}" \
        "${deployed_image}" \
        "정상 배포 후 새 이미지가 실행되어야 합니다."

    assert_contains \
        "${STATE_DIR}/docker.log" \
        "docker pull ${NEW_IMAGE}" \
        "새 이미지를 pull해야 합니다."

    assert_contains \
        "${STATE_DIR}/curl.log" \
        "http://internal.test/health" \
        "내부 Healthcheck를 실행해야 합니다."

    assert_contains \
        "${STATE_DIR}/curl.log" \
        "https://external.test/health" \
        "외부 Healthcheck를 실행해야 합니다."

    printf '[pass] 정상 배포\n'
}

test_rollback_after_health_failure() {
    printf '\n[test] Health 실패 후 Rollback\n'

    reset_state

    set +e
    run_deploy fail-new-image
    local exit_code="$?"
    set -e

    if [ "${exit_code}" -eq 0 ]; then
        printf \
            'FAIL: Health 실패 배포는 실패 코드로 종료되어야 합니다.\n' \
            >&2
        exit 1
    fi

    local restored_image
    restored_image="$(
        cat "${STATE_DIR}/current-image"
    )"

    assert_equals \
        "${PREVIOUS_IMAGE}" \
        "${restored_image}" \
        "배포 실패 후 이전 이미지로 복구되어야 합니다."

    assert_contains \
        "${STATE_DIR}/docker.log" \
        "docker pull ${NEW_IMAGE}" \
        "실패 시나리오에서도 새 이미지 pull을 시도해야 합니다."

    assert_contains \
        "${STATE_DIR}/docker.log" \
        "docker inspect --format={{.Config.Image}} fake-container-id" \
        "Rollback을 위해 이전 이미지를 조회해야 합니다."

    printf '[pass] Health 실패 후 Rollback\n'
}

test_successful_deployment
test_rollback_after_health_failure

printf '\n모든 deploy_from_ghcr 회귀 테스트를 통과했습니다.\n'
