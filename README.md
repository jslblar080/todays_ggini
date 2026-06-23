# 🐹 오늘의 끼니

<p align="center">
  <img src="assets/images/project-cover.png" width="640" alt="오늘의 끼니 프로젝트 커버" />
</p>

<h3 align="center">🥗 AI 기반 개인 맞춤형 식단 추천 및 장보기 서비스</h3>

<p align="center">
  사용자의 <strong>식단 목표</strong>, <strong>예산</strong>, <strong>선호도</strong>,
  <strong>알레르기</strong>, <strong>조리 난이도</strong>를 반영하여<br>
  식단 스타일 추천부터 월간 식단, 대체 메뉴, 장보기 정보까지 연결합니다.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Frontend-Flutter-02569B?style=flat-square&logo=flutter&logoColor=white" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Modeling-Python-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/GraphDB-Neo4j-4581C3?style=flat-square&logo=neo4j&logoColor=white" />
  <img src="https://img.shields.io/badge/Optimizer-OR--Tools-4285F4?style=flat-square" />
  <img src="https://img.shields.io/badge/Deploy-Docker-2496ED?style=flat-square&logo=docker&logoColor=white" />
</p>

<br>

## 1. 프로젝트 소개

<p align="center">
  <img src="assets/images/project-overview.png" width="1000" alt="오늘의 끼니 프로젝트 개요" />
</p>


<table style="background-color:#FFF6C7; border-left:6px solid #E6C85C; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>🎯 핵심 목표</strong><br>
      오늘의 끼니는 단순히 메뉴를 추천하는 서비스가 아니라,
      사용자 조건을 기반으로 <strong>식단 스타일 후보 → 월간 식단 → 대체 메뉴 → 식료품 구매 정보</strong>까지 연결하는 흐름을 목표로 합니다.
    </td>
  </tr>
</table>
<br>

## 2. 문제 정의와 서비스 차별점

### 해결하고자 한 문제

| 문제 상황      | 사용자 불편                      |
| ---------- | --------------------------- |
| 🍽️ 메뉴 결정  | 매일 무엇을 먹을지 고민하는 데 시간이 오래 걸림 |
| 💰 예산 관리   | 월 식비 안에서 여러 끼니를 구성하기 어려움    |
| 🥗 영양 고려   | 영양 균형과 개인 선호를 함께 고려하기 어려움   |
| ⚠️ 알레르기 확인 | 알레르기 및 제외 재료를 메뉴마다 확인해야 함   |
| 🛒 장보기     | 필요한 재료와 상품 가격을 직접 비교해야 함    |

### 오늘의 끼니의 차별점

| 기존 서비스                    | 오늘의 끼니                         |
| ------------------------- | ------------------------------ |
| ✍️ 사용자가 먹은 식단을 직접 기록      | ✨ 사용자 조건 기반 식단 자동 추천           |
| 🔍 개별 메뉴 또는 레시피 검색 중심     | 📅 식단 스타일과 월간 식단 단위 구성         |
| 🔁 메뉴 반복 및 장기 구성을 사용자가 관리 | ⚙️ 추천·최적화 엔진을 통한 다양성 및 반복 제어   |
| 📖 레시피 제공에 집중             | 🛒 식단과 식재료 구매 흐름 연결            |
| 👤 단일 사용자 조건 중심           | 👨‍👩‍👧‍👦 가구 형태와 가구원 정보까지 반영 |

<br>

## 3. 핵심 기능

### 👤 사용자 개인화

- 식단 목표, 월 예산, 활동량, 요리 실력 입력
- 선호 음식과 비선호 재료 설정
- 알레르기 및 제외 재료 기반 메뉴 필터링
- 가구 형태와 가구원 정보를 반영한 사용자 설정
- 사용자 조건 기반 페르소나 후보 추천

### 🥗 맞춤형 식단 추천

- 사용자 조건에 맞는 식단 스타일 후보 제공
- 선택한 스타일을 기반으로 월간 식단 최적화
- 끼니별 대체 메뉴 후보 제공
- 일별·월별 식단 캘린더 조회
- 메뉴별 영양 성분과 상세 정보 제공

### 🔄 식단 변경 및 피드백

- 특정 날짜와 끼니의 메뉴 변경
- 기존 식단의 균형을 고려한 대체 메뉴 제공
- 식단 만족도 및 사용자 피드백 저장
- 피드백을 활용한 추천 고도화 기반 마련

### 🛒 장보기 연결

- 식단에 필요한 재료 목록 구성
- 재료별 상품 및 가격 정보 조회
- 선택한 식재료를 장보기 목록에 추가
- 장보기 완료 여부와 예상 비용 관리
- 삭제한 장보기 항목 복원 지원

### 🔐 사용자 및 인증

- 게스트 로그인 지원
- Google, Kakao, Naver 소셜 로그인
- Access Token과 Refresh Token 기반 인증
- 로그아웃 및 회원 탈퇴 시 토큰 무효화
- 사용자 프로필과 온보딩 설정 관리

<br>

## 4. 사용자 서비스 흐름

<p align="center">
  <img src="assets/images/service-flow.png" width="1100" alt="오늘의 끼니 서비스 흐름" />
</p>

```text
회원가입 및 로그인
→ 사용자·가구 정보 입력
→ 추천 페르소나 및 식단 스타일 선택
→ 월간 식단 생성 요청
→ 식단 생성 상태 조회
→ 월간 캘린더 및 메뉴 상세 확인
→ 대체 메뉴 선택
→ 장보기 목록 생성 및 가격 확인
→ 식단 피드백 등록
```

월간 식단 생성과 같이 처리 시간이 긴 작업은 비동기로 수행하며, Frontend는 작업 ID를 사용해 생성 상태를 주기적으로 조회합니다.

<br>

## 5. 전체 시스템 아키텍처

<p align="center">
  <img src="assets/images/system-architecture.png" width="1100" alt="오늘의 끼니 전체 시스템 아키텍처" />
</p>

오늘의 끼니는 `Frontend`, `Backend`, `Modeling`, `RAG`를 역할별로 분리하고, 각 파트를 API 기반으로 연결한 구조입니다.

```text
Frontend
  └── Flutter 기반 사용자 화면
          ↓ JSON API

Backend
  ├── FastAPI 기반 API 서버
  ├── OAuth2 및 JWT 인증
  ├── Celery 비동기 작업 처리
  ├── Redis 작업 큐·캐싱·분산 락
  └── SQLAlchemy 기반 PostgreSQL 저장
          ↓ JSON API

Modeling
  ├── Profile Builder
  ├── RAG Candidate Request & Fallback
  ├── Scoring Engine
  ├── MMR Re-ranking
  ├── Monthly Plan Optimizer
  └── Plan Quality Validator
          ↕ JSON API

RAG
  ├── Ollama 기반 데이터 가공
  ├── Neo4j 지식 그래프
  └── GraphRAG 기반 후보 메뉴 검색
```

### 파트별 역할

| 파트 | 주요 역할 |
|---|---|
| 📱 Frontend | 사용자 입력, 온보딩, 식단 캘린더, 메뉴 상세 및 장보기 화면 제공 |
| ⚙️ Backend | 인증, 요청 검증, 비동기 작업 처리, 캐싱, 데이터 저장 및 파트 간 API 연동 |
| 🧠 Modeling | 사용자 프로필 생성, 후보 메뉴 평가, 재랭킹, 월간 식단 최적화 및 결과 검증 |
| 🕸️ RAG | 레시피·재료·영양 관계 데이터를 기반으로 후보 메뉴를 검색하고 Modeling에 제공 |
| 🚀 Infrastructure | Docker 기반 실행 환경, AWS EC2 배포, Nginx HTTPS 연결 및 Prometheus·Grafana 모니터링 |


<table style="background-color:#EAF4FF; border-left:6px solid #4D96D9; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>💡 구조 핵심</strong><br>
      월간 식단 생성과 같이 처리 시간이 긴 요청은 Backend에서 Celery 작업으로 분리합니다. Redis는 작업 큐, 캐싱 및 분산 락에 사용하며, 생성된 식단 결과는 PostgreSQL에 저장합니다. <br>
      운영 환경에서는 Docker와 AWS EC2를 기반으로 서비스를 실행하고, Nginx를 통해 외부 요청을 전달합니다. Modeling API의 요청 수, 오류율 및 응답시간 지표는 Prometheus가 수집하고 Grafana에서 시각화합니다.
    </td>
  </tr>
</table>




## 6. 파트별 기술 스택

### 📱 Frontend

| 기술 | 사용 목적 |
|---|---|
| Flutter | 크로스 플랫폼 모바일 애플리케이션 |
| Riverpod | 화면 및 비동기 상태 관리 |
| Dio | Backend API 통신 |
| go_router | 화면 라우팅 |
| Figma | UI·UX 설계 및 프로토타입 제작 |

### ⚙️ Backend

| 기술 | 사용 목적 |
|---|---|
| Python 3.13 | Backend 개발 언어 |
| FastAPI | REST API 서버 |
| Pydantic V2 | 요청·응답 데이터 검증 |
| SQLAlchemy | ORM 기반 데이터 접근 |
| PostgreSQL | 사용자·식단·장보기 데이터 저장 |
| Redis | 작업 큐, 캐싱, 분산 락 및 토큰 블랙리스트 |
| Celery | 식단 생성 비동기 작업 처리 |
| HTTPX | Modeling 등 외부 API 통신 |
| OAuth2 / JWT | 소셜 로그인 및 사용자 인증 |

### 🧠 Modeling

| 기술 | 사용 목적 |
|---|---|
| Python 3.11 | 추천 및 식단 최적화 엔진 |
| FastAPI | 독립 Modeling API 제공 |
| Pydantic | 입력·출력 스키마 검증 |
| OR-Tools | 사용자 조건 기반 월간 식단 최적화 |
| Weighted Scoring | 예산·영양·선호도·난이도 반영 |
| MMR | 유사 메뉴 반복 완화 및 다양성 제어 |

### 🕸️ RAG / Data

| 기술 | 사용 목적 |
|---|---|
| Python 3.11 | 데이터 파이프라인 및 API 구현 |
| LangChain / GraphRAG | 벡터·그래프 기반 복합 검색 |
| Neo4j | 메뉴·재료·영양 관계 지식 그래프 |
| Vector DB | 메뉴와 레시피 임베딩 검색 |
| Ollama / Gemma 2 | 레시피 및 관계 데이터 가공 |
| Chromium Automation | 레시피와 영양 데이터 수집 |

### 🚀 Infrastructure

| 기술 | 사용 목적 |
|---|---|
| Docker / Docker Compose | 파트별 실행 환경 표준화 |
| GitHub Actions | 테스트, 이미지 빌드 및 배포 자동화 |
| AWS EC2 | Backend 및 Modeling 서버 운영 |
| AWS RDS | PostgreSQL 운영 데이터베이스 |
| GHCR | Docker 이미지 저장 |
| Nginx / HTTPS | Reverse Proxy 및 외부 통신 보호 |

<br>

## 7. 프로젝트 구조

```text
todays_ggini/
├── frontend/
│   └── today-s_kkini/       # Flutter 모바일 애플리케이션
│
├── backend/                 # FastAPI API 및 비동기 처리 서버
│
├── modeling/                # 추천·식단 최적화 엔진 및 Modeling API
│
├── rag/                     # 데이터 수집, 지식 그래프 및 후보 검색
│
├── scripts/                 # 공통 실행 및 검증 스크립트
│
├── assets/
│   └── images/              # README 및 프로젝트 소개 이미지
│
├── Dockerfile.modeling
├── docker-compose.modeling.yml
└── README.md
```

<br>

<table style="background-color:#FFF6C7; border-left:6px solid #E6C85C; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⭐ 파트별 세부사항</strong><br>
      각 파트의 내부 모듈 구조와 구현 세부 사항은 해당 파트 README에서 확인할 수 있습니다.
    </td>
  </tr>
</table>

<br>

## 8. 파트별 상세 문서

| 파트 | 문서 | 주요 내용 |
|---|---|---|
| 📱 Frontend | [`frontend/today-s_kkini/README.md`](frontend/today-s_kkini/README.md) | 화면 구성, 상태 관리 및 API 연동 |
| ⚙️ Backend | [`backend/README.md`](backend/README.md) | 인증, 데이터베이스, 비동기 처리 및 API |
| 🧠 Modeling | `modeling/README.md` | 추천, 최적화, 검증 및 Modeling API |
| 🕸️ RAG / Data | [`rag/readme.md`](rag/readme.md) | 데이터 수집, Neo4j, GraphRAG 및 후보 검색 |

> 루트 README는 오늘의 끼니 서비스의 전체 구조와 사용자 흐름을 설명하며, 파트별 상세 구현은 각 디렉터리의 README에서 관리합니다.

<br>

## 9. 기본 실행 방법

### 9-1. 저장소 클론

```bash
git clone https://github.com/hekim-cse/todays_ggini.git
cd todays_ggini
```

### 9-2. Backend 실행

```bash
python3.13 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

PYTHONPATH=.:backend:modeling \
python -m uvicorn app.main:app \
  --app-dir backend \
  --reload
```

Backend API 문서:

```text
http://127.0.0.1:8000/docs
```

### 9-3. Modeling 실행

```bash
python3.11 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r modeling/requirements.txt
```

로컬 Modeling API 실행:

```bash
ENV=local \
PYTHONPATH=modeling \
RAG_API_URL="https://api.kkini.cloud/api/v1/meal-candidates" \
python -m uvicorn api.server:app \
  --host 0.0.0.0 \
  --port 8001 \
  --reload
```

Modeling API 문서:

```text
http://127.0.0.1:8001/docs
```

상태 확인:

```bash
curl http://127.0.0.1:8001/health
```

Docker 실행:

```bash
MODELING_API_KEY=local-secret-key \
docker compose \
  -f docker-compose.modeling.yml \
  up --build
```

### 9-4. Frontend 실행

```bash
cd frontend/today-s_kkini
flutter pub get
flutter run
```

### 9-5. RAG 실행

```bash
cd rag

python3.11 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python api_server.py
```

> 파트별 실행에 필요한 환경변수와 상세 설정은 각 파트 README를 참고합니다.

<br>

## 10. 주요 API 및 연동 흐름

### 인증 및 사용자

| Method | Endpoint | 설명 |
|---|---|---|
| `POST` | `/api/v1/auth/guest/init` | 게스트 세션 생성 |
| `POST` | `/api/v1/auth/google` | Google 로그인 |
| `POST` | `/api/v1/auth/kakao` | Kakao 로그인 |
| `POST` | `/api/v1/auth/naver` | Naver 로그인 |
| `POST` | `/api/v1/auth/refresh` | Access Token 재발급 |
| `GET` | `/api/v1/user/me` | 사용자 정보 조회 |

### 식단

| Method | Endpoint | 설명 |
|---|---|---|
| `POST` | `/api/v1/meal/generate` | 월간 식단 비동기 생성 요청 |
| `GET` | `/api/v1/meal/generate/status/{job_id}` | 식단 생성 상태 조회 |
| `POST` | `/api/v1/meal/confirm` | 생성된 식단 확정 |
| `GET` | `/api/v1/meal/calender` | 월간 식단 캘린더 조회 |
| `GET` | `/api/v1/meal/{date}` | 일일 식단 조회 |
| `POST` | `/api/v1/meal/{date}/swap` | 메뉴 변경 |
| `POST` | `/api/v1/meal/feedback` | 식단 피드백 저장 |

### 장보기

| Method | Endpoint | 설명 |
|---|---|---|
| `GET` | `/api/v1/shopping/ingredients/{ingredient_id}/prices` | 재료별 가격 조회 |
| `POST` | `/api/v1/shopping/add-shopping-items` | 장보기 항목 추가 |
| `GET` | `/api/v1/shopping/shopping-list` | 장보기 목록 조회 |
| `PATCH` | `/api/v1/shopping/shopping-list/items/check` | 구매 상태 변경 |
| `POST` | `/api/v1/shopping/shopping-list/items/batch-delete` | 장보기 항목 삭제 |
| `POST` | `/api/v1/shopping/shopping-list/items/restore` | 삭제 항목 복원 |

대표적인 식단 생성 흐름은 다음과 같습니다.

```text
Frontend
→ Backend 식단 생성 요청
→ Celery 작업 등록 및 job_id 반환
→ Modeling API 호출
→ RAG 메뉴 후보 검색
→ 월간 식단 최적화
→ PostgreSQL 저장
→ Frontend Polling
→ 생성된 식단 표시
```

<br>

## 11. 협업 방식

본 프로젝트는 Pull Request 기반으로 협업합니다.

```text
main
└── 최종 배포 및 릴리즈 브랜치

develop
└── 통합 개발 브랜치

feat/*
fix/*
refactor/*
docs/*
└── 기능별 작업 브랜치
```

### 작업 흐름

```bash
git checkout develop
git pull origin develop
git checkout -b feat/담당파트-작업명
```

```text
작업 브랜치 생성
→ 구현 및 테스트
→ Commit 및 Push
→ Pull Request 생성
→ 팀원 Review
→ develop 병합
→ 작업 브랜치 삭제
```

### Commit Convention

| 타입 | 설명 | 예시 |
|---|---|---|
| `feat` | 기능 추가 | `feat: 월간 식단 생성 API 추가` |
| `fix` | 오류 수정 | `fix: 메뉴 변경 응답 누락 수정` |
| `refactor` | 구조 및 코드 개선 | `refactor: 사용자 모델 구조 분리` |
| `docs` | 문서 수정 | `docs: 통합 README 수정` |
| `test` | 테스트 추가 및 수정 | `test: Modeling 오류 응답 테스트 추가` |
| `chore` | 설정 및 기타 작업 | `chore: Docker 실행 환경 수정` |

<br>

## 12. 팀원 역할

<p align="center">
  <img src="assets/images/team-roles.png" width="1150" alt="오늘의 끼니 팀원 역할" />
</p>
