import traceback
from fastapi import FastAPI, Depends
from fastapi import Request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import models
from database import engine, get_db
from routers import booth, users, songs, library, kiosk  # kiosk 포함
from fastapi.staticfiles import StaticFiles
from routers import mr
from core.ai_engine import get_vocal_feedback, recommend_songs
from core.security import cipher
from core.ai_engine import analyze_error
from routers import users, songs
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버가 켜질 때 실행할 내용 
    print("서버가 시작되었습니다. (Startup Event)")
    yield
    print("서버가 종료되었습니다. (Shutdown Event)")

# ===============================
# DB 테이블 생성
# ===============================
models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="🎤 SING-PICK: AI 기반 퍼스널 노래 추천 노래방 관제 시스템",
    description="""
    AI 및 정보보안 기술이 결합된 노래방 백엔드 서버입니다.
    
    **주요 기능**: 실시간 가창 분석, JWT 기반 보안 인증, AI 보컬 피드백 및 추천 등
    **기술 스택**: FastAPI, MySQL, Google Gemini AI, JWT 등
    """,
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(mr.router, prefix="/youtube", tags=["YouTube API"])
# ===============================
# FastAPI 앱 생성
# ===============================
app = FastAPI(title="SingPick Server")

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
app.include_router(kiosk.router)


def init_dummy_songs(db: Session):
    if db.query(models.Song).count() == 0:
        dummy_songs = [
            models.Song(title="0+0", singer="한로로", tj_number=99991),
            models.Song(title="한숨", singer="이하이", tj_number=99992),
            models.Song(title="여름밤에 우리", singer="전진희(feat. wave to earth)", tj_number=99993),
            models.Song(title="좋은 날", singer="아이유", tj_number=1001),
            models.Song(title="너랑 나", singer="아이유", tj_number=1002),
            models.Song(title="밤편지", singer="아이유", tj_number=1003),
            models.Song(title="보고 싶다", singer="김범수", tj_number=2001),
            models.Song(title="응급실", singer="izi", tj_number=3001),
            models.Song(title="소주 한 잔", singer="임창정", tj_number=4001),
            models.Song(title="Hype Boy", singer="NewJeans", tj_number=5001),
        ]
        db.add_all(dummy_songs)
        db.commit()
        print("🎵 [System] 가짜 노래 10곡이 DB에 저장되었습니다!")


# ===============================
# 루트 경로
# ===============================
@app.get("/")
def read_root():
    return {"message": "SingPick Server is Running!"}

@app.get("/api/v1/result/{analysis_id}")
async def get_singing_analysis(analysis_id: int, db: Session = Depends(get_db)):
    # 1. DB에서 서현이가 저장한 분석 데이터 가져오기 (models.AnalysisResult 등)
    result_data = db.query(models.AnalysisResult).filter(models.AnalysisResult.id == analysis_id).first()
    
    if not result_data:
        return {"error": "분석 데이터를 찾을 수 없습니다."}

    # 2. 보안: 만약 점수가 암호화되어 저장된다면 복호화 진행 (원영님 담당!)
    # 예: pitch = cipher.decrypt(result_data.pitch_score)
    pitch = result_data.pitch_score
    tempo = result_data.tempo_score
    volume = result_data.avg_volume

    # 3. AI 엔진 호출 (우리가 만든 '냉정한 트레이너' 프롬프트가 작동함)
    ai_feedback = get_vocal_feedback(pitch, tempo, volume)

    # 4. (선택사항) AI 피드백을 DB에 다시 저장해서 나중에 또 안 불러오게 하기
    result_data.feedback = ai_feedback
    db.commit()

    return {
        "score": {"pitch": pitch, "tempo": tempo, "volume": volume},
        "ai_feedback": ai_feedback
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 1. 시스템에서 발생한 날것의 에러 로그를 문자열로 추출
    error_log = traceback.format_exc()
    
    # 2. 터미널에 시각적으로 눈에 띄게 경고창 띄우기
    print("\n" + "!"*60)
    print("🚨 [긴급] 서버 내부 에러(500) 감지!")
    print("🤖 제미나이 시니어 엔지니어가 원인을 분석 중입니다...")
    print("!"*60)
    
    # 3. AI 엔진에 에러 로그 넘겨서 해결책 받아오기
    ai_solution = analyze_error(error_log)
    
    # 4. 터미널에 AI 분석 결과 예쁘게 출력
    print("\n🛠️ [AI 시니어 엔지니어의 분석 리포트]")
    print(ai_solution)
    print("="*60 + "\n")
    
    # 5. 프론트엔드(예원님) 화면이 뻗지 않도록 얌전한 JSON 응답 보내기
    return JSONResponse(
        status_code=500,
        content={
            "status": "fail", 
            "message": "서버 내부 오류가 발생했습니다. 백엔드 관리자가 터미널의 AI 분석을 확인 중입니다."
        }
    )