# Modeling FastAPI Serving PR Checklist

## 목적

이 문서는 `feat/modeling-fastapi-serving` 브랜치에서 구현한 Modeling FastAPI 서버, Docker 실행 환경, CI 검증 흐름을 PR 전에 점검하기 위한 체크리스트이다.

---

## 1. 구현 범위 확인

- [x] FastAPI 기반 Modeling 서버 추가
- [x] `/health` API 추가
- [x] `/meal-style-candidates` API 추가
- [x] `/monthly-plan` API 추가
- [x] `X-API-Key` 기반 인증 적용
- [x] 운영 환경에서 `/docs`, `/redoc`, `/openapi.json` 비활성화
- [x] 운영 환경 에러 메시지 최소화
- [x] RAG timeout을 `504 Gateway Timeout`으로 분리
- [x] 기타 RAG 외부 의존성 오류를 `502 Bad Gateway`로 분리

---

## 2. Docker 실행 환경 확인

- [x] `Dockerfile.modeling` 추가
- [x] `python:3.11-slim` 기반 이미지 구성
- [x] `ai/modeling` 코드 복사
- [x] 모델링 requirements 설치
- [x] FastAPI / Uvicorn 설치
- [x] non-root user 실행 설정
- [x] `PYTHONPATH=/app/ai/modeling` 설정
- [x] `ENV=prod` 기본 설정
- [x] `HEALTHCHECK` 추가
- [x] `EXPOSE 8000` 설정

---

## 3. Docker Compose 확인

- [x] `docker-compose.modeling.yml` 추가
- [x] `MODELING_API_KEY` 사용 확인
- [x] `MODELING_API_KEY` 필수 환경변수 처리
- [x] `LOG_LEVEL` 기본값 처리
- [x] `8001:8000` 포트 매핑
- [x] `.env.modeling.example` 추가
- [x] `.env.modeling` Git 제외 처리

---

## 4. 로컬 검증 결과

### FastAPI 직접 실행

- [x] `GET /health` 정상 응답
- [x] 잘못된 API Key 요청 시 `401 Unauthorized`
- [x] 올바른 API Key 요청 시 모델링 로직 진입 확인
- [x] RAG timeout 발생 시 `504 Gateway Timeout` 반환 확인

### Docker 실행

- [x] Docker image build 성공
- [x] Docker container run 성공
- [x] `/health` 정상 응답
- [x] prod 모드에서 `env` 미노출 확인
- [x] `/docs` 비활성화 확인
- [x] Docker health status `healthy` 확인

### Docker Compose 실행

- [x] `docker compose up --build` 성공
- [x] `/health` 정상 응답
- [x] wrong API key `401` 확인
- [x] RAG timeout `504` 확인
- [x] `docker compose down` 정상 종료

---

## 5. 테스트 및 검증 스크립트

- [x] HTTP smoke test 추가
- [x] HTTP smoke test에서 `/health` 확인
- [x] HTTP smoke test에서 wrong API key `401` 확인
- [x] HTTP smoke test에서 `/docs` 비활성화 확인
- [x] HTTP smoke test에서 monthly-plan `200` 또는 `504` 허용
- [x] `--skip-monthly` 옵션 추가
- [x] RAG 상태 코드 매핑 테스트 추가
- [x] RAG 상태 코드 매핑 테스트 직접 실행 가능
- [x] `rag_read_timeout` → `504`
- [x] `rag_timeout` → `504`
- [x] `rag_connection_error` → `502`
- [x] `rag_request_error` → `502`
- [x] `rag_http_error` → `502`

---

## 6. GitHub Actions 확인

- [x] `Modeling Docker Build` workflow 추가
- [x] Docker image build 검증
- [x] RAG 상태 코드 매핑 테스트를 Docker image 내부에서 실행
- [x] Modeling container 실행 검증
- [x] `/health` 응답 검증
- [x] prod 모드에서 `env` 미노출 검증
- [x] wrong API key `401` 검증
- [x] `/docs` `404` 검증
- [x] HTTP smoke test를 Docker image 내부에서 실행
- [x] `--skip-monthly`로 외부 RAG 의존성 제거
- [x] container stop 처리
- [x] 최신 CI 성공 확인

---

## 7. GHCR Publish Workflow 확인

- [x] `Modeling Docker Publish` workflow 추가
- [x] `develop` push 시 GHCR 이미지 게시
- [x] `main` push 시 GHCR 이미지 게시
- [x] feature branch에서는 publish 미실행
- [x] develop tag: `develop-<short-sha>`
- [x] main tag: `latest`, `main-<short-sha>`

주의: 이 workflow는 `develop` 또는 `main`에 merge된 뒤 실행된다.

---

## 8. 문서화 확인

- [x] Modeling Serving Guide 추가
- [x] CI/CD 흐름 문서 보강
- [x] Backend Modeling API Client Guide 추가
- [x] Notion 상위 문서 정리
- [x] Notion 세부 문서 하위 페이지 정리
- [x] PR 전 체크리스트 추가

---

## 9. 운영 배포 전 남은 사항

- [ ] 운영 환경 HTTPS 프록시 구성
- [ ] `MODELING_API_KEY` secret manager 연동
- [ ] Backend API client 실제 구현
- [ ] Backend timeout / retry / fallback 정책 정리
- [ ] Pydantic request model 필수 필드 강화
- [ ] Queue/Worker 기반 장기 처리 구조 검토
- [ ] Prometheus/Grafana 또는 CloudWatch 기반 모니터링 구성
- [ ] GHCR 이미지 pull 기반 실제 배포 자동화

---

## 10. PR 전 최종 확인 명령어

브랜치 상태 확인:

- `git status --short`
- `git log --oneline --decorate -12`

Python 문법 확인:

- `python -m py_compile ai/modeling/api/server.py`
- `python -m py_compile ai/modeling/experiments/contract/run_modeling_api_http_smoke.py`
- `python -m py_compile ai/modeling/tests/api/test_modeling_api_rag_error_status.py`

RAG 상태 코드 매핑 검증:

- `PYTHONPATH=ai/modeling python ai/modeling/tests/api/test_modeling_api_rag_error_status.py`

Docker build 검증:

- `docker build -f Dockerfile.modeling -t todays-ggini-modeling:ci .`

Docker 이미지 내부 테스트 검증:

- `docker run --rm todays-ggini-modeling:ci python ai/modeling/tests/api/test_modeling_api_rag_error_status.py`

---

## 11. 현재 브랜치

- `feat/modeling-fastapi-serving`

현재 브랜치에서는 PR 전 모델링 서버 실행 환경, Docker 검증, CI 검증, 문서화까지 완료된 상태다.
