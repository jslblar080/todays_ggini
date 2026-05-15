from fastapi import FastAPI
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

# 라우터 연결
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])
app.include_router(meal.router, prefix="/api/v1/meal", tags=["meal"])
app.include_router(shopping.router, prefix="/api/v1/shopping", tags=["shopping"])

@app.get("/")
def home():
    return {"message": "오늘의 끼니 서버 정상 작동 중!"}