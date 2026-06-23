# Backend ↔ Modeling API Client Guide

## 목적

이 문서는 Backend가 Modeling FastAPI 서버를 HTTP API 방식으로 호출할 때 필요한 연동 기준을 정리한다.

기존에는 Backend가 Modeling 함수를 직접 import하여 호출했다.

기존 구조:

- Backend
- Python 함수 직접 호출
- create_meal_style_candidates()
- create_monthly_plan()

향후에는 Modeling 서버를 별도 FastAPI 서버로 실행하고, Backend가 HTTP API로 호출하는 구조를 사용할 수 있다.

개선 구조:

- Backend
- HTTPS
- Nginx / ALB / API Gateway
- Internal HTTP
- FastAPI Modeling Server
- Modeling Service

---

## 제공 API

| Method | Endpoint | 설명 | 인증 |
| --- | --- | --- | --- |
| GET | `/health` | 모델링 서버 상태 확인 | 없음 |
| POST | `/meal-style-candidates` | 식단 스타일 후보 생성 | `X-API-Key` 필요 |
| POST | `/monthly-plan` | 월간 식단 생성 | `X-API-Key` 필요 |

---

## Backend 환경변수

Backend에서는 Modeling API 호출을 위해 아래 환경변수를 관리하는 것이 좋다.

| 환경변수 | 설명 | 예시 |
| --- | --- | --- |
| `MODELING_API_BASE_URL` | Modeling API base URL | `http://localhost:8001` |
| `MODELING_API_KEY` | Modeling API 호출용 secret | `local-secret-key` |
| `MODELING_API_TIMEOUT_SECONDS` | API 호출 timeout | `60` |

로컬 테스트 예시:

- `MODELING_API_BASE_URL=http://localhost:8001`
- `MODELING_API_KEY=local-secret-key`
- `MODELING_API_TIMEOUT_SECONDS=60`

운영 배포 예시:

- `MODELING_API_BASE_URL=https://modeling-api.example.com`
- `MODELING_API_KEY=<secret>`
- `MODELING_API_TIMEOUT_SECONDS=60`

운영 환경에서는 반드시 HTTPS 뒤에서 사용한다.

---

## 공통 Header

Modeling API 호출 시 아래 header를 사용한다.

- `Content-Type: application/json`
- `X-API-Key: <MODELING_API_KEY>`

`/health`는 인증 없이 호출 가능하지만, `/meal-style-candidates`, `/monthly-plan`은 `X-API-Key`가 필요하다.

---

## Health Check

Backend 또는 배포 환경에서는 Modeling 서버가 살아 있는지 `/health`로 확인할 수 있다.

명령어:

- `curl -s http://localhost:8001/health | python -m json.tool`

정상 응답:

- `status: ok`
- `service: todays-ggini-modeling`

운영 모드에서는 내부 환경 정보 노출을 줄이기 위해 `env` 값이 반환되지 않는다.

---

## 식단 스타일 후보 생성 API

### Endpoint

- `POST /meal-style-candidates`

### 호출 예시

- URL: `http://localhost:8001/meal-style-candidates`
- Header: `X-API-Key: local-secret-key`
- Request fixture: `modeling/experiments/fixtures/backend_style_candidates_request.json`
- Response fixture: `modeling/experiments/fixtures/backend_style_candidates_response.json`

curl 예시:

- `curl -s -X POST http://localhost:8001/meal-style-candidates -H "Content-Type: application/json" -H "X-API-Key: local-secret-key" --data-binary @modeling/experiments/fixtures/backend_style_candidates_request.json | python -m json.tool`

---

## 월간 식단 생성 API

### Endpoint

- `POST /monthly-plan`

### 호출 예시

- URL: `http://localhost:8001/monthly-plan`
- Header: `X-API-Key: local-secret-key`
- Request fixture: `modeling/experiments/fixtures/backend_monthly_plan_request.json`
- Success response fixture: `modeling/experiments/fixtures/backend_monthly_plan_success_response.json`
- Failure response fixture: `modeling/experiments/fixtures/backend_monthly_plan_failure_response.json`

curl 예시:

- `curl -s -o /tmp/modeling_monthly_response.json -w "http_status=%{http_code}\n" -X POST http://localhost:8001/monthly-plan -H "Content-Type: application/json" -H "X-API-Key: local-secret-key" --data-binary @modeling/experiments/fixtures/backend_monthly_plan_request.json`

---

## HTTP Status 처리 기준

| Status | 의미 | Backend 처리 방향 |
| --- | --- | --- |
| 200 | 정상 응답 | 결과 저장 또는 다음 단계 진행 |
| 401 | API Key 인증 실패 | 서버 설정 또는 secret 확인 |
| 422 | 요청 body 검증 실패 | Backend request payload 확인 |
| 500 | Modeling 서버 내부 오류 | 서버 로그 확인 및 장애 처리 |
| 502 | 외부 RAG 서비스 오류 | RAG 연동 상태 확인 |
| 504 | 외부 RAG 서비스 timeout | 재시도 또는 fallback 검토 |

---

## RAG Timeout 처리

월간 식단 생성 중 RAG API timeout이 발생하면 Modeling API는 `504 Gateway Timeout`을 반환한다.

운영 환경에서는 내부 에러 메시지를 그대로 노출하지 않고 아래처럼 단순화한다.

- `detail: External recommendation service error.`

이는 Modeling FastAPI 서버 자체의 실패가 아니라 외부 RAG API timeout을 분리한 결과다.

---

## Backend API Client 예시 구조

Backend 쪽에서는 Modeling API 호출 코드를 별도 client로 분리하는 것이 좋다.

예시 구조:

- `backend/app/clients/modeling_client.py`

권장 책임:

- base URL 관리
- X-API-Key header 추가
- timeout 설정
- status code별 예외 처리
- response JSON 반환

---

## Python Client 예시

아래 코드는 구조 예시다. 실제 Backend 코드 스타일에 맞춰 조정해야 한다.

```python
import os
import requests


class ModelingApiClient:
    def __init__(self) -> None:
        self.base_url = os.environ["MODELING_API_BASE_URL"].rstrip("/")
        self.api_key = os.environ["MODELING_API_KEY"]
        self.timeout = int(os.getenv("MODELING_API_TIMEOUT_SECONDS", "60"))

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

    def create_meal_style_candidates(self, payload: dict) -> dict:
        response = requests.post(
            f"{self.base_url}/meal-style-candidates",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def create_monthly_plan(self, payload: dict) -> dict:
        response = requests.post(
            f"{self.base_url}/monthly-plan",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
```

---

## 전환 전략

기존 직접 함수 호출 방식을 한 번에 제거하지 않고, 단계적으로 전환하는 것이 안전하다.

1. Modeling FastAPI 서버 배포
2. Backend Modeling API client 추가
3. feature flag로 직접 호출 방식과 API 호출 방식 병행
4. contract validation으로 request/response 확인
5. API 호출 방식 안정화 후 직접 import 방식 제거 검토

---

## 운영 주의사항

### HTTPS 필수

`X-API-Key`는 HTTP로 전송하면 평문으로 노출될 수 있다.

운영 환경에서는 반드시 HTTPS 뒤에서 사용한다.

권장 구조:

- Backend
- HTTPS
- Nginx / ALB / API Gateway
- Internal HTTP
- FastAPI Modeling Server

### Timeout 고려

월간 식단 생성은 처리 시간이 길 수 있다.

초기에는 timeout을 충분히 길게 잡고, 추후 요청 시간이 길어지면 Queue/Worker 기반 비동기 처리 구조를 검토한다.

### Secret 관리

`MODELING_API_KEY`는 코드, Git, Docker image에 포함하지 않는다.

환경변수, GitHub Secrets, 서버 secret manager 등을 사용한다.

---

## 후속 개선

- Backend Modeling API client 실제 구현
- status code별 예외 클래스 분리
- retry/fallback 정책 추가
- API request/response Pydantic schema 강화
- Queue/Worker 기반 월간 식단 생성 구조 검토
