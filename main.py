from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models
from database import engine, get_db
from routers import booth, users, songs, library, kiosk, mr  # kiosk 포함
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse 
from fastapi.routing import APIRoute
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
# 프론트엔드 React(Vite) 빌드본 정적 에셋 연동
# ===============================
# 실제 빌드 경로인 kiosk/src1/dist/assets를 연결
DIST_DIR = "kiosk/src1/dist"
ASSETS_DIR = os.path.join(DIST_DIR, "assets")

if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


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
# 프론트엔드 SPA 라우팅 및 겹침 방지 설정
# ===============================

# 기존에 등록된 모든 API 및 시스템 경로 목록을 자동으로 추출하여 가로채기를 방어
API_ROUTES = set()
for route in app.routes:
    if isinstance(route, APIRoute):
        # /users/login -> 첫 번째 단어인 'users'를 추출
        root_path = route.path.strip("/").split("/")[0]
        if root_path:
            API_ROUTES.add(root_path)

# 추가로 방어해야 할 정적 파일 경로 및 문서 주소 수동 등록
API_ROUTES.update(["docs", "redoc", "openapi.json", "mr_files", "assets"])

@app.get("/{catchall:path}")
def read_index(catchall: str):
    # 1. 요청 경로가 백엔드 API 경로로 시작하면, 가로채지 않고 원래 API 라우터로 넘김
    first_segment = catchall.strip("/").split("/")[0]
    if first_segment in API_ROUTES:
        # 이 조건문이 참이 되면 아래의 파일 리턴을 무시하고, FastAPI 내부에서 알아서 원래 API 주소로 매칭
        from fastapi.exceptions import HTTPException
        raise HTTPException(status_code=404, detail="API Not Found")
    
    # 2. API 경로가 아니고 일반 화면 이동 요청인 경우 React의 index.html을 뿌려줌
    index_path = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # 3. 만약 빌드 파일이 없는 경우 임시 안내 메시지 출력
    return {"message": "SingPick 서버가 구동 중이나 프론트엔드 빌드 파일(dist)을 찾을 수 없습니다."}