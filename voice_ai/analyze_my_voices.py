import os
import json
import numpy as np
import librosa

from extract_basic_features import extract_single_wav
from analyze_voice import load_basic_features
from audio_utils import ensure_wav


# ===============================
# 성량 점수
# ===============================
def score_volume(rms):
    if rms >= 0.08:
        return 90
    elif rms >= 0.05:
        return 75
    elif rms >= 0.03:
        return 60
    return 40


# ===============================
# 박자 점수
# ===============================
def score_tempo(bpm):
    if 120 <= bpm <= 140:
        return 100
    elif 100 <= bpm < 120 or 140 < bpm <= 160:
        return 85
    return 70


# ===============================
# BPM 계산
# ===============================
def calculate_bpm(wav_path):
    y, sr = librosa.load(wav_path, sr=None)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    if isinstance(tempo, np.ndarray):
        return float(tempo[0])
    return float(tempo)


# ===============================
# feature 자동 보장 함수
# ===============================
def ensure_feature(wav_path, feature_dir):
    """
    feature 없으면 자동 생성
    """
    if os.path.exists(feature_dir):
        return True

    print(f"[AUTO GENERATE] feature 생성: {feature_dir}")
    try:
        extract_single_wav(wav_path)
        return os.path.exists(feature_dir)
    except Exception as e:
        print(f"[ERROR] feature 생성 실패: {e}")
        return False


# ===============================
# 분석 함수
# ===============================
def analyze_one_voice(feature_dir, wav_path):

    wav_path = ensure_wav(wav_path)

    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"WAV 없음: {wav_path}")

    # feature 자동 생성
    if not ensure_feature(wav_path, feature_dir):
        raise RuntimeError(f"feature 생성 실패: {feature_dir}")

    # feature 로드
    pitch_avg, volume_avg, _, pitch_min, pitch_max, comfort_min, comfort_max = load_basic_features(feature_dir)

    # bpm
    try:
        tempo_bpm = calculate_bpm(wav_path)
    except:
        tempo_bpm = 0.0

    analysis_values = {
        "pitch_hz_avg": round(pitch_avg, 2),
        "tempo_bpm": round(tempo_bpm, 2),
        "volume_rms_avg": round(volume_avg, 4),
        "pitch_min": round(pitch_min, 2),
        "pitch_max": round(pitch_max, 2),
        "pitch_comfort_min": round(comfort_min, 2),
        "pitch_comfort_max": round(comfort_max, 2)
    }

    scores = {
        "pitch": 90 if comfort_min <= pitch_avg <= comfort_max else 60,
        "tempo": score_tempo(tempo_bpm),
        "volume": score_volume(volume_avg)
    }

    return {
        "voice_name": os.path.basename(feature_dir),
        "scores": scores,
        "analysis_values": analysis_values
    }


# ===============================
# 실행부
# ===============================
if __name__ == "__main__":

    voice_mapping = {
        "features/voice1_mrX": "user_audio/voice1_mrX.wav",
        "features/voice2_mr": "user_audio/voice2_mr.wav",
        "features/voice3_slow": "user_audio/voice3_slow.wav",
        "features/voice4_fast": "user_audio/voice4_fast.wav",
        "features/voice5_small": "user_audio/voice5_small.wav",
        "features/voice6_big": "user_audio/voice6_big.wav",
    }

    results = []

    for feature_dir, wav_path in voice_mapping.items():

        print(f"\n===== {os.path.basename(feature_dir)} =====")

        try:
            result = analyze_one_voice(feature_dir, wav_path)
            print(json.dumps(result, indent=4, ensure_ascii=False))
            results.append(result)

        except Exception as e:
            print(f"[SKIP] {wav_path} → {e}")

    with open("my_voice_feedback.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print("\n[DONE] 전체 분석 완료")