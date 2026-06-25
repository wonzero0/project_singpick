import json
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
from database import engine, get_db, SessionLocal
from core.ai_engine import get_vocal_feedback
from routers import booth, users, songs, library, kiosk, mr
from schemas import RequestReserve
from sklearn.decomposition import PCA
import numpy as np
from ai_module.visualization import get_visualization_data

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
session_user_id = "GUEST"  # [요구사항 1] 실시간 유저 세션 트래킹 글로벌 변수 유지

@app.post("/result")
def save_result(data: dict, db: Session = Depends(get_db)):
    global session_user_id
    
    # 1. 유저 ID 식별 (전달 데이터 -> 글로벌 세션 변수 -> 최신 예약자 검색 -> 최후의 보루 GUEST)
    user_id = data.get("user_id", "unknown")
    if user_id in ["unknown", "-", "", "GUEST"]:
        if session_user_id and session_user_id not in ["unknown", "GUEST", "-", ""]:
            user_id = session_user_id
        else:
            last_res = db.query(models.Reservation).order_by(models.Reservation.created_at.desc()).first()
            if last_res and last_res.user_id:
                user_id = last_res.user_id
            else:
                user_id = "GUEST" # 비회원 상태여도 GUEST 키로 저장 진행

    # 2. AI 피드백 파싱 및 스코어 매핑
    # (두 번째 코드 블록의 피드백 연산 로직과 매핑 구문을 안정적으로 유지)
    pitch = float(data.get("pitch", 0))
    tempo = float(data.get("tempo", 0))
    volume = float(data.get("volume", 0))

    p_score = min(int(pitch / 4), 100) if pitch > 0 else 85
    t_score = min(int(tempo), 100) if tempo > 0 else 80
    v_score = min(int(volume * 100), 100) if volume > 0 else 75

    # 3. 제미나이 AI 피드백 생성 예외 방어
    try:
        gemini_feedback = get_vocal_feedback(p_score, t_score, v_score, pitch, tempo, volume)
    except Exception as gemini_err:
        print(f"[WARN] 제미나이 AI 트래픽 초과(503) 에러 우회 처리: {gemini_err}")
        gemini_feedback = "현재 AI 서버 사용량이 많아 상세 피드백을 생성할 수 없습니다. 잠시 후 다시 시도해 주세요."
    data["gemini_feedback"] = gemini_feedback 
    
    # 3. 데이터베이스(MySQL) analysis_results 테이블 저장
    analysis_id = None
    try:
        new_analysis = models.AnalysisResult(
            user_id=user_id,
            score=data.get("score"),
            pitch_hz_avg=pitch,
            tempo_bpm=tempo,
            volume_rms_avg=volume,
            feedback=gemini_feedback
        )
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
        analysis_id = new_analysis.id
    except Exception as e:
        db.rollback()
        print(f"[Error] analysis_results 저장 실패: {e}")

    # 4. 3차원 임베딩 좌표 무조건 적재 (GUEST 차단 해제)
    emb_x = data.get("x") or data.get("pitch_x")
    emb_y = data.get("y") or data.get("tempo_y")
    emb_z = data.get("z") or data.get("volume_z")

    if emb_x is not None and emb_y is not None:
        try:
            new_embedding = models.SongEmbedding(
                user_id=user_id,
                analysis_result_id=analysis_id,
                x=float(emb_x),
                y=float(emb_y),
                z=float(emb_z) if emb_z is not None else 0.0
            )
            db.add(new_embedding)
            db.commit()
            print(f"✅ [임베딩 적재 성공] User: {user_id} -> ({emb_x}, {emb_y})")
        except Exception as emb_ex:
            db.rollback()
            print(f"[WARN] 임베딩 적재 오류: {emb_ex}")

    # 5. 추천 데이터 적재 유연화 (파트너 서현님 데이터 규격 자동 탐색 알고리즘)
    raw_songs, raw_artists = [], []

    # [알고리즘] 전송받은 data 딕셔너리 내부를 샅샅이 뒤져 리스트 형태의 추천 데이터를 자동 추출합니다.
    for k, v in data.items():
        if isinstance(v, list) and v:
            k_low = k.lower()
            # 추천 곡/목록 관련 키워드가 포함된 리스트 탐지 (더미가 아닌 서현님의 실데이터 우선)
            if any(kw in k_low for kw in ["song", "recommend", "similar", "top", "list"]) and not raw_songs:
                raw_songs = v
            # 추천 가수/아티스트 관련 키워드가 포함된 리스트 탐지
            if any(kw in k_low for kw in ["artist", "singer"]) and not raw_artists:
                raw_artists = v

    # 서현님의 실데이터가 탐지되지 않았을 경우에만 DB 조회 및 안전 백업 더미를 생성합니다.
    if not raw_songs:
        try:
            song_pool = db.query(models.Song).limit(5).all()
            raw_songs = [{"title": s.title, "artist": s.singer, "match": round(98.5 - (i * 2.1), 1)} for i, s in enumerate(song_pool)]
        except Exception:
            raw_songs = [{"title": "Maybe_if", "artist": "비비", "match": 96.2}, {"title": "0+0", "artist": "한로로", "match": 94.0}, {"title": "한숨", "artist": "이하이", "match": 91.5}]

    try:
        processed_songs = []
        seen_artists = set()
        processed_artists = []

        # 1) 곡 리스트 처리
        for idx, item in enumerate(raw_songs):
            if isinstance(item, str): # 문자열로 올 경우 대응
                title, artist, match_val = item, "알 수 없음", round(95.0 - (idx * 3.5), 1)
            else:
                title = item.get("title") or item.get("song") or "추천 곡"
                artist = item.get("artist") or "알 수 없음"
                match_val = item.get("match") or item.get("score") or item.get("similarity") or round(95.0 - (idx * 3.5), 1)

            processed_songs.append({"title": title, "artist": artist, "match": float(match_val)})
            if artist != "알 수 없음": seen_artists.add(artist)

        # 2) 가수 리스트 처리 (서현님이 별도 필드로 줬다면 우선 사용, 없으면 곡 정보에서 추출)
        if raw_artists:
            for idx, a in enumerate(raw_artists):
                if isinstance(a, str):
                    a_name, a_match = a, round(96.0 - (idx * 4.0), 1)
                else:
                    a_name = a.get("name") or a.get("artist") or "알 수 없음"
                    a_match = a.get("match") or a.get("score") or round(96.0 - (idx * 4.0), 1)
                processed_artists.append({"name": a_name, "match": float(a_match)})
        else:
            # 곡 정보에서 유니크 가수를 순차적으로 추출
            temp_seen = set()
            for s in processed_songs:
                if s["artist"] not in temp_seen and s["artist"] != "알 수 없음":
                    temp_seen.add(s["artist"])
                    processed_artists.append({"name": s["artist"], "match": round(96.0 - (len(processed_artists) * 4.0), 1)})

        while len(processed_songs) < 5:
            processed_songs.append({"title": "추천 대기 곡", "artist": "SingPick AI", "match": 80.0})
        while len(processed_artists) < 5:
            processed_artists.append({"name": "추천 대기 가수", "match": 85.0})

        final_songs = processed_songs[:5]
        final_artists = processed_artists[:5]

        # UPSERT 진행
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO user_recommendations (user_id, recommended_songs, recommended_artists, updated_at)
                VALUES (:user_id, :songs, :artists, CURRENT_TIMESTAMP);
            """), {"user_id": user_id, "songs": json.dumps(final_songs, ensure_ascii=False), "artists": json.dumps(final_artists, ensure_ascii=False)})
        
        data["recommended_songs"] = final_songs
        data["recommended_artists"] = final_artists
        print(f"✅ [추천리스트 적재 성공] User: {user_id}")
    except Exception as ex:
        print(f"[WARN] 추천 파싱 오류: {ex}")

    if user_id not in results_db: 
        results_db[user_id] = []
    
    results_db[user_id].append(data)
    return {"status": "saved", "user_id": user_id}


@app.get("/result")
def get_result(user_id: str):
    # 1. 실시간 메모리 확인 및 반환 구조 최적화
    res_list = results_db.get(user_id, [])
    if res_list:
        return res_list

    # 2. MySQL DB 백업 레이어 로드 및 Web.tsx 스키마 동기화 리턴
    try:
        with engine.begin() as conn:
            row = conn.execute(text("""
                SELECT recommended_songs, recommended_artists 
                FROM user_recommendations 
                WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchone()
        
        if row:
            songs_data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            artists_data = json.loads(row[1]) if isinstance(row[1], str) else row[1]
            
            return [{
                "user_id": user_id,
                "recommended_songs": songs_data,
                "recommended_artists": artists_data,
                "gemini_feedback": "성공적으로 조회된 AI 추천 데이터 세트입니다."
            }]
    except Exception as e:
        print(f"[WARN] 추천 테이블 백업 데이터 라우팅 복원 실패: {e}")
        
    return []

# 🌟 [추가 - 방어 라우터] 서현님 하드웨어에서 임베딩 전용 단독 엔드포인트로 보낼 경우 매핑용 
@app.post("/embeddings")
def save_embeddings_isolated(data: dict, db: Session = Depends(get_db)):
    global session_user_id
    user_id = data.get("user_id", session_user_id)
    x = data.get("x")
    y = data.get("y")
    z = data.get("z", 0.0)
    
    if x is not None and y is not None:
        try:
            new_embedding = models.SongEmbedding(
                user_id=user_id,
                x=float(x),
                y=float(y),
                z=float(z)
            )
            db.add(new_embedding)
            db.commit()
            return {"status": "embedding successfully saved", "user_id": user_id}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=400, detail="Missing required parameters x or y")

recording_flag, stop_flag, process, current_song, session_active, total_songs = False, False, None, 0, True, 0

@app.post("/session/start")
def session_start(data: dict):
    global recording_flag, current_song, process, session_active, total_songs, session_user_id
    recording_flag, total_songs = True, data["total_songs"]
    if current_song == 0: current_song = 1
    session_active = True
    session_user_id = data.get("user_id", "GUEST") # [요구사항 1] 세션 시작 시 유저 정보 holdings

    # 1. 실제 사용자 ID 식별 (전달된 데이터가 없으면 최신 예약자 조회)
    user_id = data.get("user_id")
    if not user_id:
        db = SessionLocal()
        last_res = db.query(models.Reservation).order_by(models.Reservation.created_at.desc()).first()
        user_id = last_res.user_id if last_res else "GUEST"
        db.close()

    if process is None or process.poll() is not None:
        env = os.environ.copy()
        env["USER_ID"] = str(user_id)
        process = subprocess.Popen(["python", "-m", "ai_module.karaoke_main"], env=env)
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


# =====================================================================
# 🚨 [서현-원영 연동] 기존 원영이의 @app.get("/feedback/pca")를 이 코드로 교체
# =====================================================================
@app.get("/feedback/pca")
def get_pca(db: Session = Depends(get_db)):
    global session_user_id
    
    # 1. 현재 가창 중인 유저 식별 (글로벌 세션 변수 우선 조회)
    user_id = session_user_id
    if user_id in ["unknown", "GUEST", "-", ""]:
        # 세션 변수가 비어있다면, 최근 등록된 분석 결과에서 유저 ID 역추적
        last_analysis = db.query(models.AnalysisResult).order_by(models.AnalysisResult.id.desc()).first()
        if last_analysis:
            user_id = last_analysis.user_id

    # 유저 식별이 불가능하면 빈 배열 반환해서 프론트엔드 에러 방지
    if not user_id:
        return []

    try:
        # 2. 서현이가 라파에서 쏴서 DB에 적재된 3차원 임베딩 좌표 추출
        user_emb_record = db.query(models.SongEmbedding)\
                            .filter(models.SongEmbedding.user_id == user_id)\
                            .order_by(models.SongEmbedding.id.desc())\
                            .first()
        
        # 3. 마찬가지로 UPSERT 완료된 추천 가수 리스트(JSON 문자열) 로드
        recommend_record = db.query(models.UserRecommendation)\
                             .filter(models.UserRecommendation.user_id == user_id)\
                             .order_by(models.UserRecommendation.id.desc())\
                             .first()

        # 아직 데이터가 적재되는 중이라 없으면 튕기지 말고 빈 배열로 대기시키기
        if not user_emb_record or not recommend_record:
            print(f"[PCA] 유저 '{user_id}'의 연동 데이터가 아직 준비되지 않았습니다.")
            return []

        # 4. 서현이 시각화 모듈에 건네줄 형태로 가공
        # 원영이 DB 사정상 x, y, z 좌표로 쪼개져 있으므로 [x, y] 배열로 합쳐줍니다.
        user_embedding = [user_emb_record.x, user_emb_record.y]
        
        # MySQL에 텍스트로 저장된 추천 가수 JSON을 파이썬 리스트로 파싱
        recommended_artists = json.loads(recommend_record.recommended_artists)

        # 5. 🌟 서현이가 만든 정밀 시각화 매핑 함수 드디어 호출!
        # 프론트엔드가 요구하는 [{x, y, type: "ref" | "user"}] 데이터셋이 여기서 완성됩니다.
        chart_points = get_visualization_data(user_embedding, recommended_artists)
        
        return chart_points

    except Exception as e:
        print(f"[CRITICAL PCA ERROR] 서현 AI 모듈 시각화 연동 중 실패: {e}")
        return []

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    api_prefixes = ["/kiosk/", "/songs/", "/library/", "/led/", "/session/", "/result", "/qr", "/reserve", "/feedback/"]
    if any(full_path.startswith(prefix.strip("/")) for prefix in api_prefixes):
        return {"status": "error", "message": "API endpoint not found"}
    return FileResponse(str(DIST_DIR / "index.html"))