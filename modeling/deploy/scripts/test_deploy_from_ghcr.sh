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

NEW_IMAGE="ghcr.io/hekim-cse/todays-ggini-modeling:main-deadbee"
PREVIOUS_IMAGE="ghcr.io/hekim-cse/todays-ggini-modeling:main-acde123"
MISMATCH_IMAGE="ghcr.io/hekim-cse/todays-ggini-modeling:main-badf00d"

cleanup() {
    rm -rf "${TEST_ROOT}"
}

trap cleanup EXIT

mkdir -p \
    "${PROJECT_DIR}/modeling/deploy" \
    "${FAKE_BIN_DIR}" \
    "${STATE_DIR}"

cat > "${PROJECT_DIR}/modeling/deploy/docker-compose.ec2.yml" <<'YAML'
services:
  modeling-api:
    image: ${MODELING_IMAGE:?MODELING_IMAGE is required}
    container_name: todays-ggini-modeling
YAML

cat > "${PROJECT_DIR}/modeling/deploy/.env.modeling.prod" <<'ENV'
MODELING_API_KEY=test-key
ENV

printf '%s\n' "${PREVIOUS_IMAGE}" \
    > "${STATE_DIR}/current-image"

cat > "${FAKE_BIN_DIR}/docker" <<'EOF_DOCKER'
#!/usr/bin/env bash

set -Eeuo pipefail

STATE_DIR="${TEST_STATE_DIR:?TEST_STATE_DIR is required}"
DOCKER_LOG="${STATE_DIR}/docker.log"
DOCKER_MODE="${TEST_DOCKER_MODE:-success}"

printf 'docker %s\n' "$*" >> "${DOCKER_LOG}"

if [ "${1:-}" = "pull" ]; then
    if [ "${DOCKER_MODE}" = "fail-pull" ]; then
        exit 1
    fi

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
    if [ "${DOCKER_MODE}" = "fail-config" ]; then
        exit 1
    fi

    exit 0
fi

if printf '%s\n' "$*" | grep -q 'up -d'; then
    target_image="${MODELING_IMAGE:?MODELING_IMAGE is required}"

    if [ "${DOCKER_MODE}" = "mismatch-after-up" ] \
        && [ "${target_image}" = "${TEST_NEW_IMAGE}" ]; then
        target_image="${TEST_MISMATCH_IMAGE:?TEST_MISMATCH_IMAGE is required}"
    fi

    printf '%s\n' "${target_image}" \
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

assert_not_equals() {
    local unexpected="$1"
    local actual="$2"
    local message="$3"

    if [ "${unexpected}" = "${actual}" ]; then
        printf 'FAIL: %s\n' "${message}" >&2
        printf '동일하면 안 되는 값: %s\n' "${actual}" >&2
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

assert_not_contains() {
    local file="$1"
    local unexpected="$2"
    local message="$3"

    if grep -Fq "${unexpected}" "${file}"; then
        printf 'FAIL: %s\n' "${message}" >&2
        printf '  unexpected: %s\n' "${unexpected}" >&2
        printf '  file:       %s\n' "${file}" >&2
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
    local deploy_image="${2:-${NEW_IMAGE}}"
    local docker_mode="${3:-success}"

    PATH="${FAKE_BIN_DIR}:${PATH}" \
    PROJECT_DIR="${PROJECT_DIR}" \
    TEST_STATE_DIR="${STATE_DIR}" \
    TEST_HEALTH_MODE="${health_mode}" \
    TEST_DOCKER_MODE="${docker_mode}" \
    TEST_NEW_IMAGE="${deploy_image}" \
    TEST_MISMATCH_IMAGE="${MISMATCH_IMAGE}" \
    HEALTH_ATTEMPTS=1 \
    HEALTH_INTERVAL_SECONDS=0 \
    INTERNAL_HEALTH_URL="http://internal.test/health" \
    EXTERNAL_HEALTH_URL="https://external.test/health" \
    bash "${DEPLOY_SCRIPT}" "${deploy_image}"
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

test_pull_failure_does_not_rollback() {
    reset_state

    printf '\n[test] 이미지 pull 실패\n'

    local output_file
    local exit_code

    output_file="$(
        mktemp
    )"

    exit_code=0

    run_deploy \
        success \
        "${NEW_IMAGE}" \
        fail-pull \
        >"${output_file}" \
        2>&1 \
        || exit_code="$?"

    if [ "${exit_code}" -eq 0 ]; then
        cat "${output_file}"
        rm -f "${output_file}"
        printf \
            'FAIL: 이미지 pull 실패를 성공으로 처리하면 안 됩니다.\n' \
            >&2
        exit 1
    fi

    assert_equals \
        "${PREVIOUS_IMAGE}" \
        "$(cat "${STATE_DIR}/current-image")" \
        "pull 실패 시 기존 실행 이미지는 유지되어야 합니다."

    assert_contains \
        "${STATE_DIR}/docker.log" \
        "docker pull ${NEW_IMAGE}" \
        "신규 이미지 pull을 시도해야 합니다."

    assert_not_contains \
        "${STATE_DIR}/docker.log" \
        "config --quiet" \
        "pull 실패 후 Compose 설정 검증을 실행하면 안 됩니다."

    assert_not_contains \
        "${STATE_DIR}/docker.log" \
        "up -d" \
        "pull 실패 후 컨테이너 실행이나 Rollback을 수행하면 안 됩니다."

    assert_contains \
        "${output_file}" \
        "컨테이너 변경 전 오류이므로 Rollback을 수행하지 않습니다." \
        "pull 실패가 배포 시작 전 오류로 처리되어야 합니다."

    rm -f "${output_file}"

    printf '[pass] 이미지 pull 실패\n'
}


test_config_failure_does_not_rollback() {
    reset_state

    printf '\n[test] Compose 설정 검증 실패\n'

    local output_file
    local exit_code

    output_file="$(
        mktemp
    )"

    exit_code=0

    run_deploy \
        success \
        "${NEW_IMAGE}" \
        fail-config \
        >"${output_file}" \
        2>&1 \
        || exit_code="$?"

    if [ "${exit_code}" -eq 0 ]; then
        cat "${output_file}"
        rm -f "${output_file}"
        printf \
            'FAIL: Compose 설정 검증 실패를 성공으로 처리하면 안 됩니다.\n' \
            >&2
        exit 1
    fi

    assert_equals \
        "${PREVIOUS_IMAGE}" \
        "$(cat "${STATE_DIR}/current-image")" \
        "Compose config 실패 시 기존 실행 이미지는 유지되어야 합니다."

    assert_contains \
        "${STATE_DIR}/docker.log" \
        "docker pull ${NEW_IMAGE}" \
        "Compose config 전에 신규 이미지 pull은 완료되어야 합니다."

    assert_contains \
        "${STATE_DIR}/docker.log" \
        "config --quiet" \
        "Compose 설정 검증을 실행해야 합니다."

    assert_not_contains \
        "${STATE_DIR}/docker.log" \
        "up -d" \
        "Compose config 실패 후 컨테이너 실행이나 Rollback을 수행하면 안 됩니다."

    assert_contains \
        "${output_file}" \
        "컨테이너 변경 전 오류이므로 Rollback을 수행하지 않습니다." \
        "Compose config 실패가 배포 시작 전 오류로 처리되어야 합니다."

    rm -f "${output_file}"

    printf '[pass] Compose 설정 검증 실패\n'
}


test_deployed_image_mismatch_rolls_back() {
    reset_state

    printf '\n[test] 실행 이미지 불일치 후 Rollback\n'

    local output_file
    local exit_code

    output_file="$(
        mktemp
    )"

    exit_code=0

    run_deploy \
        success \
        "${NEW_IMAGE}" \
        mismatch-after-up \
        >"${output_file}" \
        2>&1 \
        || exit_code="$?"

    if [ "${exit_code}" -eq 0 ]; then
        cat "${output_file}"
        rm -f "${output_file}"
        printf \
            'FAIL: 실행 이미지 불일치를 성공으로 처리하면 안 됩니다.\n' \
            >&2
        exit 1
    fi

    assert_equals \
        "${PREVIOUS_IMAGE}" \
        "$(cat "${STATE_DIR}/current-image")" \
        "실행 이미지 불일치 후 이전 이미지로 복구되어야 합니다."

    assert_contains \
        "${output_file}" \
        "실행 이미지가 배포 대상과 다릅니다." \
        "실행 이미지 불일치 오류를 출력해야 합니다."

    assert_contains \
        "${output_file}" \
        "expected=${NEW_IMAGE}, actual=${MISMATCH_IMAGE}" \
        "예상 이미지와 실제 이미지 정보를 출력해야 합니다."

    assert_contains \
        "${output_file}" \
        "이전 이미지로 Rollback합니다: ${PREVIOUS_IMAGE}" \
        "실행 이미지 불일치 후 Rollback을 수행해야 합니다."

    assert_contains \
        "${STATE_DIR}/docker.log" \
        "docker pull ${NEW_IMAGE}" \
        "불일치 시나리오에서도 신규 이미지를 pull해야 합니다."

    assert_contains \
        "${STATE_DIR}/docker.log" \
        "up -d" \
        "신규 이미지 실행과 Rollback을 수행해야 합니다."

    rm -f "${output_file}"

    printf '[pass] 실행 이미지 불일치 후 Rollback\n'
}


test_same_image_deployment_is_noop() {
    reset_state

    printf '\n[test] 동일 이미지 재배포 no-op\n'

    run_deploy \
        success \
        "${PREVIOUS_IMAGE}"

    assert_equals \
        "${PREVIOUS_IMAGE}" \
        "$(cat "${STATE_DIR}/current-image")" \
        "동일 이미지 요청 후 실행 이미지는 변경되지 않아야 합니다."

    assert_not_contains \
        "${STATE_DIR}/docker.log" \
        "docker pull ${PREVIOUS_IMAGE}" \
        "동일 이미지 요청에서는 pull을 실행하면 안 됩니다."

    assert_not_contains \
        "${STATE_DIR}/docker.log" \
        "up -d" \
        "동일 이미지 요청에서는 컨테이너를 재실행하면 안 됩니다."

    assert_contains \
        "${STATE_DIR}/curl.log" \
        "http://internal.test/health" \
        "동일 이미지 요청에서도 내부 Health를 확인해야 합니다."

    assert_contains \
        "${STATE_DIR}/curl.log" \
        "https://external.test/health" \
        "동일 이미지 요청에서도 외부 Health를 확인해야 합니다."

    printf '[pass] 동일 이미지 재배포 no-op\n'
}


test_same_image_health_failure_does_not_redeploy() {
    reset_state

    printf '\n[test] 동일 이미지 Health 실패\n'

    local output_file
    local exit_code

    output_file="$(
        mktemp
    )"

    exit_code=0

    run_deploy \
        fail-new-image \
        "${PREVIOUS_IMAGE}" \
        >"${output_file}" \
        2>&1 \
        || exit_code="$?"

    if [ "${exit_code}" -eq 0 ]; then
        cat "${output_file}"
        rm -f "${output_file}"
        printf \
            'FAIL: 동일 이미지의 Health 실패를 성공으로 처리하면 안 됩니다.\n' \
            >&2
        exit 1
    fi

    assert_equals \
        "${PREVIOUS_IMAGE}" \
        "$(cat "${STATE_DIR}/current-image")" \
        "Health 실패 후에도 실행 이미지 상태는 변경되지 않아야 합니다."

    assert_not_contains \
        "${STATE_DIR}/docker.log" \
        "docker pull ${PREVIOUS_IMAGE}" \
        "동일 이미지 Health 실패 시 pull을 실행하면 안 됩니다."

    assert_not_contains \
        "${STATE_DIR}/docker.log" \
        "up -d" \
        "배포를 시작하지 않았으므로 Rollback 재배포를 실행하면 안 됩니다."

    assert_contains \
        "${output_file}" \
        "healthcheck 실패" \
        "동일 이미지의 Health 실패 원인을 출력해야 합니다."

    rm -f "${output_file}"

    printf '[pass] 동일 이미지 Health 실패\n'
}


test_rejects_mutable_latest_tag() {
    local latest_image
    local output_file
    local exit_code

    latest_image=\
"ghcr.io/hekim-cse/todays-ggini-modeling:latest"

    output_file="$(
        mktemp
    )"

    exit_code=0

    TEST_NEW_IMAGE="${latest_image}" \
    bash "${DEPLOY_SCRIPT}" "${latest_image}" \
        >"${output_file}" \
        2>&1 \
        || exit_code="$?"

    if [ "${exit_code}" -eq 0 ]; then
        cat "${output_file}"
        rm -f "${output_file}"
        fail \
            "latest 이미지 태그가 거부되지 않았습니다."
    fi

    assert_contains \
        "${output_file}" \
        "불변 main SHA 이미지 태그만 배포할 수 있습니다." \
        "latest 이미지 태그 거부 오류를 출력해야 합니다."

    rm -f "${output_file}"

    printf '%s\n' \
        "latest 이미지 태그 거부 테스트를 통과했습니다."
}

assert_not_equals \
    "${PREVIOUS_IMAGE}" \
    "${NEW_IMAGE}" \
    "이전 이미지와 신규 이미지는 서로 달라야 합니다."

test_successful_deployment
test_rollback_after_health_failure
test_pull_failure_does_not_rollback
test_config_failure_does_not_rollback
test_deployed_image_mismatch_rolls_back
test_same_image_deployment_is_noop
test_same_image_health_failure_does_not_redeploy
test_rejects_mutable_latest_tag

printf '\n모든 deploy_from_ghcr 회귀 테스트를 통과했습니다.\n'
