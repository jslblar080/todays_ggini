from fastapi import FastAPI
import os
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.scheduler import purge_expired_data
from app.api import user, auth, meal, shopping
from app.db.session import engine
from app.db import base  # 중요: 모델들을 import 해야 테이블이 생성됨
from fastapi.middleware.cors import CORSMiddleware

# 서버 시작 시 테이블 생성
base.Base.metadata.create_all(bind=engine)

app = FastAPI(title="오늘의 끼니 API")

# 모든 도메인에서의 접근을 허용하거나, 특정 프론트엔드 주소만 허용합니다.
origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서버 구동 시 실행될 로직
@app.on_event("startup")
def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    
    # 매일 새벽 4시 0분에 일괄 삭제 함수 실행
    scheduler.add_job(purge_expired_data, 'cron', hour=4, minute=0)
    
    scheduler.start()
    print("자동 데이터 정리(TTL) 스케줄러 가동 시작 - 매일 04:00")

# 1. 이미지가 저장될 실제 폴더가 없으면 자동 생성합니다.
os.makedirs("app/static/images", exist_ok=True) 

# 2. /images URL로 요청이 오면 app/static/images 폴더의 파일을 제공하도록 연결합니다.
app.mount("/images", StaticFiles(directory="app/static/images"), name="images")

# 라우터 연결
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])
app.include_router(meal.router, prefix="/api/v1/meal", tags=["meal"])
app.include_router(shopping.router, prefix="/api/v1/shopping", tags=["shopping"])

@app.get("/")
def home():
    return {"message": "오늘의 끼니 서버 정상 작동 중!"}