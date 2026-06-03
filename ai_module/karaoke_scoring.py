import numpy as np

# =========================
# 🎯 점수 구성 요소
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
# 🎯 FINAL SCORE
# =========================
def calculate_score(features):

    pitch = pitch_accuracy(
        features.get("pitch_hz_avg", 0),
        features.get("pitch_comfort_min", 0),
        features.get("pitch_comfort_max", 0)
    )

    rhythm = rhythm_accuracy(features.get("tempo_bpm", 0))

    stable = stability(
        features.get("pitch_min", 0),
        features.get("pitch_max", 0)
    )

    total_score = (pitch * 0.5 + rhythm * 0.3 + stable * 0.2) * 100

    return round(min(total_score, 100), 1)