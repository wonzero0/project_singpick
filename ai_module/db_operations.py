import os
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import models
from core import ai_engine
from ai_module.karaoke_scoring import calculate_score

def save_analysis_result_to_db(
    db: Session,
    user_id: str,
    filename: str,
    file_path: str,
    analysis_values: dict,
    recommendations: list,
    similar_artists: list
):
    """
    Analyzes vocal data, generates AI feedback, and saves the results to the database.

    Args:
        db (Session): The SQLAlchemy database session.
        user_id (str): The ID of the user.
        filename (str): The original filename of the uploaded audio.
        file_path (str): The path where the analyzed audio file is stored.
        analysis_values (dict): Dictionary containing various analysis features
                                (e.g., pitch_hz_avg, tempo_bpm, volume_rms_avg).
        recommendations (list): List of song recommendations.
        similar_artists (list): List of similar artists.

    Returns:
        tuple: A tuple containing (new_analysis_object, score, gemini_feedback, pitch_score_input, tempo_score_input, volume_score_input).
    """

    try:
        # 1. 데이터 매핑 검증 및 타입 안전성 확보 (Mapping & Type Safety)
        # analyzeVoice가 반환하는 키(예: 'pitch')와 모델 칼럼명(예: 'pitch_hz_avg') 매칭 및 float 변환
        p_raw = analysis_values.get("pitch_hz_avg") if analysis_values.get("pitch_hz_avg") is not None else analysis_values.get("pitch")
        t_raw = analysis_values.get("tempo_bpm") if analysis_values.get("tempo_bpm") is not None else analysis_values.get("tempo")
        v_raw = analysis_values.get("volume_rms_avg") if analysis_values.get("volume_rms_avg") is not None else analysis_values.get("volume")
        
        pitch_hz_avg = float(p_raw if p_raw is not None else 0.0)
        tempo_bpm = float(t_raw if t_raw is not None else 0.0)
        volume_rms_avg = float(v_raw if v_raw is not None else 0.0)

        # calculate_score 함수 호출 시 내부 로직이 정확한 키를 참조하도록 analysis_values 업데이트
        analysis_values.update({
            "pitch_hz_avg": pitch_hz_avg,
            "tempo_bpm": tempo_bpm,
            "volume_rms_avg": volume_rms_avg
        })

        # 2. 최종 점수 계산 (기존 로직 활용)
        raw_calc_score = calculate_score(analysis_values)
        score = float(raw_calc_score if raw_calc_score is not None else 0.0)

        # 3. Gemini 피드백 생성을 위한 점수 변환 (0일 경우 기본값 설정)
        pitch_score_input = min(int(pitch_hz_avg / 4), 100) if pitch_hz_avg > 0 else 85
        tempo_score_input = min(int(tempo_bpm), 100) if tempo_bpm > 0 else 80
        volume_score_input = min(int(volume_rms_avg * 100), 100) if volume_rms_avg > 0 else 75

        # 4. Gemini API를 통한 AI 피드백 생성
        gemini_feedback = ai_engine.get_vocal_feedback(
            pitch_score=pitch_score_input,
            tempo_score=tempo_score_input,
            avg_volume=volume_score_input,
            pitch_hz_avg=pitch_hz_avg,
            tempo_bpm=tempo_bpm,
            volume_rms_avg=volume_rms_avg
        )
        # 피드백 텍스트가 비어있을 경우 대비
        if not gemini_feedback:
            gemini_feedback = "분석 결과가 생성되었으나 피드백 내용을 불러오지 못했습니다."

        # 5. DB 모델 객체 생성
        new_analysis = models.AnalysisResult(
            user_id=user_id if user_id else "GUEST",
            filename=filename,
            score=score,
            pitch_hz_avg=pitch_hz_avg,
            tempo_bpm=tempo_bpm,
            volume_rms_avg=volume_rms_avg,
            feedback=gemini_feedback[:500], # DB 칼럼 크기 제한(String 500) 준수
            feature_path=file_path
        )

        # 6. DB 저장 및 커밋
        print(f"[DEBUG] DB 저장 시도 데이터: user={new_analysis.user_id}, score={new_analysis.score}, file={new_analysis.filename}")
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
        print(f"[SUCCESS] DB 저장 완료 - ID: {new_analysis.id}")
        
        return new_analysis, score, gemini_feedback, pitch_score_input, tempo_score_input, volume_score_input

    except SQLAlchemyError as e:
        db.rollback()
        print("\n" + "!"*50)
        print(f"[CRITICAL DB ERROR] 저장 실패!")
        print(f"Error Message: {str(e)}")
        print(f"Attempted Data: \n"
              f"  - user_id: {user_id}\n"
              f"  - filename: {filename}\n"
              f"  - score: {score}\n"
              f"  - pitch_hz_avg: {pitch_hz_avg}\n"
              f"  - tempo_bpm: {tempo_bpm}\n"
              f"  - volume_rms_avg: {volume_rms_avg}\n"
              f"  - feedback length: {len(gemini_feedback) if gemini_feedback else 0}\n"
              f"  - feature_path: {file_path}")
        print("!"*50 + "\n")
        # 에러 발생 시 빈 객체와 기본값 반환하여 전체 흐름 유지
        return None, 0.0, "피드백을 생성할 수 없습니다.", 0, 0, 0