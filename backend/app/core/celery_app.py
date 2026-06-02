import os
from celery import Celery
from app.db.base import Base

# Redis 브로커 URL 설정 (환경변수나 기존 settings 활용)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery 앱 초기화
celery_app = Celery(
    "meal_plan_worker",
    broker=REDIS_URL,
    backend=REDIS_URL # 태스크의 최종 결과물(return 값)을 보관할 백엔드
)

# 윈도우 환경 및 대규모 무거운 연산에 최적화된 Celery 옵션 조정
celery_app.conf.update(
    timezone="Asia/Seoul",
    task_track_started=True,          # 태스크 시작 상태 추적 활성화
    worker_max_tasks_per_child=100,   # 메모리 누수 방지를 위해 100번 작업 후 프로세스 재생성
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_ignore_result=True,   # 태스크의 return 결과를 저장하지 않음 (메모리 절약)
    task_store_errors_even_if_ignored=True # 단, 에러가 났을 때의 로그는 추적할 수 있게 허용
)

# 실행할 태스크 모듈 등록 (app.tasks 모듈 안에 등록할 예정)
celery_app.autodiscover_tasks(["app.api.meal"], force=True)