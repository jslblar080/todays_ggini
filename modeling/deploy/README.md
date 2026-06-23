# Modeling Server Manual Deployment

## 목적

이 문서는 Modeling FastAPI 서버를 EC2에서 수동으로 배포하기 위한 절차를 정리한다.

초기 단계에서는 EC2 서버에 직접 접속하여 Docker Compose로 컨테이너를 실행한다.
이후 GHCR image pull 기반 배포와 GitHub Actions 자동 배포로 확장한다.

---

## 배포 구조

- Backend 또는 Client
- HTTPS
- Nginx
- Internal HTTP
- FastAPI Modeling Server container

FastAPI 컨테이너는 외부에 직접 노출하지 않는다.
컨테이너 포트는 EC2 내부 localhost에만 바인딩한다.

---

## 1. EC2 서버 준비

Ubuntu EC2 기준으로 Docker, Docker Compose plugin, Nginx를 설치한다.

- sudo apt update
- sudo apt install -y docker.io docker-compose-plugin nginx
- sudo systemctl enable docker
- sudo systemctl start docker
- sudo usermod -aG docker $USER

docker 그룹 적용을 위해 SSH 재접속이 필요할 수 있다.

---

## 2. 프로젝트 코드 준비

EC2 서버에서 repository를 clone하거나 기존 repository를 pull한다.

- git clone <repository-url>
- cd todays_ggini
- git checkout feat/modeling-manual-deployment
- git pull origin feat/modeling-manual-deployment

---

## 3. 환경변수 파일 준비

예시 파일을 복사해 실제 운영 환경변수 파일을 만든다.

- cp modeling/deploy/env.modeling.example modeling/deploy/.env.modeling.prod

생성한 `.env.modeling.prod` 파일에서 `MODELING_API_KEY` 값을 실제 secret으로 변경한다.

주의: `.env.modeling.prod` 파일은 Git에 커밋하지 않는다.

---

## 4. Docker Compose 실행

EC2에서 아래 명령어로 Modeling API 컨테이너를 빌드하고 실행한다.

- docker compose --env-file modeling/deploy/.env.modeling.prod -f modeling/deploy/docker-compose.ec2.yml up -d --build

상태 확인:

- docker ps
- docker logs todays-ggini-modeling
- curl -s http://127.0.0.1:8000/health

정상 응답에는 `status: ok`와 `service: todays-ggini-modeling`이 포함되어야 한다.

---

## 5. Nginx 설정

Nginx 예시 설정을 복사한다.

- sudo cp modeling/deploy/nginx-modeling-api.conf.example /etc/nginx/sites-available/modeling-api
- sudo ln -s /etc/nginx/sites-available/modeling-api /etc/nginx/sites-enabled/modeling-api

`server_name` 값을 실제 도메인으로 수정한다.

- sudo nginx -t
- sudo systemctl reload nginx

---

## 6. HTTPS 적용

운영 환경에서는 반드시 HTTPS를 적용한다.

초기 수동 배포 검증 후 Certbot 또는 ALB를 사용해 HTTPS를 적용한다.

권장 구조:

- Backend 또는 Client
- HTTPS
- Nginx 또는 ALB
- Internal HTTP
- FastAPI Modeling Server

---

## 7. 수동 배포 검증

서버 내부에서 확인:

- curl -s http://127.0.0.1:8000/health

외부에서 확인:

- curl -s https://<modeling-api-domain>/health

API Key 인증 확인:

- wrong API key 요청 시 401이 반환되어야 한다.
- 정상 API key 요청 시 모델링 API에 진입해야 한다.

---

## 8. 종료 및 재시작

컨테이너 종료:

- docker compose --env-file modeling/deploy/.env.modeling.prod -f modeling/deploy/docker-compose.ec2.yml down

컨테이너 재시작:

- docker compose --env-file modeling/deploy/.env.modeling.prod -f modeling/deploy/docker-compose.ec2.yml up -d --build

---

## 9. 자동 배포 확장 계획

수동 배포가 안정화되면 다음 단계로 확장한다.

1. GitHub Actions에서 GHCR image publish
2. EC2에서 GHCR image pull
3. docker compose up -d로 컨테이너 교체
4. /health 기반 배포 검증
5. 실패 시 이전 image tag로 rollback

## 운영 도메인 및 HTTPS

운영 모델링 API는 다음 도메인을 사용한다.

    https://modeling.todays-ggini.shop

요청 경로:

    Backend 또는 Client
    → Gabia DNS
    → EC2 Elastic IP
    → Nginx HTTPS :443
    → FastAPI container 127.0.0.1:8000

### DNS 레코드

    Type: A
    Host: modeling
    Value: EC2 Elastic IP

### Nginx 도메인 설정

    server_name modeling.todays-ggini.shop;

### 인증서 발급

    sudo certbot --nginx \
      -d modeling.todays-ggini.shop

Certbot이 Nginx에 인증서를 적용하고 HTTP 요청을 HTTPS로
리다이렉트하도록 설정한다.

### 인증서 자동 갱신 검증

    systemctl status certbot.timer --no-pager
    sudo certbot renew --dry-run

### 외부 배포 검증

    ./modeling/deploy/scripts/verify_https_deployment.sh

다른 주소를 검증하려면 환경변수로 전달한다.

    MODELING_API_BASE_URL=https://example.com \
      ./modeling/deploy/scripts/verify_https_deployment.sh

## 백엔드 연동 설정

백엔드는 다음 환경변수를 사용한다.

    MODELING_API_BASE_URL=https://modeling.todays-ggini.shop
    MODELING_API_KEY=<secret>
    MODELING_API_CONNECT_TIMEOUT_SECONDS=10
    MODELING_API_READ_TIMEOUT_SECONDS=120

`MODELING_API_KEY`는 Git에 저장하지 않고 운영 Secret 또는
서버 환경변수로 관리한다.

월간 식단 API는 RAG 조회와 최적화를 포함하므로 실제 HTTPS
E2E 검증에서 약 24초가 소요되었다.

운영 중에는 RAG 응답 지연, 후보 수 증가, EC2 CPU 부하,
동시 요청 등의 영향으로 처리 시간이 늘어날 수 있으므로
백엔드와 Nginx의 읽기 제한 시간은 충분한 여유를 둔다.

이번 수동 배포 검증 결과:

    HTTP status: 200
    Solver status: FEASIBLE
    Days: 30
    Selected meals: 90
    Estimated cost: 249201
    Warnings: []
    Response size: 약 1.47 MB
    End-to-end elapsed time: 약 24초

응답 크기가 크기 때문에 운영 로그에는 전체 응답 JSON을
기록하지 않는다. 다음과 같은 요약 정보만 기록하는 것을
권장한다.

    request_id
    http_status
    elapsed_ms
    solver_status
    days_count
    selected_menu_count
    failure_reason
    response_size_bytes

<br>

## 관련 문서

Modeling API의 FastAPI 서빙 구성부터 Docker 및 EC2 배포 과정은 아래 문서에서 확인할 수 있습니다.

- [🚀 Modeling FastAPI 서빙 및 배포](https://app.notion.com/p/FastAPI-3859e3e335cc8000b0edeb7366ca5ccc?source=copy_link)  
  FastAPI 서버 구성, API Key 인증, Docker 이미지, Nginx Reverse Proxy 및 EC2 배포 과정
