"""
audio/ 폴더 안의 wav 파일에 대해
1) Demucs로 MR 제거 (mp3 출력)
2) 보컬(vocals.mp3) 로드
3) 무음 제거
4) feature 추출
5) features/<파일명>/ 저장

+ 안정적인 tempo 추출 (librosa 버전 호환 완료)
+ 음역대 분석
"""

import os
import subprocess
import numpy as np
import librosa

# 🔥 수정 (import 경로)
from ai_module.audio_utils import ensure_wav

# 🔥 기준 경로 (중요)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

AUDIO_DIR = os.path.join(BASE_DIR, "audio")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
FEATURE_DIR = os.path.join(BASE_DIR, "features")

SR = 22050

os.makedirs(FEATURE_DIR, exist_ok=True)


# =====================
# 🔥 추가 (핵심 해결)
# =====================
def extract_single_wav(wav_path):
    """
    서버에서 사용하는 단일 wav 처리 함수
    """
    audio_dir = os.path.dirname(wav_path)
    wav_name = os.path.basename(wav_path)
    process_one_file(audio_dir, wav_name)


# =====================
# Demucs (vocals 추출)
# =====================
def separate_vocals(wav_path):
    subprocess.run(
        [
            "python", "-m", "demucs",
            "--two-stems", "vocals",
            "--mp3",
            "-n", "htdemucs",
            wav_path,
            "-o", TEMP_DIR
        ],
        check=True
    )

    name = os.path.splitext(os.path.basename(wav_path))[0]

    return os.path.join(
        TEMP_DIR, "htdemucs", name, "vocals.mp3"
    )


# =====================
# Feature 추출
# =====================
def extract_features(y, sr):
    features = {}

    # =====================
    # Pitch (F0)
    # =====================
    f0, _, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7")
    )

    f0_clean = f0[~np.isnan(f0)]
    features["f0"] = np.nan_to_num(f0)

    # 음역대
    if len(f0_clean) > 0:
        pitch_min = float(np.min(f0_clean))
        pitch_max = float(np.max(f0_clean))
        pitch_range = pitch_max - pitch_min
    else:
        pitch_min = pitch_max = pitch_range = 0.0

    features["pitch_min"] = np.array([pitch_min])
    features["pitch_max"] = np.array([pitch_max])
    features["pitch_range"] = np.array([pitch_range])

    # =====================
    # TEMPO
    # =====================
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
    tempo_value = float(tempo[0]) if len(tempo) > 0 else 0.0
    features["tempo"] = np.array([tempo_value])

    # =====================
    # RMS
    # =====================
    features["rms"] = librosa.feature.rms(y=y)[0]

    # =====================
    # MFCC
    # =====================
    features["mfcc"] = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

    # =====================
    # Spectral features
    # =====================
    features["spectral_centroid"] = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    features["spectral_bandwidth"] = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    features["spectral_rolloff"] = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]

    # =====================
    # ZCR
    # =====================
    features["zcr"] = librosa.feature.zero_crossing_rate(y)[0]

    return features


# =====================
# 1개 파일 처리
# =====================
def process_one_file(audio_dir, wav_name):
    wav_path = os.path.join(audio_dir, wav_name)

    if not os.path.exists(wav_path):
        print(f"[SKIP] file not found: {wav_path}")
        return

    wav_path = ensure_wav(wav_path)

    name = os.path.splitext(os.path.basename(wav_path))[0]

    print(f"[PROCESS] {os.path.basename(wav_path)}")

    vocals_path = separate_vocals(wav_path)

    if not os.path.exists(vocals_path):
        print(f"[SKIP] vocals not found")
        return

    y, sr = librosa.load(vocals_path, sr=SR, mono=True)

    # 무음 제거
    y, _ = librosa.effects.trim(y, top_db=20)

    if len(y) < sr:
        print(f"[SKIP] too short audio")
        return

    features = extract_features(y, sr)

    out_dir = os.path.join(FEATURE_DIR, name)
    os.makedirs(out_dir, exist_ok=True)

    for k, v in features.items():
        np.save(os.path.join(out_dir, f"{k}.npy"), v)

    print(f"[DONE] Features saved → {out_dir}")


# =====================
# batch 실행
# =====================
if __name__ == "__main__":

    for f in os.listdir(AUDIO_DIR):
        if f.lower().endswith((".wav", ".mp3", ".mp4", ".m4a", ".flac")):
            process_one_file(AUDIO_DIR, f)

    print("\nALL FEATURE EXTRACTION DONE")