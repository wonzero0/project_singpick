from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
import models
import shutil
import os
from core import ai_engine

from ai_module.analyze_voice_final import analyzeVoice
from ai_module.karaoke_scoring import calculate_score

router = APIRouter(prefix="/songs", tags=["Songs"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".mp4", ".m4a", ".flac"}

# ============================================
# 노래 업로드 + AI 분석
# ============================================
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
        # 1. 오디오 물리 분석 데이터 추출
        # =========================
        result = analyzeVoice(file_path)

        analysis_values = result.get("analysis_values", {})
        feedback = result.get("feedback", "분석 완료")
        recommendations = result.get("recommendations", [])
        similar_songs = result.get("similar_songs", [])
        similar_artists = result.get("similar_artists", [])

        # =========================
        # 2. 최종 점수 계산
        # =========================
        score = calculate_score(analysis_values)

        # Web.tsx 그래프 및 Gemini 반영을 위한 0~100 스케일 가공
        # (기존 물리 분석 모듈의 최대/평균값 기반 정형화가 필요할 수 있으나, 임시로 안전하게 맵핑)
        pitch_score_input = min(int(analysis_values.get("pitch_hz_avg", 0.0) / 4), 100) if analysis_values.get("pitch_hz_avg", 0.0) > 0 else 85
        tempo_score_input = min(int(analysis_values.get("tempo_bpm", 0.0)), 100) if analysis_values.get("tempo_bpm", 0.0) > 0 else 80
        volume_score_input = min(int(analysis_values.get("volume_rms_avg", 0.0) * 100), 100) if analysis_values.get("volume_rms_avg", 0.0) > 0 else 75

        # =========================
        # 3. 제미나이 AI 보컬 피드백 생성
        # =========================
        # ai_engine.py의 get_vocal_feedback 함수를 호출하여 보컬 리포트 생성
        gemini_feedback = ai_engine.get_vocal_feedback(
            pitch_score=pitch_score_input,
            tempo_score=tempo_score_input,
            avg_volume=volume_score_input
        )

        # =========================
        # 4. DB 저장
        # =========================
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

        reservation = db.query(models.Reservation).filter(
            models.Reservation.id == reservation_id
        ).first()

        if reservation:
            reservation.status = "completed"

        db.commit()
        db.refresh(new_analysis)

        # =========================
        # 5. 누적 히스토리 및 평균 계산
        # =========================
        all_histories = db.query(models.AnalysisResult).filter(
            models.AnalysisResult.user_id == user_id
        ).all()

        if len(all_histories) == 0:
            raise HTTPException(status_code=500, detail="히스토리 조회 실패")

        avg_score = sum(h.score for h in all_histories) / len(all_histories)
        avg_pitch = sum(h.pitch_hz_avg for h in all_histories) / len(all_histories)
        avg_tempo = sum(h.tempo_bpm for h in all_histories) / len(all_histories)
        avg_volume = sum(h.volume_rms_avg for h in all_histories) / len(all_histories)

        # 누적 가이드 피드백 문장 구성
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

        # 가수/곡 추천 결과가 비어있을 때를 대비한 든든한 예외 방어코드
        top_song = similar_songs[0] if similar_songs else "좋은 날"
        top_singer = similar_artists[0] if similar_artists else "아이유"

        # =========================
        # 6. 🌟 Web.tsx 맞춤형 응답 반환구조 체결
        # =========================
        return {
            "status": "success",
            "message": f"{user_id} 분석 완료",
            "data": {
                # 폰 화면의 'AI 상세 피드백' 텍스트 박스로 매핑되는 결과
                "feedback": gemini_feedback, 
                
                # 리액트의 setVoiceStats()가 처리할 수 있는 0~1 혹은 0~100 스케일 점수 매핑
                "pitch_score": pitch_score_input,
                "tempo_score": tempo_score_input,
                "volume_score": volume_score_input,
                
                # 리액트 추천 곡 목록 매핑
                "top_song": top_song,
                "top_singer": top_singer,

                # 기존 시스템 데이터 보존용
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
def get_user_history(
    user_id: str,
    db: Session = Depends(get_db)
):
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