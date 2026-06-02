import os
from ai_module.extract_user_features import extract_user_features
from ai_module.analyze_voice_total import analyze_voice_total
from ai_module.extract_user_embedding import extract_user_embedding
from ai_module.make_user_session_embedding import make_user_session_embedding
from ai_module.recommend_by_similarity import recommend_by_similarity
import ai_module.karaoke_scoring as karaoke_scoring

from core.ai_engine import get_vocal_feedback


# =========================
# 🎯 서버용 분석 함수
# =========================
def run_analysis(audio_path):
    print("\n🎤 서버 음성 분석 시작")

    # 1. feature 추출
    print("🔧 feature 추출")
    feature = extract_user_features(audio_path)

    # 2. 음성 분석
    print("🧠 음성 분석")
    analysis = analyze_voice_total(feature)

    # 3. embedding 생성
    print("🧬 embedding 생성")
    embedding = extract_user_embedding(feature)

    # (단일 파일이라 평균 필요 없음)
    user_embedding = embedding

    # 4. 추천
    print("🎯 추천 실행")
    result = recommend_by_similarity(user_embedding)

    # 5. 점수 계산
    print("🎤 점수 계산")
    score = karaoke_scoring.run([analysis])

    # 6. Gemini 연동 
    print("🤖 AI 피드백 생성 중...")

    vals = analysis["analysis_values"]
    feedback = get_vocal_feedback(
        pitch_score=score.get("pitch", 0),       # karaoke_scoring 내의 pitch 점수
        tempo_score=score.get("rhythm", 0),      # karaoke_scoring 내의 rhythm 점수
        avg_volume=vals.get("volume_avg", 0),    # 칼럼: volume_avg
        pitch_hz_avg=vals.get("pitch_hz_avg", 0),# 칼럼: pitch_hz_avg
        tempo_bpm=vals.get("tempo_bpm", 0),      # 칼럼: tempo_bpm
        volume_rms_avg=vals.get("volume_rms", 0) # 칼럼: volume_rms
    )


    # 7. 결과 정리 
    return {
        "analysis": analysis,
        "recommendation": result,
        "score": score,
        "feedback":feedback
    }