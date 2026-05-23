from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models
from database import engine, get_db
from routers import booth, users, songs, library, kiosk, mr  # kiosk 포함
from fastapi.staticfiles import StaticFiles
#from led_controller import start_led, stop_led

# 🔥🔥🔥 추가 (ai_module 경로 문제 해결)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "ai_module"))

# ===============================
# DB 테이블 생성
# ===============================
models.Base.metadata.create_all(bind=engine)

# ===============================
# FastAPI 앱 생성
# ===============================
app = FastAPI(title="SingPick Server")

@app.post("/led/play")
def led_play():
    start_led()
    return {"message": "LED START"}

@app.post("/led/stop")
def led_stop():
    stop_led()
    return {"message": "LED STOP"}

# ===============================
# Kiosk 관련: 정적 파일 서비스
# ===============================
app.mount("/kiosk_static", StaticFiles(directory="kiosk"), name="kiosk_static")

# ===============================
# CORS 설정
# ===============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (테스트용), 운영 시 실제 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# 라우터 등록
# ===============================
app.include_router(users.router)
app.include_router(booth.router)
app.include_router(songs.router)
app.include_router(library.router)
app.include_router(kiosk.router)
app.include_router(mr.router, prefix="/library")

# ===============================
# 정적 MR 파일 서비스
# ===============================
app.mount("/mr_files", StaticFiles(directory="downloaded_mrs"), name="mr_files")

# ===============================
# 임시 노래 데이터 초기화 (10곡)
# ===============================
def init_dummy_songs(db: Session):
    if db.query(models.Song).count() == 0:
        dummy_songs = [
            models.Song(title="0+0", singer="한로로", ky_number=99991),
            models.Song(title="한숨", singer="이하이", ky_number=99992),
            models.Song(title="여름밤에 우리", singer="전진희(feat. wave to earth)", ky_number=99993),
            models.Song(title="좋은 날", singer="아이유", ky_number=1001),
            models.Song(title="너랑 나", singer="아이유", ky_number=1002),
            models.Song(title="밤편지", singer="아이유", ky_number=1003),
            models.Song(title="보고 싶다", singer="김범수", ky_number=2001),
            models.Song(title="응급실", singer="izi", ky_number=3001),
            models.Song(title="소주 한 잔", singer="임창정", ky_number=4001),
            models.Song(title="Hype Boy", singer="NewJeans", ky_number=5001),
        ]
        db.add_all(dummy_songs)
        db.commit()
        print("🎵 [System] 가짜 노래 10곡이 DB에 저장되었습니다!")

@app.on_event("startup")
def on_startup():
    db = next(get_db())
    init_dummy_songs(db)

# ===============================
# 루트 경로
# ===============================
@app.get("/")
def read_root():
    return {"message": "SingPick Server is Running!"}