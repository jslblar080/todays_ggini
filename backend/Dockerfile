FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 상위 폴더 루트 기준이므로 backend 폴더 안의 requirements를 가리킵니다.
COPY backend/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY ai/modeling/requirements.txt ./ai_requirements.txt

RUN pip install --no-cache-dir -r ai_requirements.txt

# ai 폴더와 backend 폴더가 있는 최상위 루트 전체를 복사합니다.
COPY . .

# backend 폴더를 루트 디렉터리로 삼아서 그 안의 app.main:app을 실행하도록 강제 지정합니다.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]