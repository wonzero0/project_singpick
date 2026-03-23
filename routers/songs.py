from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
import models
import shutil
import os
from ai_module.analyze_voice_final import analyzeVoice
import json

router = APIRouter(prefix="/songs", tags=["🎵 Songs (노래/AI 연동)"])

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
            raise HTTPException(status_code=400, detail="업로드된 파일명이 없습니다.")

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식: {ext}")

        filename = file.filename
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = analyzeVoice(wav_path=file_path)

        if not isinstance(result, dict):
            raise HTTPException(status_code=500, detail="AI 분석 결과 형식이 올바르지 않습니다.")

        scores = result.get("scores", {})
        analysis_values = result.get("analysis_values", {})
        ai_feedback = result.get("feedback", "분석 완료")
        recommendations = result.get("recommendations", [])
        similar_songs = result.get("similar_songs", [])
        similar_artists = result.get("similar_artists", [])

        final_feedback_text = ai_feedback
        if isinstance(final_feedback_text, list):
            final_feedback_text = json.dumps(final_feedback_text, ensure_ascii=False)

        # DB 저장 (자동 점수 기록)
        new_analysis = models.AnalysisResult(
            user_id=user_id,
            filename=filename,
            pitch_score=scores.get("pitch", 0.0),
            tempo_score=scores.get("tempo", 0.0),
            volume_score=scores.get("volume", 0.0),
            pitch_hz_avg=analysis_values.get("pitch_hz_avg", 0.0),
            tempo_bpm=analysis_values.get("tempo_bpm", 0.0),
            volume_rms_avg=analysis_values.get("volume_rms_avg", 0.0),
            feedback=final_feedback_text,
            feature_path=file_path
        )
        db.add(new_analysis)

        reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
        if reservation:
            reservation.status = "completed"

        db.commit()
        db.refresh(new_analysis)

        return {
            "status": "success",
            "message": f"{user_id}님의 분석 및 예약 완료",
            "data": {
                "scores": scores,
                "analysis_values": analysis_values,
                "feedback": ai_feedback,
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
        raise HTTPException(status_code=500, detail=f"서버 내부 오류: {str(e)}")