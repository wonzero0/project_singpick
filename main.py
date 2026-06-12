from fastapi import FastAPI, Request, Depends, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from pathlib import Path
from urllib.parse import quote
import sys, os, subprocess, time, models
from database import engine, get_db
from routers import booth, users, songs, library, kiosk, mr
from schemas import RequestReserve

# ===============================
# 경로 및 설정
# ===============================
BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "kiosk" / "src1" / "dist"
ASSETS_DIR = DIST_DIR / "assets"

sys.path.append(os.path.join(os.path.dirname(__file__), "ai_module"))
try:
    from Lighting.inside.led_controller import start_led as start_led_arduino, stop_led as stop_led_arduino
except Exception as e:
    print("[WARN] Arduino disabled:", e)
    def start_led_arduino(): pass
    def stop_led_arduino(): pass


# ===============================
# DB 및 스키마 초기화
# ===============================
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

# ===============================
# FastAPI 앱 및 미들웨어
# ===============================
app = FastAPI(title="SingPick Server")
router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        print(f"[RequestLogger] Path: {request.url.path}, Method: {request.method}, Status: {response.status_code}, Time: {process_time:.4f}s")
        return response

app.add_middleware(RequestLoggerMiddleware)

# ===============================
# 라우터 등록
# ===============================
app.include_router(users.router)
app.include_router(booth.router)
app.include_router(songs.router)
app.include_router(library.router)
app.include_router(kiosk.router)
app.include_router(mr.router, prefix="/library")
app.include_router(router) 

# ===============================
# 정적 파일 마운트
# ===============================
app.mount("/mr_files", StaticFiles(directory="downloaded_mrs"), name="mr_files")
if ASSETS_DIR.exists(): app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
if DIST_DIR.exists(): app.mount("/dist", StaticFiles(directory=str(DIST_DIR)), name="dist")

# ===============================
# 노래 데이터 초기화
# ===============================
def init_dummy_songs(db: Session):
    if db.query(models.Song).count() == 0:
        dummy_songs = [
            models.Song(title="0+0", singer="한로로", ky_number=81234),
            models.Song(title="한숨", singer="이하이", ky_number=49040),
            models.Song(title="사랑의 배터리", singer="홍진영", ky_number=46927),
            models.Song(title="여름밤에 우리", singer="전진희(feat. wave to earth)", ky_number=81235),
            models.Song(title="좋은 날", singer="아이유", ky_number=47250),
            models.Song(title="소주 한 잔", singer="임창정", ky_number=6279),
            models.Song(title="응급실", singer="izi", ky_number=64156),
            models.Song(title="가시", singer="버즈", ky_number=65005),
            models.Song(title="보고 싶다", singer="김범수", ky_number=6259),
            models.Song(title="Hype Boy", singer="NewJeans", ky_number=82222),
            models.Song(title="사건의 지평선", singer="윤하", ky_number=81111),
            models.Song(title="Tears", singer="소찬휘", ky_number=6133),
            models.Song(title="체념", singer="빅마마", ky_number=63273),
            models.Song(title="첫눈처럼 너에게 가겠다", singer="에일리", ky_number=49363),
            models.Song(title="모든 날, 모든 순간", singer="폴킴", ky_number=49764),
            models.Song(title="좋니", singer="윤종신", ky_number=49531),
            models.Song(title="오래된 노래", singer="스탠딩 에그", ky_number=47854),
            models.Song(title="취중진담", singer="전람회", ky_number=3350),
            models.Song(title="애인있어요", singer="이은미", ky_number=45367),
            models.Song(title="비밀번호 486", singer="윤하", ky_number=45851),
            models.Song(title="눈의 꽃", singer="박효신", ky_number=64645),
            models.Song(title="천년의 사랑", singer="박완규", ky_number=5455),
            models.Song(title="말리꽃", singer="이승철", ky_number=6233),
            models.Song(title="노래방에서", singer="장범준", ky_number=59998),
            models.Song(title="Ditto", singer="NewJeans", ky_number=83333),
            models.Song(title="Love Dive", singer="IVE", ky_number=84444),
            models.Song(title="다시 만난 세계", singer="소녀시대", ky_number=46014),
            models.Song(title="밤편지", singer="아이유", ky_number=49511),
            models.Song(title="오르트구름", singer="윤하", ky_number=85555),
            models.Song(title="스물다섯, 스물하나", singer="자우림", ky_number=77969),
            models.Song(title="너의 의미", singer="아이유", ky_number=78065),
            models.Song(title="안아줘", singer="정준일", ky_number=47625),
            models.Song(title="널 사랑하지 않아", singer="어반자카파", ky_number=49091),
            models.Song(title="우주를 줄게", singer="볼빨간사춘기", ky_number=49111),
            models.Song(title="TOMBOY", singer="(여자)아이들", ky_number=86666),
            models.Song(title="신호등", singer="이무진", ky_number=87777),
            models.Song(title="다정히 내 이름을 부르면", singer="경서예지", ky_number=88888),
            models.Song(title="취기를 빌려", singer="산들", ky_number=89999),
            models.Song(title="Dynamite", singer="BTS", ky_number=91111),
            models.Song(title="봄날", singer="BTS", ky_number=49222),
            models.Song(title="그대라는 사치", singer="한동근", ky_number=49123),
            models.Song(title="어디에도", singer="엠씨더맥스", ky_number=49015),
            models.Song(title="선물", singer="멜로망스", ky_number=49333),
            models.Song(title="에잇", singer="아이유", ky_number=92222),
            models.Song(title="Celebrity", singer="아이유", ky_number=93333),
            models.Song(title="Next Level", singer="aespa", ky_number=94444),
            models.Song(title="Antifragile", singer="LE SSERAFIM", ky_number=96666),
        ]
        db.add_all(dummy_songs)
        db.commit()
        print("🎵 [System] 노래 50곡이 DB에 저장되었습니다!")

@app.on_event("startup")
def on_startup():
    db = next(get_db())
    init_dummy_songs(db)

# ===============================
# 기타 엔드포인트
# ===============================
@app.post("/led/play")
def play_led():
    start_led_arduino()
    return {"status": "success"}

@app.post("/led/stop")
def stop_led():
    stop_led_arduino()
    return {"status": "success"}

@app.get("/qr", response_class=HTMLResponse)
def show_qr_page(request: Request):
    target_url = str(request.base_url)
    qr_data = quote(target_url, safe="")
    html_content = f"""
    <html>
        <head><title>SingPick QR Code Portal</title></head>
        <body>
            <div class="card">
                <h1>🎤 SingPick 모바일 연결 큐알</h1>
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={qr_data}" alt="QR Code">
                <div class="url-box">{target_url}</div>
            </div>
        </body>
    </html>
    """
    return html_content

results_db = {}
@app.post("/result")
def save_result(data: dict, db: Session = Depends(get_db)):
    user_id = data.get("user_id", "unknown")
    
    # 1. 데이터베이스(MySQL)의 analysis_results 테이블에 물리적으로 저장
    try:
        new_analysis = models.AnalysisResult(
            user_id=user_id,
            score=data.get("score"),
            pitch_hz_avg=data.get("pitch"),   # karaoke_main.py의 'pitch' 키 매핑
            tempo_bpm=data.get("tempo"),     # karaoke_main.py의 'tempo' 키 매핑
            volume_rms_avg=data.get("volume"),# karaoke_main.py의 'volume' 키 매핑
            feedback=data.get("feedback")
        )
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
        print(f"[System] {user_id}의 분석 결과가 DB에 성공적으로 저장되었습니다. (ID: {new_analysis.id})")
    except Exception as e:
        db.rollback()
        print(f"[Error] DB 저장 중 오류 발생: {e}")

    # 2. 실시간 조회를 위한 기존 메모리(딕셔너리) 저장 유지
    if user_id not in results_db: results_db[user_id] = []
    results_db[user_id].append(data)
    return {"status": "saved"}

@app.get("/result")
def get_result(user_id: str):
    return results_db.get(user_id, [])

recording_flag, stop_flag, process, current_song, session_active, total_songs = False, False, None, 0, True, 0

@app.post("/session/start")
def session_start(data: dict):
    global recording_flag, current_song, process, session_active, total_songs
    recording_flag, total_songs = True, data["total_songs"]
    if current_song == 0: current_song = 1
    session_active = True
    if process is None or process.poll() is not None:
        process = subprocess.Popen(["python", "-m", "ai_module.karaoke_main"])
    return {"recording": True, "song": current_song}

@app.post("/session/stop")
def session_stop():
    global recording_flag
    recording_flag = False
    return {"status": "recording stopped"}

@app.get("/session/status")
def session_status():
    return {"recording": recording_flag, "song": current_song, "session_active": session_active, "total_songs": total_songs}

@app.post("/session/next")
def session_next():
    global current_song, recording_flag
    current_song += 1
    recording_flag = False
    return {"song": current_song, "recording": recording_flag}

@app.get("/")
def root():
    return FileResponse(str(DIST_DIR / "index.html"))

@app.post("/session/end")
def session_end():
    global session_active, recording_flag
    session_active, recording_flag = False, False
    return {"status": "ended"}

final_session_result = {}
@app.post("/session/final_result")
def save_final_result(data: dict):
    global final_session_result
    final_session_result = data
    return {"status": "ok"}

@app.get("/session/final_result")
def get_final_result():
    return final_session_result

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    api_prefixes = ["/kiosk/", "/songs/", "/library/", "/led/", "/session/", "/result", "/qr", "/reserve"]
    if any(full_path.startswith(prefix.strip("/")) for prefix in api_prefixes):
        return {"status": "error", "message": "API endpoint not found"}
    return FileResponse(str(DIST_DIR / "index.html"))

# main.py 하단에 추가
@app.on_event("startup")
async def print_routes():
    print("--- [현재 등록된 모든 경로] ---")
    for route in app.routes:
        if hasattr(route, "methods"):
            print(f"Path: {route.path}, Methods: {route.methods}")