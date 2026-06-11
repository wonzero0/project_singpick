from fastapi import FastAPI, Request, Depends, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from pathlib import Path
from urllib.parse import quote
from schemas import RequestReserve
import sys, os, subprocess, models
from database import engine, get_db
from routers import booth, users, songs, library, kiosk, mr
from state import BOOTH_ID
import time

# 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), "ai_module"))
try:
    from Lighting.inside.led_controller import start_led as start_led_arduino, stop_led as stop_led_arduino
except Exception as e:
    print("[WARN] Arduino disabled:", e)
    def start_led_arduino(): pass
    def stop_led_arduino(): pass

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "kiosk" / "src1" / "dist"
ASSETS_DIR = DIST_DIR / "assets"

# DB 및 스키마 설정
models.Base.metadata.create_all(bind=engine)

def ensure_reservation_schema():
    inspector = inspect(engine)
    if "reservations" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("reservations")}
        with engine.begin() as conn:
            if "user_id" not in columns: conn.execute(text("ALTER TABLE reservations ADD COLUMN user_id VARCHAR(50) NULL"))
            if "booth_id" not in columns: conn.execute(text("ALTER TABLE reservations ADD COLUMN booth_id INT DEFAULT 1"))
            if "song_id" not in columns: conn.execute(text("ALTER TABLE reservations ADD COLUMN song_id INT"))

ensure_reservation_schema()

app = FastAPI(title="SingPick Server")
router = APIRouter()

# CORS 설정
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- 예약 로직 (RequestReserve) ---
@router.post("/reserve")
def reserve_song_endpoint(request: RequestReserve, db: Session = Depends(get_db)):
    print(f"[DEBUG /reserve] 요청 수신: {request}")
    try:
        # DB에 예약 정보 삽입
        new_res = models.Reservation(
            booth_id=request.booth_id,
            song_id=request.song_id,
            user_id=request.user_id,
            status="waiting"
        )
        db.add(new_res)
        db.commit()
        db.refresh(new_res)
        print(f"[DEBUG /reserve] DB 저장 성공: {new_res.booth_id}:{new_res.song_id}:{new_res.user_id}")
        return {
            "status": "success", 
            "reservation_key": f"{new_res.booth_id}:{new_res.song_id}:{new_res.user_id}"
        }
    except Exception as e:
        db.rollback()
        print(f"[ERROR /reserve] DB 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 모든 요청을 로깅하는 미들웨어 추가
class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        print(f"[RequestLogger] Path: {request.url.path}, Method: {request.method}, Status: {response.status_code}, Time: {process_time:.4f}s")
        return response

app.add_middleware(RequestLoggerMiddleware)

@router.post("/led/play")
def led_play():
    start_led_arduino()
    return {"status": "success", "message": "Inside LED (Mirror Ball) started"}

@router.post("/led/stop")
def led_stop():
    stop_led_arduino()
    return {"status": "success", "message": "Inside LED (Mirror Ball) stopped"}

# 라우터 등록
app.include_router(users.router)
app.include_router(booth.router)
app.include_router(songs.router)
app.include_router(library.router)
app.include_router(kiosk.router)
app.include_router(mr.router, prefix="/library")
app.include_router(router) # 위에서 정의한 예약 라우터

# 정적 파일 마운트
app.mount("/mr_files", StaticFiles(directory="downloaded_mrs"), name="mr_files")
if ASSETS_DIR.exists(): app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
if DIST_DIR.exists(): app.mount("/dist", StaticFiles(directory=str(DIST_DIR)), name="dist")

# LED 제어 및 노래 초기화 로직 등은 기존과 동일하게 유지...
# (여기에 LED 제어, init_dummy_songs, 세션 관련 코드들을 붙여넣으세요)

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    api_prefixes = ["/kiosk/", "/songs/", "/library/", "/led/", "/session/", "/result", "/qr", "/reserve"]
    if any(full_path.startswith(prefix.strip("/")) for prefix in api_prefixes):
        return {"status": "error", "message": "API endpoint not found"}
    return FileResponse(str(DIST_DIR / "index.html"))