#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/todays_ggini}"
COMPOSE_FILE="${PROJECT_DIR}/deploy/modeling/docker-compose.ec2.yml"
ENV_FILE="${PROJECT_DIR}/deploy/modeling/.env.modeling.prod"

SERVICE_NAME="modeling-api"
CONTAINER_NAME="todays-ggini-modeling"

INTERNAL_HEALTH_URL="${INTERNAL_HEALTH_URL:-http://127.0.0.1:8000/health}"
EXTERNAL_HEALTH_URL="${EXTERNAL_HEALTH_URL:-https://modeling.todays-ggini.shop/health}"

HEALTH_ATTEMPTS="${HEALTH_ATTEMPTS:-30}"
HEALTH_INTERVAL_SECONDS="${HEALTH_INTERVAL_SECONDS:-5}"

NEW_IMAGE="${1:-}"
PREVIOUS_IMAGE=""
DEPLOYMENT_STARTED="false"
ROLLBACK_STARTED="false"


log() {
    printf '[modeling-deploy] %s\n' "$*"
}


fail() {
    log "ERROR: $*"
    exit 1
}


wait_for_health() {
    local url="$1"
    local label="$2"
    local attempt

    for attempt in $(seq 1 "${HEALTH_ATTEMPTS}"); do
        if curl \
            --fail \
            --silent \
            --show-error \
            --max-time 10 \
            "${url}" \
            >/dev/null
        then
            log "${label} healthcheck 성공: ${url}"
            return 0
        fi

        log \
            "${label} healthcheck 대기 중 " \
            "(${attempt}/${HEALTH_ATTEMPTS})"

        sleep "${HEALTH_INTERVAL_SECONDS}"
    done

    log "${label} healthcheck 실패: ${url}"
    return 1
}


show_container_logs() {
    log "최근 컨테이너 로그를 출력합니다."

    docker compose \
        --env-file "${ENV_FILE}" \
        -f "${COMPOSE_FILE}" \
        logs \
        --tail=200 \
        "${SERVICE_NAME}" \
        || true
}


rollback() {
    if [ "${ROLLBACK_STARTED}" = "true" ]; then
        log "Rollback이 이미 진행 중입니다."
        return 1
    fi

    ROLLBACK_STARTED="true"

    if [ -z "${PREVIOUS_IMAGE}" ]; then
        log "이전 이미지가 없어 Rollback할 수 없습니다."
        return 1
    fi

    log "이전 이미지로 Rollback합니다: ${PREVIOUS_IMAGE}"

    MODELING_IMAGE="${PREVIOUS_IMAGE}" \
    docker compose \
        --env-file "${ENV_FILE}" \
        -f "${COMPOSE_FILE}" \
        up \
        -d \
        --no-build \
        "${SERVICE_NAME}"

    wait_for_health \
        "${INTERNAL_HEALTH_URL}" \
        "Rollback 내부"

    wait_for_health \
        "${EXTERNAL_HEALTH_URL}" \
        "Rollback 외부"

    log "Rollback 완료: ${PREVIOUS_IMAGE}"
}


handle_error() {
    local exit_code="$?"
    local line_number="${1:-unknown}"

    trap - ERR

    log \
        "배포 중 오류가 발생했습니다. " \
        "line=${line_number}, exit_code=${exit_code}"

    show_container_logs

    if [ "${DEPLOYMENT_STARTED}" != "true" ]; then
        log "컨테이너 변경 전 오류이므로 Rollback을 수행하지 않습니다."
    elif [ -n "${PREVIOUS_IMAGE}" ]; then
        if rollback; then
            log "새 이미지 배포 실패 후 이전 버전으로 복구했습니다."
        else
            log "Rollback에도 실패했습니다. 서버 상태를 직접 확인해야 합니다."
        fi
    else
        log "기존 컨테이너가 없어 자동 Rollback을 수행하지 않았습니다."
    fi

    exit "${exit_code}"
}


trap 'handle_error "${LINENO}"' ERR


if [ -z "${NEW_IMAGE}" ]; then
    fail \
        "배포할 이미지가 필요합니다. " \
        "사용법: $0 ghcr.io/<owner>/<image>:<tag>"
fi

if [[ ! "${NEW_IMAGE}" =~ :main-[0-9a-f]{7,40}$ ]]; then
    fail \
        "불변 main SHA 이미지 태그만 배포할 수 있습니다. " \
        "입력값: ${NEW_IMAGE}"
fi

# Compose 파일은 ps, logs, config 등 모든 명령에서
# MODELING_IMAGE 값이 있어야 해석할 수 있다.
# 기본값은 새 배포 이미지로 설정하고,
# Rollback 시에는 해당 명령에서 PREVIOUS_IMAGE로 덮어쓴다.
export MODELING_IMAGE="${NEW_IMAGE}"

if [ ! -f "${COMPOSE_FILE}" ]; then
    fail "Compose 파일을 찾을 수 없습니다: ${COMPOSE_FILE}"
fi

if [ ! -f "${ENV_FILE}" ]; then
    fail "운영 환경변수 파일을 찾을 수 없습니다: ${ENV_FILE}"
fi

cd "${PROJECT_DIR}"

log "배포 대상 이미지: ${NEW_IMAGE}"

CURRENT_CONTAINER_ID="$(
    docker compose \
        --env-file "${ENV_FILE}" \
        -f "${COMPOSE_FILE}" \
        ps \
        -q \
        "${SERVICE_NAME}"
)"

if [ -n "${CURRENT_CONTAINER_ID}" ]; then
    PREVIOUS_IMAGE="$(
        docker inspect \
            --format='{{.Config.Image}}' \
            "${CURRENT_CONTAINER_ID}"
    )"

    log "현재 실행 이미지: ${PREVIOUS_IMAGE}"
else
    log "현재 실행 중인 Modeling 컨테이너가 없습니다."
fi

if [ "${PREVIOUS_IMAGE}" = "${NEW_IMAGE}" ]; then
    log "현재 동일한 이미지가 실행 중입니다."
    log "컨테이너 재배포를 건너뛰고 Health 상태만 확인합니다."

    wait_for_health \
        "${INTERNAL_HEALTH_URL}" \
        "내부"

    wait_for_health \
        "${EXTERNAL_HEALTH_URL}" \
        "외부"

    log "동일 이미지 배포 요청 확인 완료"
    log "실행 이미지: ${PREVIOUS_IMAGE}"

    docker compose \
        --env-file "${ENV_FILE}" \
        -f "${COMPOSE_FILE}" \
        ps

    exit 0
fi

log "GHCR 이미지를 내려받습니다."

docker pull "${NEW_IMAGE}"

log "Compose 설정을 검증합니다."

MODELING_IMAGE="${NEW_IMAGE}" \
docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    config \
    --quiet

log "새 이미지로 컨테이너를 실행합니다."

DEPLOYMENT_STARTED="true"

MODELING_IMAGE="${NEW_IMAGE}" \
docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    up \
    -d \
    --no-build \
    "${SERVICE_NAME}"

wait_for_health \
    "${INTERNAL_HEALTH_URL}" \
    "내부"

wait_for_health \
    "${EXTERNAL_HEALTH_URL}" \
    "외부"

DEPLOYED_IMAGE="$(
    docker inspect \
        --format='{{.Config.Image}}' \
        "${CONTAINER_NAME}"
)"

if [ "${DEPLOYED_IMAGE}" != "${NEW_IMAGE}" ]; then
    fail \
        "실행 이미지가 배포 대상과 다릅니다. " \
        "expected=${NEW_IMAGE}, actual=${DEPLOYED_IMAGE}"
fi

log "배포 성공"
log "실행 이미지: ${DEPLOYED_IMAGE}"

docker compose \
    --env-file "${ENV_FILE}" \
    -f "${COMPOSE_FILE}" \
    ps
