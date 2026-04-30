from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
import models
import shutil
import os

from ai_module.analyze_voice_final import analyzeVoice
from ai_module.karaoke_scoring import calculate_score

router = APIRouter(prefix="/songs", tags=["Songs"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".mp4", ".m4a", ".flac"}


@router.post("/upload")
async def upload_song(
    file: UploadFile = File(...),
    reservation_id: int = Form(...),
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

        # =========================
        # AI 분석
        # =========================
        result = analyzeVoice(file_path)

        analysis_values = result.get("analysis_values", {})
        feedback = result.get("feedback", "분석 완료")
        recommendations = result.get("recommendations", [])
        similar_songs = result.get("similar_songs", [])
        similar_artists = result.get("similar_artists", [])

        # =========================
        # 최종 점수
        # =========================
        score = calculate_score(analysis_values)

        # =========================
        # DB 저장 (🔥 수정 완료)
        # =========================
        new_analysis = models.AnalysisResult(
            user_id=user_id,
            filename=file.filename,

            score=score,   # ✅ 여기만 존재해야 정상

            pitch_hz_avg=analysis_values.get("pitch_hz_avg", 0.0),
            tempo_bpm=analysis_values.get("tempo_bpm", 0.0),
            volume_rms_avg=analysis_values.get("volume_rms_avg", 0.0),

            feedback=feedback,
            feature_path=file_path
        )

        db.add(new_analysis)

        reservation = db.query(models.Reservation).filter(
            models.Reservation.id == reservation_id
        ).first()

        if reservation:
            reservation.status = "completed"

        db.commit()
        db.refresh(new_analysis)

        return {
            "status": "success",
            "message": f"{user_id} 분석 완료",
            "data": {
                "scores": {
                    "total_score": score
                },
                "analysis_values": analysis_values,
                "feedback": feedback,
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