import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "singpick_db")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 2. 엔진 생성 (파이썬과 DB를 연결하는 자동차 엔진)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. 세션 생성 (DB와 대화하는 통로)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 모델 베이스 (테이블 만드는 틀)
Base = declarative_base()

# 5. DB 세션 가져오기 함수 (나중에 API에서 씁니다)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()