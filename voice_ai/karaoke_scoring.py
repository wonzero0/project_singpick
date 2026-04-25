import os
import numpy as np
from analyze_voice import analyze_voice


# =========================
# 🎯 변환 함수 (핵심)
# =========================

def pitch_accuracy(pitch_avg, comfort_min, comfort_max):
    if pitch_avg == 0:
        return 0.0

    center = (comfort_min + comfort_max) / 2
    error = abs(pitch_avg - center)

    return float(max(0, 1 - error / 150))


def rhythm_accuracy(tempo):
    if tempo == 0:
        return 0.0

    return float(max(0, 1 - abs(tempo - 120) / 120))


def stability(pitch_min, pitch_max):
    if pitch_max == 0:
        return 0.0

    spread = pitch_max - pitch_min
    return float(max(0, 1 - spread / 300))


# =========================
# 🎯 TJ 점수 계산
# =========================
def calculate_score(features):

    pitch = pitch_accuracy(
        features["pitch_hz_avg"],
        features["pitch_comfort_min"],
        features["pitch_comfort_max"]
    )

    rhythm = rhythm_accuracy(features["tempo_bpm"])

    stable = stability(
        features["pitch_min"],
        features["pitch_max"]
    )

    score = (pitch * 0.5 + rhythm * 0.3 + stable * 0.2) * 100

    return round(min(score, 100), 1)


# =========================
# 🎯 실행
# =========================
def run():

    print("\n🎤 노래방 점수 시스템 시작\n")

    wav_dir = "user_audio/"
    feature_base = "user_features/"

    wav_files = sorted([
        f for f in os.listdir(wav_dir)
        if f.endswith(".wav")
    ])

    scores = []

    for i, wav in enumerate(wav_files):

        name = wav.replace(".wav", "")
        feature_path = os.path.join(feature_base, name)

        if not os.path.exists(feature_path):
            print(f"❌ feature 없음: {name}")
            continue

        try:
            result = analyze_voice(feature_path)
            f = result["analysis_values"]

            score = calculate_score(f)
            scores.append(score)

            print(f"🎵 {i+1}곡 ({wav}) : {score}점")

        except Exception as e:
            print(f"❌ 실패: {wav} ({e})")

    print("\n-------------------")
    print(f"🎤 최종 점수: {round(np.mean(scores),1)}점 / 100점")
    print("-------------------\n")


if __name__ == "__main__":
    run()