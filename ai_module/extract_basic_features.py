import os
import subprocess
import numpy as np
import librosa
from ai_module.audio_utils import ensure_wav

AUDIO_DIR = "audio"
TEMP_DIR = "temp"
FEATURE_DIR = "features"
SR = 22050

os.makedirs(FEATURE_DIR, exist_ok=True)


def separate_vocals(wav_path):
    command = [
        "demucs", 
        "--two-stems", "vocals",
        "--mp3",
        "-n", "htdemucs",
        wav_path,
        "-o", TEMP_DIR,
        "-d", "cpu" 
    ]
    
    print(f"[System] Demucs 실행 중: {wav_path}")
    
    subprocess.run(command, check=True)

    name = os.path.splitext(os.path.basename(wav_path))[0]
    vocals_path = os.path.join(TEMP_DIR, "htdemucs", name, "vocals.mp3")
    return vocals_path

def extract_features(y, sr):
    features = {}

    f0, _, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7")
    )

    f0_clean = f0[~np.isnan(f0)]
    features["f0"] = np.nan_to_num(f0)

    if len(f0_clean) > 0:
        pitch_min = np.min(f0_clean)
        pitch_max = np.max(f0_clean)
        pitch_range = pitch_max - pitch_min
    else:
        pitch_min = 0
        pitch_max = 0
        pitch_range = 0

    features["pitch_min"] = np.array([pitch_min])
    features["pitch_max"] = np.array([pitch_max])
    features["pitch_range"] = np.array([pitch_range])

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0])
    else:
        tempo = float(tempo)
    features["tempo_bpm"] = np.array([tempo])

    features["rms"] = librosa.feature.rms(y=y)[0]
    features["mfcc"] = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    features["spectral_centroid"] = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    features["spectral_bandwidth"] = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    features["spectral_rolloff"] = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    features["zcr"] = librosa.feature.zero_crossing_rate(y)[0]

    return features


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
        print("[SKIP] vocals.mp3 not found")
        return

    y, sr = librosa.load(vocals_path, sr=SR, mono=True)
    y, _ = librosa.effects.trim(y, top_db=20)

    if len(y) < sr:
        print("[SKIP] 음성 너무 짧음")
        return

    features = extract_features(y, sr)

    out_dir = os.path.join(FEATURE_DIR, name)
    os.makedirs(out_dir, exist_ok=True)

    for k, v in features.items():
        np.save(os.path.join(out_dir, f"{k}.npy"), v)

    print(f"[DONE] Features saved → {out_dir}")


def extract_single_wav(wav_path):
    process_one_file(
        os.path.dirname(wav_path),
        os.path.basename(wav_path)
    )


if __name__ == "__main__":
    for f in os.listdir(AUDIO_DIR):
        if f.lower().endswith((".wav", ".mp3", ".mp4", ".m4a", ".flac")):
            process_one_file(AUDIO_DIR, f)

    print("\n모든 음성 파일 feature 추출 완료")