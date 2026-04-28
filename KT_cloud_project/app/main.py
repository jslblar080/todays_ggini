from fastapi import FastAPI
from app.api import user, auth
from app.db.session import engine
from app.db import base  # 중요: 모델들을 import 해야 테이블이 생성됨

# 서버 시작 시 테이블 생성
base.Base.metadata.create_all(bind=engine)

app = FastAPI(title="오늘의 끼니 API")

# 라우터 연결
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(user.router, prefix="/api/v1/users", tags=["users"])

@app.get("/")
def home():
    return {"message": "오늘의 끼니 서버 정상 작동 중!"}