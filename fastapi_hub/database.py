import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 현재 파일(database.py)이 위치한 폴더 경로 추출
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 상위 폴더(agri_platform)에 있는 agri_data.db 경로 생성
# os.path.join을 쓰면 윈도우/맥/리눅스 어디서든 경로가 꼬이지 않습니다.
DB_PATH = os.path.join(BASE_DIR, "..", "agri_data.db")

# 3. SQLite 파일 경로 설정 (상위 폴더의 파일을 가리킴)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# (참고) DB 세션을 가져오는 공통 함수 (main.py에서 사용 중일 거예요)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()