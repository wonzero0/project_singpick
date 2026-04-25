import os
import numpy as np
import librosa

# =========================
# 설정
# =========================
INPUT_DIR = "user_audio"
OUTPUT_DIR = "user_features"
SR = 22050


# =========================
# feature 추출 함수
# =========================
def extract_features(y, sr):
    features = {}

    # -------------------------
    # 1. pitch (🔥 핵심 수정)
    # -------------------------
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7")
    )

    # ✅ analyze_voice에서 필요
    features["f0"] = np.nan_to_num(f0)

    f0_clean = f0[~np.isnan(f0)] if f0 is not None else np.array([])

    if len(f0_clean) > 0:
        pitch_min = np.min(f0_clean)
        pitch_max = np.max(f0_clean)
        pitch_range = pitch_max - pitch_min
    else:
        pitch_min = 0.0
        pitch_max = 0.0
        pitch_range = 0.0

    features["pitch_min"] = np.array([pitch_min])
    features["pitch_max"] = np.array([pitch_max])
    features["pitch_range"] = np.array([pitch_range])

    # -------------------------
    # 2. tempo (🔥 안정 버전)
    # -------------------------
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)

    # 배열 → 스칼라 변환
    tempo_value = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)
    features["tempo"] = np.array([tempo_value])

    # -------------------------
    # 3. rms
    # -------------------------
    rms = librosa.feature.rms(y=y)[0]
    features["rms"] = rms

    # -------------------------
    # 4. mfcc (🔥 shape 유지 중요)
    # -------------------------
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    features["mfcc"] = mfcc

    # -------------------------
    # 5. spectral centroid
    # -------------------------
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    features["spectral_centroid"] = spectral_centroid

    # -------------------------
    # 6. spectral bandwidth
    # -------------------------
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    features["spectral_bandwidth"] = spectral_bandwidth

    # -------------------------
    # 7. spectral rolloff
    # -------------------------
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    features["spectral_rolloff"] = spectral_rolloff

    # -------------------------
    # 8. zero crossing rate
    # -------------------------
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    features["zcr"] = zcr

    return features


# =========================
# feature 저장 함수
# =========================
def save_features(song_name, features):
    song_dir = os.path.join(OUTPUT_DIR, song_name)
    os.makedirs(song_dir, exist_ok=True)

    for key, value in features.items():
        save_path = os.path.join(song_dir, f"{key}.npy")
        np.save(save_path, value)


# =========================
# 전체 사용자 음성 처리
# =========================
def process_all_user_audio():
    if not os.path.exists(INPUT_DIR):
        raise FileNotFoundError(f"user_audio 폴더 없음: {INPUT_DIR}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    success = []
    fail = []

    audio_files = [
        f for f in os.listdir(INPUT_DIR)
        if f.lower().endswith((".wav", ".mp3"))
    ]

    if len(audio_files) == 0:
        print("[INFO] user_audio 폴더에 음성 파일이 없습니다.")
        return

    for file_name in audio_files:
        song_name = os.path.splitext(file_name)[0]
        file_path = os.path.join(INPUT_DIR, file_name)

        print("\n" + "=" * 50)
        print(f"[LOAD] {file_path}")

        try:
            y, sr = librosa.load(file_path, sr=SR, mono=True)

            # 무음 제거 (추천)
            y, _ = librosa.effects.trim(y, top_db=20)

            if len(y) < sr:
                print("[SKIP] 너무 짧은 음성")
                continue

            features = extract_features(y, sr)
            save_features(song_name, features)

            print(f"[DONE] User features saved → {OUTPUT_DIR}\\{song_name}")
            success.append(song_name)

        except Exception as e:
            print(f"[ERROR] {song_name}: {e}")
            fail.append(song_name)

    print("\n" + "=" * 50)
    print("모든 사용자 음성 feature 추출 완료")
    print(f"[SUCCESS] 성공: {len(success)}개 -> {success}")
    print(f"[FAIL] 실패: {len(fail)}개 -> {fail}")


# =========================
# 단독 실행
# =========================
if __name__ == "__main__":
    process_all_user_audio()