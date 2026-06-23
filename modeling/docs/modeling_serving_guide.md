# Modeling FastAPI Serving Guide

## 목적

이 문서는 Todays Ggini Modeling 서버를 FastAPI와 Docker 기반으로 실행하는 방법을 정리한다.

모델링 서버는 기존 Python 함수 직접 호출 방식에서 HTTP API 호출 방식으로 확장할 수 있도록 구성되어 있다.

## 제공 API

| Method | Path | 설명 | 인증 |
| --- | --- | --- | --- |
| GET | `/health` | 서버 상태 확인 | 없음 |
| POST | `/meal-style-candidates` | 식단 스타일 후보 생성 | `X-API-Key` 필요 |
| POST | `/monthly-plan` | 월간 식단 생성 | `X-API-Key` 필요 |

## 보안 기준

운영 환경에서는 아래 기준을 따른다.

- 외부 공개 API는 HTTPS 뒤에서만 사용한다.
- FastAPI Modeling 서버는 외부에 직접 노출하지 않는다.
- Backend 또는 내부 프록시만 Modeling API를 호출한다.
- `X-API-Key`는 최소 인증 장치로 사용한다.
- API Key는 코드에 직접 작성하지 않고 환경변수로 주입한다.
- 운영 환경에서는 `/docs`, `/redoc`, `/openapi.json`을 비활성화한다.
- 운영 환경에서는 내부 에러 타입과 상세 메시지를 응답에 노출하지 않는다.

권장 배포 구조는 아래와 같다.

```text
Backend
  ↓ HTTPS
Nginx / ALB / API Gateway
  ↓ Internal HTTP
FastAPI Modeling Server
```

## 로컬 Docker 이미지 빌드

```bash
docker build -f Dockerfile.modeling -t todays-ggini-modeling:local .
```

## Docker 단독 실행

```bash
docker run --rm \
  --name todays-ggini-modeling \
  -e MODELING_API_KEY=local-secret-key \
  -p 8001:8000 \
  todays-ggini-modeling:local
```

## Docker Compose 실행

먼저 로컬 실행용 환경변수 파일을 만든다.

```bash
cp .env.modeling.example .env.modeling
```

`.env.modeling` 예시:

```env
MODELING_API_KEY=local-secret-key
LOG_LEVEL=INFO
```

Compose 실행:

```bash
docker compose --env-file .env.modeling -f docker-compose.modeling.yml up --build
```

Compose 종료:

```bash
docker compose --env-file .env.modeling -f docker-compose.modeling.yml down
```

`MODELING_API_KEY`는 필수 환경변수다. 값이 없으면 서버 실행 또는 종료 명령에서 Compose 변수 검증에 실패할 수 있다.

## Health Check

```bash
curl -s http://localhost:8001/health | python -m json.tool
```

정상 응답:

```json
{
  "status": "ok",
  "service": "todays-ggini-modeling"
}
```

Docker 실행 환경은 기본적으로 `ENV=prod`이므로 `/health` 응답에 `env` 값이 노출되지 않는다.

## API Key 인증 실패 확인

```bash
curl -s -o /tmp/modeling_wrong_key_response.json \
  -w "http_status=%{http_code}\n" \
  -X POST http://localhost:8001/monthly-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: wrong-key" \
  --data-binary @modeling/experiments/fixtures/backend_monthly_plan_request.json

python -m json.tool /tmp/modeling_wrong_key_response.json
```

정상 결과:

```text
http_status=401
```

```json
{
  "detail": "Invalid or missing API key."
}
```

## 월간 식단 생성 API 확인

```bash
curl -s -o /tmp/modeling_monthly_response.json \
  -w "http_status=%{http_code}\n" \
  -X POST http://localhost:8001/monthly-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: local-secret-key" \
  --data-binary @modeling/experiments/fixtures/backend_monthly_plan_request.json

python - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("/tmp/modeling_monthly_response.json").read_text(encoding="utf-8"))

print("keys:", list(data.keys()))
print("detail:", data.get("detail"))
print("days:", len(data.get("monthly_plan", {}).get("days", [])))
PY
```

RAG API가 정상 응답하면 `http_status=200`과 월간 식단 결과가 반환된다.

RAG API timeout이 발생하면 운영 모드에서는 아래처럼 응답한다.

```text
http_status=504
detail: External recommendation service error.
days: 0
```

이는 Modeling FastAPI 서버의 실패가 아니라 외부 RAG API timeout을 `504 Gateway Timeout`으로 분리한 결과다.

## 현재 한계 및 후속 개선 사항

### 1. Pydantic Request Model은 아직 강한 검증을 하지 않는다

현재 요청 모델은 Backend contract 호환성을 위해 extra field를 허용한다.

```python
class MonthlyPlanRequest(BaseModel):
    class Config:
        extra = "allow"
```

따라서 현재 단계에서는 잘못된 필드까지 엄격하게 차단하지 않는다.

추후 Backend 요청 형식이 더 고정되면 `user_id`, `budget`, `meal_count_per_day` 등 필수 필드를 명시해 FastAPI의 `422 Unprocessable Entity` 검증을 강화할 수 있다.

### 2. RAG timeout 판별은 문자열 기반이다

현재는 `RagRequestError` 메시지에 `timeout` 또는 `시간이 초과`가 포함되어 있는지 확인해 `504`로 분리한다.

추후에는 `RagRequestError` 내부에 `failure_reason="timeout"` 같은 명시적 필드를 추가하는 것이 더 안정적이다.

### 3. API Key는 HTTPS와 함께 사용해야 한다

`X-API-Key`는 최소 인증 장치다.

운영 환경에서 HTTP로 전송하면 API Key가 평문으로 노출될 수 있으므로 반드시 HTTPS 뒤에서 사용해야 한다.

### 4. 처리 시간이 길면 Queue 기반 구조를 고려한다

월간 식단 생성은 RAG, optimizer, validation이 포함되어 처리 시간이 길어질 수 있다.

요청 시간이 길어져 Backend timeout이 발생할 경우 아래 구조를 고려한다.

```text
Backend request
  ↓
Job 등록
  ↓
Queue
  ↓
Worker가 월간 식단 생성
  ↓
결과 저장
  ↓
Backend가 결과 조회
```

## 참고

현재 Docker 기반 실행은 로컬 검증과 배포 준비를 위한 단계다.

실제 운영에서는 HTTPS, secret 관리, 접근 제어, 로그/모니터링, timeout 정책을 함께 구성해야 한다.

## CI/CD 흐름

모델링 서버 Docker 작업은 GitHub Actions를 통해 두 단계로 나누어 검증한다.

### 1. Docker Build 검증

`Modeling Docker Build` workflow는 모델링 서버 Docker 이미지가 정상적으로 빌드되고, 컨테이너가 실행되는지 확인한다.

실행 조건:

- `pull_request`: `develop`, `main` 대상
- `push`: `feat/modeling-fastapi-serving`

검증 내용:

- Docker image build
- container run
- `/health` 200 확인
- prod 모드에서 env 미노출 확인
- wrong API key 요청 시 401 확인
- `/docs` 비활성화 404 확인
- container stop

이 workflow는 이미지를 registry에 push하지 않는다.
PR 단계에서는 배포용 이미지 게시보다 Dockerfile과 서버 실행 가능 여부를 검증하는 것이 목적이다.

### 2. GHCR 이미지 게시

`Modeling Docker Publish` workflow는 `develop` 또는 `main`에 push될 때만 실행된다.

실행 조건:

- `push`: `develop`
- `push`: `main`

이미지 게시 규칙:

- develop merge 시: `ghcr.io/hekim-cse/todays-ggini-modeling:develop-<short-sha>`
- main merge 시: `ghcr.io/hekim-cse/todays-ggini-modeling:latest`
- main merge 시: `ghcr.io/hekim-cse/todays-ggini-modeling:main-<short-sha>`

이 구조를 통해 feature branch나 PR에서는 이미지가 불필요하게 계속 쌓이지 않도록 하고, 실제 통합 브랜치에 반영될 때만 배포 가능한 이미지를 생성한다.

## Docker Desktop에서 확인하는 방법

로컬에서 Docker image를 빌드하면 Docker Desktop의 `Images` 탭에서 아래 이미지를 확인할 수 있다.

- `todays-ggini-modeling:local`

컨테이너를 실행하면 `Containers` 탭에서 아래 컨테이너를 확인할 수 있다.

- `todays-ggini-modeling`

컨테이너 상세 화면에서는 아래 정보를 확인할 수 있다.

- Logs
- Port mapping
- Health status
- Environment
- Image name

Dockerfile에 `HEALTHCHECK`가 설정되어 있으므로 컨테이너가 정상적으로 `/health`에 응답하면 상태가 `healthy`로 표시된다.

## 운영 배포 시 주의사항

현재 FastAPI 서버 컨테이너는 내부적으로 HTTP로 실행된다.

- FastAPI Modeling Server
- 내부 포트: `8000`
- 내부 통신: HTTP

운영 환경에서는 이 컨테이너를 외부에 직접 노출하지 않고, 반드시 HTTPS를 처리하는 앞단 프록시 뒤에 둔다.

권장 구조:

- Backend / Client
- HTTPS
- Nginx / ALB / API Gateway
- Internal HTTP
- FastAPI Modeling Server

`X-API-Key`는 HTTPS와 함께 사용해야 한다.
HTTP로 API Key를 전송하면 중간에서 평문으로 노출될 수 있으므로 운영 환경에서는 HTTPS 구성이 필수다.
