import os
import json
import numpy as np

BASE_DIR = "user_features"
OUTPUT_PATH = "summary_features.json"


# =========================
# 안전 로더
# =========================
def safe_load(path):
    try:
        if not os.path.exists(path):
            print("[MISS FILE]", path)
            return None

        data = np.load(path, allow_pickle=True)

        # scalar
        if np.isscalar(data):
            return float(data)

        # array
        return data.flatten().tolist()

    except Exception as e:
        print("[LOAD ERROR]", path, "->", e)
        return None


# =========================
# 1. 폴더 존재 확인
# =========================
print("\n===== BASE DIR CHECK =====")
print("BASE_DIR EXISTS:", os.path.exists(BASE_DIR))
print("CONTENT:", os.listdir(BASE_DIR))


# =========================
# 2. voice 폴더 필터링
# =========================
voices = [
    v for v in os.listdir(BASE_DIR)
    if os.path.isdir(os.path.join(BASE_DIR, v))
]

print("\n===== DETECTED VOICES =====")
print("COUNT:", len(voices))
print(voices)


# =========================
# 3. feature 생성
# =========================
results = []

for voice in sorted(voices):
    voice_path = os.path.join(BASE_DIR, voice)

    print("\n========================")
    print("[VOICE]", voice)

    feature = {
        "voice": voice,

        "mfcc": safe_load(os.path.join(voice_path, "mfcc.npy")),
        "pitch_max": safe_load(os.path.join(voice_path, "pitch_max.npy")),
        "pitch_min": safe_load(os.path.join(voice_path, "pitch_min.npy")),
        "pitch_range": safe_load(os.path.join(voice_path, "pitch_range.npy")),
        "rms": safe_load(os.path.join(voice_path, "rms.npy")),

        "spectral_bandwidth": safe_load(os.path.join(voice_path, "spectral_bandwidth.npy")),
        "spectral_centroid": safe_load(os.path.join(voice_path, "spectral_centroid.npy")),
        "spectral_rolloff": safe_load(os.path.join(voice_path, "spectral_rolloff.npy")),

        "tempo": safe_load(os.path.join(voice_path, "tempo.npy")),
        "zcr": safe_load(os.path.join(voice_path, "zcr.npy"))
    }

    results.append(feature)

    print("[DONE]", voice)


# =========================
# 4. 저장
# =========================
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("\n========================")
print("[FINISH]")
print("TOTAL VOICES:", len(results))
print("OUTPUT:", OUTPUT_PATH)