import os
import json
import numpy as np
import librosa
from ai_module.analyze_voice import load_basic_features
from ai_module.audio_utils import ensure_wav

# ===============================
# 성량 점수 (절대 RMS 기준)
# ===============================
def score_volume(rms):
    if rms >= 0.08:
        return 90
    elif rms >= 0.05:
        return 75
    elif rms >= 0.03:
        return 60
    else:
        return 40

# ===============================
# 박자 점수 (절대 BPM 기준)
# ===============================
def score_tempo(tempo_bpm):
    if 120 <= tempo_bpm <= 140:
        return 100
    elif 100 <= tempo_bpm < 120 or 140 < tempo_bpm <= 160:
        return 85
    else:
        return 70

# ===============================
# 성량 피드백
# ===============================
def volume_feedback(rms):
    if rms >= 0.08:
        return "성량이 충분하고 힘 있는 발성입니다."
    elif rms >= 0.05:
        return "안정적인 성량으로 잘 불렀습니다."
    else:
        return "조금 더 자신 있게 소리를 내도 좋겠습니다."

# ===============================
# 히스토리 로드
# ===============================
def load_history():
    if not os.path.exists("voice_history.json"):
        return []
    try:
        with open("voice_history.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

# ===============================
# 히스토리 저장
# ===============================
def save_history(history):
    with open("voice_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

# ===============================
# 히스토리 업데이트
# ===============================
def update_history(history, analysis_values):
    history.append({
        "pitch_avg": analysis_values["pitch_hz_avg"],
        "tempo": analysis_values["tempo_bpm"],
        "volume": analysis_values["volume_rms_avg"]
    })
    return history

# ===============================
# 개인 평균 계산
# ===============================
def get_personal_average(history):
    if len(history) == 0:
        return None
    pitch = sum(h["pitch_avg"] for h in history) / len(history)
    tempo = sum(h["tempo"] for h in history) / len(history)
    volume = sum(h["volume"] for h in history) / len(history)
    return {"pitch_avg": pitch, "tempo": tempo, "volume": volume}

# ===============================
# 피드백 생성
# ===============================
def generate_feedback(scores, analysis_values, personal_avg=None):
    feedback = []

    if scores["pitch"] >= 90:
        feedback.append("음정이 매우 안정적입니다.")
    elif scores["pitch"] >= 70:
        feedback.append("전반적으로 음정은 무난합니다.")
    else:
        feedback.append("음정 기복이 있어 연습이 필요합니다.")

    if scores["tempo"] >= 90:
        feedback.append("박자를 정확하게 잘 지켰습니다.")
    else:
        feedback.append("박자가 다소 불안정합니다.")

    feedback.append(volume_feedback(analysis_values["volume_rms_avg"]))

    if personal_avg:
        if analysis_values["pitch_hz_avg"] > personal_avg["pitch_avg"]:
            feedback.append("평소보다 높은 음역을 사용했습니다.")
        else:
            feedback.append("평소와 비슷한 음역대입니다.")

        if analysis_values["volume_rms_avg"] < personal_avg["volume"]:
            feedback.append("평소보다 성량이 작습니다.")

    return " ".join(feedback)

# ===============================
# WAV에서 BPM 계산
# ===============================
def calculate_bpm(wav_path):
    y, sr = librosa.load(wav_path, sr=None)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    if isinstance(tempo, np.ndarray):
        return float(tempo[0])
    return float(tempo)

# ===============================
# 단일 보이스 분석
# ===============================
def analyze_one_voice(feature_dir, wav_path):
    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"WAV 파일이 존재하지 않습니다: {wav_path}")

    wav_path = ensure_wav(wav_path)
    tempo_bpm = calculate_bpm(wav_path)

    pitch_avg, volume_avg, _, pitch_min, pitch_max, comfort_min, comfort_max = load_basic_features(feature_dir)

    analysis_values = {
        "pitch_hz_avg": round(pitch_avg, 2),
        "tempo_bpm": round(tempo_bpm, 2),
        "volume_rms_avg": round(volume_avg, 4),
        "pitch_min": round(pitch_min, 2),
        "pitch_max": round(pitch_max, 2),
        "pitch_comfort_min": round(comfort_min, 2),
        "pitch_comfort_max": round(comfort_max, 2)
    }

    pitch_score = 90 if comfort_min <= pitch_avg <= comfort_max else 60
    tempo_score = score_tempo(tempo_bpm)
    volume_score = score_volume(volume_avg)
    scores = {"pitch": pitch_score, "tempo": tempo_score, "volume": volume_score}

    history = load_history()
    personal_avg = get_personal_average(history)
    feedback = generate_feedback(scores, analysis_values, personal_avg)

    history = update_history(history, analysis_values)
    save_history(history)

    return {
        "voice_name": os.path.basename(feature_dir),
        "scores": scores,
        "analysis_values": analysis_values,
        "feedback": feedback
    }

# ===============================
# 실행
# ===============================
if __name__ == "__main__":
    voice_mapping = {
        "features/voice1_mrX": "audio/voice1_mrX.wav",
        "features/voice2_mr": "audio/voice2_mr.wav",
        "features/voice3_slow": "audio/voice3_slow.wav",
        "features/voice4_fast": "audio/voice4_fast.wav",
        "features/voice5_small": "audio/voice5_small.wav",
        "features/voice6_big": "audio/voice6_big.wav",
    }

    all_results = []

    for feature_dir, wav_path in voice_mapping.items():
        print(f"\n===== {os.path.basename(feature_dir)} 분석 중 =====")
        result = analyze_one_voice(feature_dir=feature_dir, wav_path=wav_path)
        all_results.append(result)
        print(json.dumps(result, indent=4, ensure_ascii=False))

    with open("my_voice_feedback.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=4, ensure_ascii=False)

    print("\n모든 내 목소리 평가 완료")