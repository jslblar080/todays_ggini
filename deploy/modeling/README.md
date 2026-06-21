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

- cp deploy/modeling/env.modeling.example deploy/modeling/.env.modeling.prod

생성한 `.env.modeling.prod` 파일에서 `MODELING_API_KEY` 값을 실제 secret으로 변경한다.

주의: `.env.modeling.prod` 파일은 Git에 커밋하지 않는다.

---

## 4. Docker Compose 실행

EC2에서 아래 명령어로 Modeling API 컨테이너를 빌드하고 실행한다.

- docker compose --env-file deploy/modeling/.env.modeling.prod -f deploy/modeling/docker-compose.ec2.yml up -d --build

상태 확인:

- docker ps
- docker logs todays-ggini-modeling
- curl -s http://127.0.0.1:8000/health

정상 응답에는 `status: ok`와 `service: todays-ggini-modeling`이 포함되어야 한다.

---

## 5. Nginx 설정

Nginx 예시 설정을 복사한다.

- sudo cp deploy/modeling/nginx-modeling-api.conf.example /etc/nginx/sites-available/modeling-api
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

- docker compose --env-file deploy/modeling/.env.modeling.prod -f deploy/modeling/docker-compose.ec2.yml down

컨테이너 재시작:

- docker compose --env-file deploy/modeling/.env.modeling.prod -f deploy/modeling/docker-compose.ec2.yml up -d --build

---

## 9. 자동 배포 확장 계획

수동 배포가 안정화되면 다음 단계로 확장한다.

1. GitHub Actions에서 GHCR image publish
2. EC2에서 GHCR image pull
3. docker compose up -d로 컨테이너 교체
4. /health 기반 배포 검증
5. 실패 시 이전 image tag로 rollback
