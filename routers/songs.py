from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional 
from database import get_db
import models
import shutil
import os
from ai_module.analyze_voice_final import analyzeVoice
from core.ai_engine import get_vocal_feedback, recommend_songs
from core.auth import get_current_user_optional 
from pydantic import BaseModel

# Swagger 문서에 보여질 예시 데이터 (프론트엔드 참고용)
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
        "recommendations": "아이유 - 밤편지를 추천합니다."
    }

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files") 

router = APIRouter(prefix="/songs", tags=["🎵 Songs (노래/AI 연동)"])


@router.post(
    "/upload", 
    summary="🎙️ 녹음 파일 업로드 (회원/비회원 공용)",
    description="""
    사용자의 가창 WAV 파일을 분석하여 점수, AI 피드백, 그리고 프론트엔드 차트용 그래프 데이터를 제공합니다.
    - **회원**: 로그인 토큰을 함께 보내면 본인 히스토리에 자동 저장됩니다.
    - **비회원**: 토큰 없이 업로드 시 'Guest' 계정으로 처리됩니다.
    """,
    response_model=AnalysisResponse, # 👈 어떤 데이터가 나가는지 명시
    status_code=200 # 👈 성공 시 기본 상태 코드
)
async def upload_song(
    file: UploadFile = File(...),
    reservation_id: int = Form(...),
    # 1. 폼 데이터의 user_id는 선택 사항으로 변경
    user_id: Optional[str] = Form(None), 
    # 2. 토큰이 있으면 가져오고 없으면 None을 주는 문지기 적용
    current_user: Optional[str] = Depends(get_current_user_optional), 
    reference_song: str = Form("No_Doubt"),
    user_bpm: float = Form(120.0),
    db: Session = Depends(get_db)
):

    # 3. 사용자 식별 우선순위 결정 (토큰 ID > 폼 ID > Guest)
    final_user_id = "Guest"
    if current_user:
        final_user_id = current_user
    elif user_id:
        final_user_id = user_id

    # 1. 파일 저장 로직 ...
    filename = file.filename
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 2. AI 분석 실행
        result = analyzeVoice(wav_path=file_path, reference_song=reference_song, user_bpm=user_bpm)
        
        if "error" in result:
            return {"status": "fail", "message": result["error"]}

        # 3. AI 엔진 호출 (제미나이 텍스트 피드백)
        real_ai_feedback = get_vocal_feedback(
            pitch_score=result["scores"]["pitch"],
            tempo_score=result["scores"]["tempo"],
            avg_volume=result["scores"]["volume"]
        )
        
        real_ai_recommendations = recommend_songs("내 음색에 어울리는 한국 가수")

        # 4. 분석 결과 DB 저장 (식별된 final_user_id 사용)
        new_analysis = models.AnalysisResult(
            user_id=final_user_id, # 로그인 여부에 따라 Guest 또는 ID 저장
            filename=filename,
            pitch_score=result["scores"]["pitch"],
            tempo_score=result["scores"]["tempo"],
            volume_score=result["scores"]["volume"],
            pitch_hz_avg=result["analysis_values"]["pitch_hz_avg"],
            tempo_bpm=result["analysis_values"]["tempo_bpm"],
            volume_rms_avg=result["analysis_values"]["volume_rms_avg"],
            feedback=real_ai_feedback,
            feature_path=file_path
        )
        db.add(new_analysis)

        # 5. 예약 상태 업데이트 및 commit ...
        reservation = db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()
        if reservation:
            reservation.status = "completed"

        db.commit() 

        # ---------------------------------------------------------
        # [데이터 시각화용 딕셔너리 조립 (진짜 DB 연동)]
        # ---------------------------------------------------------
        if final_user_id == "Guest":
            # 1. 비회원인 경우: 과거 기록이 없으므로 오늘 점수만 차트에 담아줍니다.
            chart_data = {
                "labels": ["오늘"],
                "datasets": {
                    "pitch": [result["scores"]["pitch"]],
                    "tempo": [result["scores"]["tempo"]],
                    "volume": [result["scores"]["volume"]]
                }
            }
        else:
            # 2. 회원인 경우: DB에서 본인의 최근 5번 기록을 최신순으로 가져옵니다.
            recent_records = db.query(models.AnalysisResult)\
                               .filter(models.AnalysisResult.user_id == final_user_id)\
                               .order_by(models.AnalysisResult.id.desc())\
                               .limit(5)\
                               .all()
            
            # 그래프는 '과거 -> 현재' 순서로 그려야 하므로 리스트 순서를 뒤집어줍니다.
            recent_records.reverse()

            labels = []
            pitch_data = []
            tempo_data = []
            volume_data = []

            # DB에서 뽑아온 데이터로 배열을 차곡차곡 채웁니다.
            for idx, record in enumerate(recent_records):
                # 맨 마지막 데이터(방금 DB에 저장된 것)는 '오늘'로 라벨링
                if idx == len(recent_records) - 1:
                    labels.append("오늘")
                else:
                    labels.append(f"{idx + 1}회차")
                    
                pitch_data.append(record.pitch_score)
                tempo_data.append(record.tempo_score)
                volume_data.append(record.volume_score)

            chart_data = {
                "labels": labels,
                "datasets": {
                    "pitch": pitch_data,
                    "tempo": tempo_data,
                    "volume": volume_data
                }
            }

        # ==========================================
        # 🚨 [보안] 분석 완료 후 원본 오디오 파일 즉시 삭제
        # ==========================================
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🔒 보안 및 용량 관리를 위해 원본 파일이 삭제되었습니다: {file_path}")
        except Exception as e:
            print(f"⚠️ 파일 삭제 실패: {e}")

        # 프론트엔드로 최종 JSON 응답
        return {
            "status": "success", 
            "message": f"{final_user_id}님의 분석이 완료되었습니다.",
            "data": {
                "scores": result["scores"],                 # 방사형 차트용 (현재 점수)
                "trend": chart_data,                        # 꺾은선 그래프용 (실제 DB 기록)
                "feedback": real_ai_feedback,               # 제미나이 텍스트 피드백
                "recommendations": real_ai_recommendations    # 추천 가수/곡
            }
        }

    # 🚨 에러 발생 시 처리
    except Exception as e:
        db.rollback()  # 에러가 나면 DB에 잘못 들어간 걸 다시 취소(롤백)합니다.
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"서버 에러: {str(e)}")