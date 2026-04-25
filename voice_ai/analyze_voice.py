import os
import numpy as np

# ===============================
# 기본 feature 불러오기
# ===============================
def load_basic_features(feature_dir):

    f0 = np.load(os.path.join(feature_dir, "f0.npy"))
    rms = np.load(os.path.join(feature_dir, "rms.npy"))
    mfcc = np.load(os.path.join(feature_dir, "mfcc.npy"))

    pitch_min = float(np.load(os.path.join(feature_dir, "pitch_min.npy")).item())
    pitch_max = float(np.load(os.path.join(feature_dir, "pitch_max.npy")).item())

    valid_f0 = f0[f0 > 0]

    pitch_avg = float(np.mean(valid_f0)) if len(valid_f0) > 0 else 0.0
    volume_avg = float(np.mean(rms))
    mfcc_mean = np.mean(mfcc, axis=1)

    # 편안 음역
    if len(valid_f0) > 0:
        pitch_comfort_min = float(np.percentile(valid_f0, 5))
        pitch_comfort_max = float(np.percentile(valid_f0, 95))
    else:
        pitch_comfort_min = 0.0
        pitch_comfort_max = 0.0

    return (
        pitch_avg,
        volume_avg,
        mfcc_mean,
        pitch_min,
        pitch_max,
        pitch_comfort_min,
        pitch_comfort_max
    )


# ===============================
# Timbre 벡터 생성
# ===============================
def build_timbre_vector(feature_dir):

    mfcc = np.load(os.path.join(feature_dir, "mfcc.npy"))
    centroid = np.load(os.path.join(feature_dir, "spectral_centroid.npy"))
    zcr = np.load(os.path.join(feature_dir, "zcr.npy"))

    vector = np.concatenate([
        np.mean(mfcc, axis=1),
        [np.mean(centroid)],
        [np.mean(zcr)]
    ])

    return vector.tolist()


# ===============================
# 목소리 분석 (🔥 최종)
# ===============================
def analyze_voice(feature_dir):

    (
        pitch_avg,
        volume_avg,
        _,
        user_min,
        user_max,
        comfort_min,
        comfort_max
    ) = load_basic_features(feature_dir)

    # =========================
    # 🔥 tempo 읽기 (핵심 수정)
    # =========================
    tempo_path = os.path.join(feature_dir, "tempo.npy")

    if os.path.exists(tempo_path):
        tempo_bpm = float(np.load(tempo_path).item())
    else:
        tempo_bpm = 0.0

    return {
        "analysis_values": {
            "pitch_hz_avg": round(pitch_avg, 2),
            "tempo_bpm": round(tempo_bpm, 2),
            "volume_rms_avg": round(volume_avg, 4),
            "pitch_min": round(user_min, 2),
            "pitch_max": round(user_max, 2),
            "pitch_comfort_min": round(comfort_min, 2),
            "pitch_comfort_max": round(comfort_max, 2)
        },
        "timbre_vector": build_timbre_vector(feature_dir)
    }