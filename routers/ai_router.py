from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.ai_engine import get_vocal_feedback
# 사진의 칼럼명을 참조할 모델 (가정)
from models.score import Score 

router = APIRouter()

@router.get("/get-feedback/{reservation_id}")
async def get_feedback(reservation_id: int, db: Session = Depends(get_db)):
    # 1. DB에서 분석 데이터 조회
    data = db.query(Score).filter(Score.reservation_id == reservation_id).first()
    if not data:
        return {"error": "분석 데이터가 없습니다."}
    
    # 2. AI 엔진에게 데이터 전달
    feedback = get_vocal_feedback(
        pitch_score=data.score, 
        tempo_score=data.tempo_bpm, # 예시 매핑
        avg_volume=data.volume_rms, 
        pitch_hz_avg=data.pitch_hz_avg,
        tempo_bpm=data.tempo_bpm,
        volume_rms_avg=data.volume_rms
    )
    
    # 3. DB 'feedback' 칼럼 업데이트
    data.feedback = feedback
    db.commit()
    
    return {"feedback": feedback}