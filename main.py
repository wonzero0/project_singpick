from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
import models
from database import engine, get_db
from routers import booth, users, songs, library, kiosk, mr 
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse 
from fastapi.routing import APIRoute
import sys
import os
from fastapi.responses import HTMLResponse
from urllib.parse import quote
from fastapi import APIRouter
sys.path.append(os.path.join(os.path.dirname(__file__), "ai_module"))
try:
    from Lighting.inside.led_controller import start_led as start_led_arduino, stop_led as stop_led_arduino
except Exception as e:
    print("[WARN] Arduino disabled:", e)

    def start_led_arduino():
        pass

    def stop_led_arduino():
        pass
import subprocess

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = Path(__file__).resolve().parent / "kiosk" / "src1" / "dist"
ASSETS_DIR = DIST_DIR / "assets"

# ===============================
# DB 테이블 생성
# ===============================
models.Base.metadata.create_all(bind=engine)


def ensure_reservation_schema():
    inspector = inspect(engine)
    if "reservations" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("reservations")}
    with engine.begin() as conn:
        if "user_id" not in columns:
            conn.execute(text("ALTER TABLE reservations ADD COLUMN user_id VARCHAR(50) NULL"))
        else:
            conn.execute(text("ALTER TABLE reservations MODIFY COLUMN user_id VARCHAR(50) NULL"))

        if "booth_id" not in columns:
            conn.execute(text("ALTER TABLE reservations ADD COLUMN booth_id INT DEFAULT 1"))
        else:
            conn.execute(text("ALTER TABLE reservations MODIFY COLUMN booth_id INT DEFAULT 1"))

        if "song_id" not in columns:
            conn.execute(text("ALTER TABLE reservations ADD COLUMN song_id INT"))
        else:
            conn.execute(text("ALTER TABLE reservations MODIFY COLUMN song_id INT"))


ensure_reservation_schema()

# ===============================
# FastAPI 앱 생성
# ===============================
app = FastAPI(title="SingPick Server")

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


@app.post("/led/play")
def play_led():
    start_led_arduino()
    return {"status":"success"}

@app.post("/led/stop")
def stop_led_endpoint():
    stop_led_arduino()
    return {"status":"success"}


# ===============================
# 프론트엔드 React(Vite) 빌드본 정적 에셋 연동
# ===============================
# 실제 빌드 경로인 kiosk/src1/dist/assets를 연결



if ASSETS_DIR.exists() and ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")



# ===============================
# 임시 노래 데이터 초기화 (10곡)
# ===============================
def init_dummy_songs(db: Session):
    if db.query(models.Song).count() == 0:
        dummy_songs = [
            # 고정 요청곡 (3곡)
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
# 프론트엔드 SPA 라우팅 및 겹침 방지 설정
# ===============================



@app.get("/qr", response_class=HTMLResponse)
def show_qr_page(request: Request):
    # (컴퓨터 터미널에 ipconfig를 치면 나오는 IPv4 주소입니다.)
    
    target_url = str(request.base_url)
    qr_data = quote(target_url, safe="")
    
    # 오픈소스 QR 코드 API를 이용해 화면에 QR을 이쁘게 띄워주는 HTML
    html_content = f"""
    <html>
        <head>
            <title>SingPick QR Code Portal</title>
            <style>
                body {{ font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background-color: #f7f9fa; margin: 0; }}
                .card {{ background: white; padding: 40px; border-radius: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); text-align: center; }}
                img {{ width: 250px; height: 250px; margin: 20px 0; border: 4px solid #2F7C31; border-radius: 12px; }}
                h1 {{ color: #111; font-size: 22px; margin-bottom: 5px; }}
                p {{ color: #666; font-size: 14px; margin-bottom: 25px; }}
                .url-box {{ background: #eee; padding: 10px 15px; border-radius: 8px; font-family: monospace; font-size: 14px; color: #333; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🎤 SingPick 모바일 연결 큐알</h1>
                <p>스마트폰 카메라로 아래 QR 코드를 스캔하세요!<br>(주의: 컴퓨터와 휴대폰이 같은 와이파이에 연결되어 있어야 합니다)</p>
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={qr_data}" alt="QR Code">
                <div class="url-box">{target_url}</div>
            </div>
        </body>
    </html>
    """
    return html_content



# ===============================
# 결과 저장 DB
# ===============================
results_db = {}


@app.post("/result")
def save_result(data: dict):
    user_id = data.get("user_id", "unknown")

    if user_id not in results_db:
        results_db[user_id] = []

    results_db[user_id].append(data)

    return {"status": "saved"}


@app.get("/result")
def get_result(user_id: str):
    return results_db.get(user_id, [])


# ===============================
# 세션 상태 변수 (중앙관리)
# ===============================
recording_flag = False
stop_flag = False
process = None
current_song = 0
finished_flag = False
session_active = True

# ===============================
# 세션 시작
# ===============================
@app.post("/session/start")
def session_start():

    global recording_flag
    global current_song
    global process
    global finished_flag
    global session_active

    recording_flag = True
    current_song = 1
    finished_flag = False
    session_active = True

    print("🎤 세션 시작")
    print(f"song={current_song}")

    process = subprocess.Popen([
        "python",
        "-m",
        "ai_module.karaoke_main"
    ])

    return {
        "recording": True,
        "song": 1
    }


# ===============================
# 세션 종료
# ===============================
@app.post("/session/stop")
def session_stop():
    global recording_flag

    recording_flag = False

    print("🛑 녹음 종료")

    return {"status": "recording stopped"}


# ===============================
# 상태 확인
# ===============================
@app.get("/session/status")
def session_status():
    return {
        "recording": recording_flag,
        "song": current_song,
        "finished": finished_flag,
        "session_active": session_active
    }


# ===============================
# 다음 곡 / 녹음 중지 트리거
# ===============================
@app.post("/session/next")
def session_next():
    global current_song, recording_flag

    current_song += 1
    recording_flag = True

    print(
        f"🎤 다음곡 시작 "
        f"(song={current_song})"
    )

    return {
        "recording": recording_flag,
        "song": current_song
    }

if ASSETS_DIR.exists() and ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

from fastapi.responses import FileResponse

@app.get("/")
def root():
    return FileResponse(str(DIST_DIR / "index.html"))

@app.post("/session/finish")
def session_finish():

    global finished_flag
    global recording_flag

    finished_flag = True
    recording_flag = False

    print("🏁 전체 세션 종료")

    return {"status": "finished"}

@app.post("/session/end")
def session_end():
    global session_active, finished_flag, recording_flag

    session_active = False
    finished_flag = True
    recording_flag = False

    print("🏁 전체 세션 종료 (FINAL SIGNAL)")

    return {"status": "ended"}

final_session_result = {}

@app.post("/session/final_result")
def save_final_result(data: dict):
    global final_session_result
    final_session_result = data
    print("🏆 FINAL RESULT STORED:", data)
    return {"status": "ok"}


@app.get("/session/final_result")
def get_final_result():
    return final_session_result
