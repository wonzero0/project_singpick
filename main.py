import traceback
from fastapi import FastAPI, Depends
from fastapi import Request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import models
from database import engine, get_db, SessionLocal
from routers import booth, users, songs, library, kiosk  # kiosk 포함
from fastapi.staticfiles import StaticFiles
from routers import mr
from core.ai_engine import get_vocal_feedback, recommend_songs
from core.security import cipher
from core.ai_engine import analyze_error
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("서버가 시작되었습니다. (Startup Event)")
    db = SessionLocal()
    try:
        init_dummy_songs(db)
    finally:
        db.close()
    yield
    print("서버가 종료되었습니다. (Shutdown Event)")

# ===============================
# DB 테이블 생성
# ===============================
models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="🎤 SING-PICK: AI 기반 퍼스널 노래 추천 노래방 관제 시스템",
    description="""
    사용자 음색에 가장 잘 어울리는, 가장 잘 부를 수 있는 노래를 추천드리는 노래방 백엔드 서버입니다.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# ===============================
# 정적 파일 서비스 (폴더 문 열어주기 - 모두 한곳으로 모음!)
# ===============================
app.mount("/downloaded_mrs", StaticFiles(directory="downloaded_mrs"), name="downloaded_mrs")
app.mount("/kiosk_static", StaticFiles(directory="kiosk"), name="kiosk_static")

# ===============================
# CORS 설정
# ===============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (테스트용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# 라우터 등록
# ===============================
# app.include_router(mr.router, prefix="/youtube", tags=["YouTube API"])
app.include_router(users.router)
app.include_router(booth.router)
app.include_router(songs.router)
app.include_router(kiosk.router)
app.include_router(library.router)


def init_dummy_songs(db: Session):
    # 현재 노래가 몇 곡 있는지 확인
    song_count = db.query(models.Song).count()
    
    # 🚨 노래가 50곡이 안 되면? (예전 10곡만 있거나 꼬였을 때) -> 싹 청소하고 새로 넣기!
    if song_count < 50:
        print("🎵 [System] 기존 DB 데이터를 정리하고 50곡을 새로 세팅합니다...")
        
        # (중요) 에러 방지를 위해 예약된 내역 먼저 지우고, 노래를 지웁니다.
        db.query(models.Reservation).delete()
        db.query(models.Song).delete()
        db.commit()

        dummy_songs = [
            # --- 🌟 화면 켜지면 바로 보이는 상위 10곡 ---
            models.Song(title="0+0", singer="한로로", ky_number=81234),
            models.Song(title="한숨", singer="이하이", ky_number=49040),
            models.Song(title="여름밤에 우리", singer="전진희(feat. wave to earth)", ky_number=81235),
            models.Song(title="좋은 날", singer="아이유", ky_number=47250),
            models.Song(title="소주 한 잔", singer="임창정", ky_number=6279),
            models.Song(title="응급실", singer="izi", ky_number=64156),
            models.Song(title="가시", singer="버즈", ky_number=65005),
            models.Song(title="보고 싶다", singer="김범수", ky_number=6259),
            models.Song(title="Hype Boy", singer="NewJeans", ky_number=82222),
            models.Song(title="사건의 지평선", singer="윤하", ky_number=81111),
            
            # --- 🔍 검색으로 찾을 수 있는 40곡 (총 50곡) ---
            models.Song(title="Tears", singer="소찬휘", ky_number=6133),
            models.Song(title="체념", singer="빅마마", ky_number=63273),
            models.Song(title="사랑의 배터리", singer="홍진영", ky_number=46927),
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
            models.Song(title="ELEVEN", singer="IVE", ky_number=95555),
            models.Song(title="Antifragile", singer="LE SSERAFIM", ky_number=96666),
            models.Song(title="Super Shy", singer="NewJeans", ky_number=97777),
            models.Song(title="후라이의 꿈", singer="AKMU", ky_number=98888)
        ]
        db.add_all(dummy_songs)
        db.commit()
        print("🎵 [System] 기본 인기곡 50곡이 DB에 세팅되었습니다!")

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