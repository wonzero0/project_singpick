from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional 
from database import get_db
import models
import shutil
import os
import json # 서현님 코드 추가분
from ai_module.analyze_voice_final import analyzeVoice
from core.ai_engine import get_vocal_feedback, recommend_songs
from core.auth import get_current_user_optional 
from pydantic import BaseModel

# Swagger 문서에 보여질 예시 데이터
class AnalysisResponse(BaseModel):
    status: str = "success"
    message: str = "분석 완료"
    data: dict = {
        "scores": {"pitch": 80, "tempo": 90, "volume": 70},
        "trend": {
            "labels": ["1회차", "2회차", "3회차", "오늘"],
            "datasets": {
                "pitch": [65, 70, 82, 80],
                "tempo": [80, 82, 88, 90],
                "volume": [70, 75, 75, 70]
            }
        },
        "feedback": "전체적으로 안정적입니다...",
        "recommendations": "아이유 - 밤편지를 추천합니다.",
        "similar_songs": [],
        "similar_artists": []
    }

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files") 
os.makedirs(UPLOAD_DIR, exist_ok=True) # 서현님 코드 추가분 (폴더 자동생성)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".mp4", ".m4a", ".flac"} # 서현님 코드 추가분

router = APIRouter(prefix="/songs", tags=["🎵 Songs (노래/AI 연동)"])


@router.post(
    "/upload", 
    summary="🎙️ 녹음 파일 업로드 (회원/비회원 공용)",
    response_model=AnalysisResponse,
    status_code=200
)
async def upload_song(
    file: UploadFile = File(...),
    reservation_id: int = Form(...),
    user_id: Optional[str] = Form(None), 
    current_user: Optional[str] = Depends(get_current_user_optional), 
    reference_song: str = Form("No_Doubt"),
    user_bpm: float = Form(120.0),
    db: Session = Depends(get_db)
):

    # 1. 사용자 식별 (원영님 로직)
    final_user_id = "Guest"
    if current_user:
        final_user_id = current_user
    elif user_id:
        final_user_id = user_id

    try:
        # 2. 파일 확장자 검사 (서현님 로직)
        if not file.filename:
            raise HTTPException(status_code=400, detail="업로드된 파일명이 없습니다.")

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식: {ext}")

        # 3. 파일 저장 
        filename = file.filename
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 4. AI 분석 실행
        result = analyzeVoice(wav_path=file_path, reference_song=reference_song, user_bpm=user_bpm)
        
        if not isinstance(result, dict):
            raise HTTPException(status_code=500, detail="AI 분석 결과 형식이 올바르지 않습니다.")
        if "error" in result:
            return {"status": "fail", "message": result["error"]}

        # 5. 데이터 안전하게 추출 (서현님 로직)
        scores = result.get("scores", {"pitch": 0.0, "tempo": 0.0, "volume": 0.0})
        analysis_values = result.get("analysis_values", {"pitch_hz_avg": 0.0, "tempo_bpm": 0.0, "volume_rms_avg": 0.0})
        similar_songs = result.get("similar_songs", [])
        similar_artists = result.get("similar_artists", [])

        # 6. LLM 피드백 호출 (원영님 로직)
        real_ai_feedback = get_vocal_feedback(
            pitch_score=scores.get("pitch", 0.0),
            tempo_score=scores.get("tempo", 0.0),
            avg_volume=scores.get("volume", 0.0)
        )
        real_ai_recommendations = recommend_songs("내 음색에 어울리는 한국 가수")

        # 7. 분석 결과 DB 저장 
        new_analysis = models.AnalysisResult(
            user_id=final_user_id,
            filename=filename,
            pitch_score=scores.get("pitch", 0.0),
            tempo_score=scores.get("tempo", 0.0),
            volume_score=scores.get("volume", 0.0),
            pitch_hz_avg=analysis_values.get("pitch_hz_avg", 0.0),
            tempo_bpm=analysis_values.get("tempo_bpm", 0.0),
            volume_rms_avg=analysis_values.get("volume_rms_avg", 0.0),
            feedback=real_ai_feedback,
            feature_path=file_path
        )
        db.add(new_analysis)

        # 8. 예약 상태 업데이트 
        reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
        if reservation:
            reservation.status = "completed"

        db.commit() 
        db.refresh(new_analysis)

        # 9. 데이터 시각화용 차트 데이터 조립 (원영님 로직)
        if final_user_id == "Guest":
            chart_data = {
                "labels": ["오늘"],
                "datasets": {
                    "pitch": [scores.get("pitch", 0.0)],
                    "tempo": [scores.get("tempo", 0.0)],
                    "volume": [scores.get("volume", 0.0)]
                }
            }
        else:
            recent_records = db.query(models.AnalysisResult)\
                               .filter(models.AnalysisResult.user_id == final_user_id)\
                               .order_by(models.AnalysisResult.id.desc())\
                               .limit(5)\
                               .all()
            
            recent_records.reverse()
            labels, pitch_data, tempo_data, volume_data = [], [], [], []

            for idx, record in enumerate(recent_records):
                if idx == len(recent_records) - 1:
                    labels.append("오늘")
                else:
                    labels.append(f"{idx + 1}회차")
                    
                pitch_data.append(record.pitch_score)
                tempo_data.append(record.tempo_score)
                volume_data.append(record.volume_score)

            chart_data = {
                "labels": labels,
                "datasets": {"pitch": pitch_data, "tempo": tempo_data, "volume": volume_data}
            }

        # 10. 🚨 [보안] 분석 완료 후 원본 오디오 파일 즉시 삭제 (원영님 핵심 로직!)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🔒 보안 및 용량 관리를 위해 원본 파일이 삭제되었습니다: {file_path}")
        except Exception as e:
            print(f"⚠️ 파일 삭제 실패: {e}")

        # 11. 프론트엔드로 최종 JSON 응답 (서현님 변수 + 원영님 차트 통합)
        return {
            "status": "success", 
            "message": f"{final_user_id}님의 분석이 완료되었습니다.",
            "data": {
                "scores": scores,                 
                "trend": chart_data,                        
                "feedback": real_ai_feedback,               
                "recommendations": real_ai_recommendations,
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