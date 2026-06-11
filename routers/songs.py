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
from ai_module.karaoke_scoring import calculate_score

router = APIRouter(prefix="/songs", tags=["Songs"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".mp4", ".m4a", ".flac"}


# ============================================
# 🌟 신규 추가: 진짜 DB에 예약을 생성해 주는 라우터
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

        analysis_values = result.get("analysis_values", {})
        feedback = result.get("feedback", "분석 완료")
        recommendations = result.get("recommendations", [])
        similar_songs = result.get("similar_songs", [])
        similar_artists = result.get("similar_artists", [])

        # 2. 최종 점수 계산
        score = calculate_score(analysis_values)

        pitch_score_input = min(int(analysis_values.get("pitch_hz_avg", 0.0) / 4), 100) if analysis_values.get("pitch_hz_avg", 0.0) > 0 else 85
        tempo_score_input = min(int(analysis_values.get("tempo_bpm", 0.0)), 100) if analysis_values.get("tempo_bpm", 0.0) > 0 else 80
        volume_score_input = min(int(analysis_values.get("volume_rms_avg", 0.0) * 100), 100) if analysis_values.get("volume_rms_avg", 0.0) > 0 else 75

        # 3. 제미나이 AI 보컬 피드백 생성
        gemini_feedback = ai_engine.get_vocal_feedback(
            pitch_score=pitch_score_input,
            tempo_score=tempo_score_input,
            avg_volume=volume_score_input,
            pitch_hz_avg=analysis_values.get("pitch_hz_avg", 0.0), 
            tempo_bpm=analysis_values.get("tempo_bpm", 0.0),       
            volume_rms_avg=analysis_values.get("volume_rms_avg", 0.0) 
        )

        # 4. DB 저장
        new_analysis = models.AnalysisResult(
            user_id=user_id,
            filename=file.filename,
            score=score,
            pitch_hz_avg=analysis_values.get("pitch_hz_avg", 0.0),
            tempo_bpm=analysis_values.get("tempo_bpm", 0.0),
            volume_rms_avg=analysis_values.get("volume_rms_avg", 0.0),
            feedback=gemini_feedback, 
            feature_path=file_path
        )
        db.add(new_analysis)

        # reservation_id 형식 파싱 및 상태 완료 업데이트
        print(f"[DEBUG /upload] reservation_id={reservation_id}, user_id={user_id}")
        
        try:
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
                print(f"[DEBUG /upload] Reservation status 업데이트 완료: completed")
        except Exception as e:
            print(f"[DEBUG /upload] reservation 처리 중 예외 발생 (무시 가능): {e}")

        db.commit()
        db.refresh(new_analysis)

        # 5. 누적 히스토리 및 평균 계산구조 완벽 복구
        all_histories = db.query(models.AnalysisResult).filter(
            models.AnalysisResult.user_id == user_id
        ).all()

        if len(all_histories) == 0:
            raise HTTPException(status_code=500, detail="히스토리 조회 실패")

        avg_score = sum(h.score for h in all_histories) / len(all_histories)
        avg_pitch = sum(h.pitch_hz_avg for h in all_histories) / len(all_histories)
        avg_tempo = sum(h.tempo_bpm for h in all_histories) / len(all_histories)
        avg_volume = sum(h.volume_rms_avg for h in all_histories) / len(all_histories)

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