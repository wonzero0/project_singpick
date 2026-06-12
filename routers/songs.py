from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from database import get_db
import models
import shutil, time
import os
from core import ai_engine
from models import Reservation 
from state import current_kiosk_state
from schemas import RequestReserve
from ai_module.analyze_voice_final import analyzeVoice
from ai_module.db_operations import save_analysis_result_to_db

router = APIRouter(prefix="/songs", tags=["Songs"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".mp4", ".m4a", ".flac"}


# ============================================
# DB에 예약을 생성해 주는 라우터
# ============================================
@router.post("/reserve")
def reserve_song_endpoint(request: RequestReserve, db: Session = Depends(get_db)):
    """
    프론트엔드에서 곡을 고르고 예약할 때 호출하는 API (songs 라우터)
    """
    print(f"[DEBUG /songs/reserve] 예약 요청 수신: booth_id={request.booth_id}, song_id={request.song_id}, user_id={request.user_id}")
    try:
        # 2. 파라미터로 받은 'request' 객체에서 booth_id와 song_id를 꺼냅니다.
        booth_id = request.booth_id
        song_id = request.song_id
        
        # kiosk 상태에 맞게 회원 정보 매핑 (request.user_id는 무시되고 kiosk 상태의 user_id 사용)
        current_user = current_kiosk_state.get("user_id", "GUEST")
        if not current_user or current_user == "-":
            current_user = "GUEST"

        # DB 모델 생성
        new_reservation = models.Reservation(
            booth_id=booth_id,
            song_id=song_id,
            user_id=current_user,
            status="waiting"
        )
        
        db.add(new_reservation)
        print(f"[DEBUG /songs/reserve] DB에 예약 객체 추가 시도: {new_reservation}")
        db.commit()
        db.refresh(new_reservation)
        
        print(f"[DEBUG /songs/reserve] 예약 생성 성공 -> 복합키: {new_reservation.booth_id}:{new_reservation.song_id}:{new_reservation.user_id}, User: {current_user}")
        
        # 3. 반환값: 복합 기본키를 반환합니다.
        return {
            "status": "success", 
            "reservation_key": f"{new_reservation.booth_id}:{new_reservation.song_id}:{new_reservation.user_id}", # 복합 기본키 반환
            "user_id": current_user
        }
    except IntegrityError as e:
        db.rollback()
        print(f"[ERROR /songs/reserve] 데이터베이스 무결성 오류 발생: {e}")
        raise HTTPException(status_code=409, detail=f"예약 중복 또는 제약 조건 위반: {e}")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[ERROR /songs/reserve] 예약 처리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"예약 처리 중 오류 발생: {e}")

# ============================================
# 노래 업로드 + AI 분석 (통합 누적 히스토리 보존 버전)
# ============================================
@router.post("/upload")
async def upload_song(
    file: UploadFile = File(...),
    reservation_id: str = Form(...),  # 형식: "booth:song:user"
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    # user_id 전처리 (공백 등 제거)
    user_id = user_id.strip() if user_id else "GUEST"

    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일 없음")

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="지원하지 않는 파일")

        file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. 오디오 물리 분석 데이터 추출
        result = analyzeVoice(file_path)

        # 안전한 데이터 매핑: AI 분석 결과에서 수치 추출 시 방어적 형변환 및 기본값 할당
        analysis_values = result.get("analysis_values", {})
        cur_pitch = float(analysis_values.get("pitch_hz_avg", 0.0))
        cur_tempo = float(analysis_values.get("tempo_bpm", 0.0))
        cur_volume = float(analysis_values.get("volume_rms_avg", 0.0))

        feedback = result.get("feedback", "분석 완료")
        recommendations = result.get("recommendations", [])
        similar_songs = result.get("similar_songs", [])
        similar_artists = result.get("similar_artists", [])

        # 2. 분석 결과 저장 및 AI 피드백 생성
        # database.py의 설정을 공유하는 주입된 DB 세션(db)을 사용하여 test_db.py와 동일한 환경을 보장합니다.
        try:
            new_analysis, score, gemini_feedback, pitch_score_input, tempo_score_input, volume_score_input = save_analysis_result_to_db(
                db=db,
                user_id=user_id,
                filename=file.filename,
                file_path=file_path,
                analysis_values=analysis_values,
                recommendations=recommendations,
                similar_artists=similar_artists
            )

            if not new_analysis:
                raise ValueError("AnalysisResult 객체가 생성되지 않았습니다.")

            # 분석 데이터 명시적 커밋: 이후 로직에서 에러가 나더라도 분석 데이터 자체는 DB에 안전하게 보존되도록 트랜잭션 분리
            print(f"[DEBUG] 최종 DB 저장 성공: ID={new_analysis.id}")

        except Exception as e:
            db.rollback()
            print(f"[ERROR /upload] DB 저장 중 치명적 오류 발생 및 롤백 수행: {str(e)}")
            raise HTTPException(status_code=500, detail="분석 결과 데이터베이스 저장 실패")

        # 4. reservation_id 형식 파싱 및 상태 완료 업데이트
        print(f"[DEBUG /upload] reservation_id={reservation_id}, user_id={user_id}")
        
        try:
            if ":" in reservation_id:
                booth_id, song_id, res_user = reservation_id.split(":")
                booth_id = int(booth_id)
                song_id = int(song_id)
                
                reservation = db.query(models.Reservation).filter(
                    models.Reservation.booth_id == booth_id,
                    models.Reservation.song_id == song_id,
                    models.Reservation.user_id == res_user,
                    models.Reservation.status != "completed"
                ).first()

                if reservation:
                    reservation.status = "completed"
                    db.commit() # 예약 상태 변경 반영
                    print(f"[DEBUG /upload] Reservation status 업데이트 완료: completed")
            else:
                print(f"[WARN /upload] reservation_id 형식이 복합키가 아닙니다: {reservation_id}. 예약을 'completed'로 업데이트하지 않고 건너뜁니다.")
        except Exception as e:
            print(f"[DEBUG /upload] reservation 처리 중 예외 발생: {e}")

        # 5. 누적 히스토리 및 평균 계산 (실제 유저 환경용 예외 차단 적용)
        try:
            all_histories = db.query(models.AnalysisResult).filter(
                models.AnalysisResult.user_id == user_id
            ).all()

            # 방어적 히스토리 계산: 첫 방문자이거나 데이터가 없을 경우 현재 곡의 데이터로 대체
            if len(all_histories) > 0:
                avg_score = sum(h.score for h in all_histories) / len(all_histories)
                avg_pitch = sum(h.pitch_hz_avg for h in all_histories) / len(all_histories)
                avg_tempo = sum(h.tempo_bpm for h in all_histories) / len(all_histories)
                avg_volume = sum(h.volume_rms_avg for h in all_histories) / len(all_histories)
            else:
                avg_score = score
                avg_pitch = cur_pitch
                avg_tempo = cur_tempo
                avg_volume = cur_volume

            overall_feedback = ""
            if avg_score >= 90:
                overall_feedback += "전체적으로 매우 안정적인 가창 능력을 유지하고 있습니다. "
            elif avg_score >= 75:
                overall_feedback += "방문할수록 노래 실력이 점차 향상되고 있습니다. "
            else:
                overall_feedback += "음정과 박자 안정성 연습이 더 필요합니다. "

            if avg_pitch >= 320:
                overall_feedback += "고음 영역에서 강점을 보입니다."
            elif avg_pitch >= 250:
                overall_feedback += "중음 영역이 안정적입니다."
            else:
                overall_feedback += "저음 중심의 음역대를 가지고 있습니다."

            top_song = similar_songs[0] if similar_songs else "좋은 날"
            top_singer = similar_artists[0] if similar_artists else "아이유"
        except Exception as e:
            print(f"[DEBUG /upload] 히스토리 및 피드백 계산 중 예외 발생: {e}")
            all_histories = []
            avg_score, avg_pitch, avg_tempo, avg_volume = score, cur_pitch, cur_tempo, cur_volume
            overall_feedback = "현재 가창 데이터를 분석 중입니다."
            top_song = similar_songs[0] if similar_songs else "정보 없음"
            top_singer = similar_artists[0] if similar_artists else "정보 없음"

        # 6. Web.tsx 맞춤형 데이터 반환
        return {
            "status": "success",
            "message": f"{user_id} 분석 완료",
            "data": {
                "feedback": gemini_feedback, 
                "pitch_score": pitch_score_input,
                "tempo_score": tempo_score_input,
                "volume_score": volume_score_input,
                "top_song": top_song,
                "top_singer": top_singer,
                "scores": {"total_score": score},
                "analysis_values": analysis_values,
                "overall_feedback": overall_feedback,
                "overall_analysis": {
                    "history_count": len(all_histories),
                    "avg_score": round(avg_score, 1),
                    "avg_pitch": round(avg_pitch, 1),
                    "avg_tempo": round(avg_tempo, 1),
                    "avg_volume": round(avg_volume, 4)
                },
                "recommendations": recommendations,
                "similar_songs": similar_songs,
                "similar_artists": similar_artists
            }
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 사용자 과거 기록 조회
# ============================================
@router.get("/history/{user_id}")
def get_user_history(user_id: str, db: Session = Depends(get_db)):
    histories = db.query(models.AnalysisResult).filter(
        models.AnalysisResult.user_id == user_id
    ).order_by(models.AnalysisResult.created_at.desc()).all()

    result = []
    for h in histories:
        result.append({
            "id": h.id,
            "date": h.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "filename": h.filename,
            "score": h.score,
            "feedback": h.feedback,
            "pitch_hz_avg": h.pitch_hz_avg,
            "tempo_bpm": h.tempo_bpm,
            "volume_rms_avg": h.volume_rms_avg
        })

    return {
        "status": "success",
        "count": len(result),
        "data": result
    }