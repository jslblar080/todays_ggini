from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./today_kkini.db"

engine = create_engine(   # 데이터베이스와의 연결을 위한 엔진 객체를 생성
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} # 여러 스레드에서 동일한 데이터베이스 연결을 사용할 수 있도록 허용
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# autocommit=False: 세션이 자동으로 커밋되지 않도록 설정합니다. 즉, 명시적으로 커밋해야만 변경사항이 데이터베이스에 반영됩니다
# autoflush=False: 세션이 자동으로 플러시되지 않도록 설정합니다. 이는 세션에 있는 변경사항이 데이터베이스에 즉시 반영되지 않도록 합니다.
# bind=engine: 생성된 세션이 앞서 생성한 엔진과 연결되도록 합니다