# 오늘의 끼니 — RAG (Retrieval-Augmented Generation)

스마트 영양 & 예산 플래너 **오늘의 끼니**의 핵심 지식 베이스이자 AI 식단 추천 및 대체 메뉴 생성을 담당하는 RAG 파이프라인 엔진입니다.
사용자의 페르소나·온보딩 정보에 맞추어 영양 제약 조건과 가격 예산 범위 내의 최적화된 식단 후보군 및 메뉴 데이터를 가공하여 Modeling 및 Backend 레이어에 전달합니다.

통합 레포지토리의 `rag/` 폴더 하위에서 독립적인 Python 가상환경(`.venv`)으로 관리되며, 별도의 Cloud 인프라 환경에서 추론 엔진 및 지식 그래프가 구동됩니다.

---

## 🛠 기술 스택

| 영역 | 선택 기술 | 비고 |
| --- | --- | --- |
| **언어 / 환경** | Python `3.11.x` 이상 / `.venv` | 패키지 격리 및 의존성 관리 |
| **RAG 프레임워크** | LangChain / GraphRAG | 벡터 및 그래프 기반 복합 검색 아키텍처 |
| **데이터베이스** | Neo4j / Vector DB | 데이터 간 관계성(지식 그래프) 및 임베딩 벡터 저장 |
| **LLM / 오케스트레이션** | Ollama / `gemma2:9b` | 로컬/클라우드 환경 내 독립 모델 추론 수행 |
| **데이터 수집** | Chromium 기반 자동화 | 영양 정보 및 만개의 레시피 로우 데이터 수집 |

---

## 📐 아키텍처 — 데이터 생명주기 기반 레이어 분리

`rag/` 디렉토리는 데이터의 수집(Scrape)부터 가공(Process), DB 반영(Update), 그리고 지식 제공(DB/API)까지의 흐름을 반영하여 기능별 모듈로 격리되어 있습니다.

### 디렉토리 구조

```text
rag/
├── main.py                   # RAG 파이프라인 메인 실행 진입점
├── api_server.py             # Modeling/Backend 연동용 API 엔드포인트
├── requirements.txt          # 파이썬 의존성 패키지 명세
├── chrome_automation_profile/# [로컬 전용] 크롬 자동화 세션 프로필 (git 추적 제외)
├── data/                     # 데이터 저장소 (대용량 원천/DB 파일은 git 추적 제외)
│   └── raw_mankae_recipes.jsonl
└── src/                      # RAG 핵심 소스코드 폴더
    ├── db/                   # 그래프 DB(Neo4j) 및 벡터 DB 연결 및 쿼리 레이어
    ├── processor/            # 수집 데이터 파싱, 임베딩 분할 및 그래프 스키마 매핑
    ├── scraper/              # 만개의 레시피 등 외부 식단 데이터 웹 스크래퍼 코드
    └── updater/              # 파이프라인 갱신 및 DB 동기화 모듈

```

### 데이터 흐름 (Data Flow)

```text
[외부 식단/레시피 데이터]
       │
       ▼ (src/scraper)
[Raw 데이터 자산 (.jsonl)] ───► 구조화/임베딩 (src/processor)
                                      │
                                      ▼ (src/db & updater)
                        [Neo4j 지식 그래프 & Vector DB]
                                      │
                                      ▼ (api_server.py)
                        [Modeling 파이프라인 (식단 최적화)]

```

* **Scraper**: 정기적으로 외부 영양소 및 레시피 소스를 크롤링하여 `data/` 내에 로우 파일로 적재합니다.
* **Processor**: 텍스트 청킹, 벡터 임베딩 변환 및 엔티티 간의 관계를 분석하여 지식 그래프 형태로 스키마를 정규화합니다.
* **DB/Updater**: 정제된 데이터를 데이터베이스에 안전하게 적재/갱신하고 인덱싱을 관리합니다.
* **API Server**: 모델링 파트의 요청을 받아 지식 그래프와 벡터 검색을 융합한 최적의 메뉴 후보군을 응답합니다.

---

## 🧩 핵심 기능 (Modules)

| 모듈 / 파일 경로 | 설명 |
| --- | --- |
| `src/scraper/` | 만개의 레시피 스크래퍼 및 영양성분 공공데이터 수집 엔진 |
| `src/processor/` | LangChain 기반 텍스트 분할 및 엔티티-관계(Entity-Relation) 추출기 |
| `src/db/` | Neo4j Cypher 쿼리 빌더 및 벡터 유사도 검색 인터페이스 |
| `src/updater/` | 신규 레시피 및 재료 최저가 변동 데이터 DB 배치 업데이트 모듈 |
| `api_server.py` | Modeling 파이프라인 연동을 위한 전용 임베딩/지식 검색 API 서빙 |
| `graph_product_prelinker.py` | 수집된 식재료 데이터와 마트 최저가 상품 데이터 간의 개체명 연결(EL) 스크립트 |
| `post_cleaner.py` | 불완전한 문장 데이터 및 중복 레시피 노드 정제를 위한 후처리 유틸리티 |

---

## 🔑 환경변수 및 보안 (.env)

대용량 데이터베이스 접근 자격 증명 및 LLM API Key 등 민감한 시크릿 정보가 포함되므로, `.env` 파일은 커밋하지 않고 로컬 환경에서 개별 관리합니다.

| 환경변수 키 | 설명 | 비고 |
| --- | --- | --- |
| `NEO4J_URI` | Neo4j 데이터베이스 접속 주소 | 기본값: `bolt://localhost:7687` |
| `NEO4J_USERNAME` | Neo4j 접속 계정 명 |  |
| `NEO4J_PASSWORD` | Neo4j 접속 비밀번호 |  |
| `OLLAMA_BASE_URL` | Ollama 추론 서버 주소 | 기본값: `http://localhost:11434` |
| `EMBEDDING_MODEL_NAME` | 지식 벡터화에 사용할 임베딩 모델명 |  |
| `LLM_MODEL_NAME` | 엔티티 추출 및 가공에 사용할 LLM 모델명 |  |

---

## 🚀 실행 방법

### 1. 환경 설정 및 의존성 설치

```bash
# RAG 디렉토리로 이동
cd rag

# 파이썬 가상환경 생성 및 활성화 (최초 1회)
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux 기준
# Windows 환경일 경우: .\venv\Scripts\activate

# 의존성 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt

```

### 2. 파이프라인 단계별 실행

```bash
# [1단계] 데이터 수집: 레시피 및 식재료 스크래핑 실행
python -m src.scraper.main

# [2단계] 데이터 가공 및 적재: 로우 데이터 임베딩 및 지식 그래프 구축
python main.py

# [3단계] API 서빙: Modeling 파트 연동용 RAG API 서버 구동
python api_server.py

```

---

## 📌 개발 및 릴리즈 노트

* **데이터 제외 원칙 (`.gitignore`)**
* 로컬 수행 시 생성되는 크롬 프로필(`chrome_automation_profile/`), Neo4j 내부 트랜잭션 로그 및 데이터 파일(`rag/data/neo4j/`), 무거운 텍스트 자산(`.jsonl`, `.csv`)은 레포지토리 용량 제한(100MB) 및 보안을 위해 깃 추적에서 제외합니다.


* **Knowledge Graph-first 아키텍처**
* 단순 키워드/벡터 검색의 한계를 극복하기 위해 **재료-음식-영양소** 간의 상관관계를 Neo4j 지식 그래프로 구현했습니다. 이를 통해 사용자 페르소나 맞춤형 필터링(예: 특정 알레르기 유발 재료 제외, 당뇨식단 제약 충족 등)에 유연하게 대응합니다.


* **버전 관리 권고**
* 본 RAG 구현부는 내부 엔진 소스 공유를 목적으로 포함되었으며, 실제 운영 서버 설정 및 배처(Batch) 등 인프라 아키텍처 관련 세부 내용은 포함하고 있지 않습니다.