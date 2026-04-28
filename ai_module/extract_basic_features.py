import os
import numpy as np
from ai_module.audio_utils import ensure_wav

AUDIO_DIR = "audio"
FEATURE_DIR = "features"

os.makedirs(FEATURE_DIR, exist_ok=True)


def process_one_file(audio_dir, wav_name):
    wav_path = os.path.join(audio_dir, wav_name)

    if not os.path.exists(wav_path):
        print(f"[SKIP] file not found: {wav_path}")
        return

    wav_path = ensure_wav(wav_path)
    name = os.path.splitext(os.path.basename(wav_path))[0]

    print(f"[PROCESS] {os.path.basename(wav_path)}")

    out_dir = os.path.join(FEATURE_DIR, name)
    os.makedirs(out_dir, exist_ok=True)

    # AI 분석용 실제 feature 대신 더미 feature 저장
    dummy_features = {
        "f0": np.array([0.0]),
        "pitch_min": np.array([0.0]),
        "pitch_max": np.array([0.0]),
        "pitch_range": np.array([0.0]),
        "tempo_bpm": np.array([120.0]),
        "rms": np.array([0.1]),
        "mfcc": np.zeros((13, 1)),
        "spectral_centroid": np.array([0.0]),
        "spectral_bandwidth": np.array([0.0]),
        "spectral_rolloff": np.array([0.0]),
        "zcr": np.array([0.0]),
    }

    for k, v in dummy_features.items():
        np.save(os.path.join(out_dir, f"{k}.npy"), v)

    print(f"[DONE] Dummy features saved → {out_dir}")


def extract_single_wav(wav_path):
    process_one_file(
        os.path.dirname(wav_path),
        os.path.basename(wav_path)
    )


if __name__ == "__main__":
    if os.path.exists(AUDIO_DIR):
        for f in os.listdir(AUDIO_DIR):
            if f.lower().endswith((".wav", ".mp3", ".mp4", ".m4a", ".flac")):
                process_one_file(AUDIO_DIR, f)

    print("\n모든 음성 파일 feature 추출 완료")