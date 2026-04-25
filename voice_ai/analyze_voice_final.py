import os
import json
import numpy as np
import librosa

from extract_basic_features import extract_single_wav
from analyze_voice import analyze_voice
from audio_utils import ensure_wav
from sklearn.metrics.pairwise import cosine_similarity


# =========================
# cosine similarity
# =========================
def cosine_sim(a, b):
    a = np.array(a).reshape(1, -1)
    b = np.array(b).reshape(1, -1)
    return float(cosine_similarity(a, b)[0][0])


# =========================
# 1. 사용자 음성 분석 (핵심)
# =========================
def analyze_user_folder(audio_dir="audio"):

    user_vectors = []
    bpm_list = []
    analysis_log = []

    for file in os.listdir(audio_dir):
        if not file.endswith((".wav", ".mp3", ".mp4", ".m4a", ".flac")):
            continue

        wav_path = os.path.join(audio_dir, file)
        wav_path = ensure_wav(wav_path)

        voice_name = os.path.splitext(file)[0]
        feature_dir = os.path.join("features", voice_name)

        print(f"\n[PROCESS] {file}")

        # 🔥 핵심: 캐시 처리 (Demucs 재실행 방지)
        if not os.path.exists(feature_dir):
            extract_single_wav(wav_path)
        else:
            print(f"[SKIP] feature already exists: {voice_name}")

        result = analyze_voice(feature_dir=feature_dir)

        # BPM
        try:
            y, sr = librosa.load(wav_path, sr=None)
            tempo = librosa.beat.tempo(y=y, sr=sr)
            bpm = float(tempo[0])
            result["analysis_values"]["tempo_bpm"] = bpm
            bpm_list.append(bpm)
        except:
            bpm = None

        # 로그 저장
        analysis_log.append({
            "file": file,
            "analysis": result["analysis_values"]
        })

        print("\n🎤 USER ANALYSIS")
        for k, v in result["analysis_values"].items():
            print(f"{k}: {v}")

        user_vectors.append(result["timbre_vector"])

    # =========================
    # 평균 계산
    # =========================
    user_embedding = np.mean(user_vectors, axis=0)
    avg_bpm = np.mean(bpm_list) if bpm_list else 0

    print("\n======================")
    print("🎤 FINAL USER REPORT")
    print("======================")
    print(f"AVG BPM: {avg_bpm:.2f}")
    print(f"VECTOR DIM: {user_embedding.shape}")
    print("======================\n")

    return user_embedding, analysis_log, avg_bpm


# =========================
# 2. reference 로드
# =========================
def load_reference(json_path="reference_songs.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_embedding(path):
    return np.load(os.path.join("embedding_vectors", path)).flatten()


# =========================
# 3. 추천
# =========================
def recommend(user_embedding):

    data = load_reference()
    results = []

    for item in data:

        emb = load_embedding(item["embedding_file"])
        score = cosine_sim(user_embedding, emb)

        results.append({
            "title": item["title"],
            "artist": item["artist"],
            "score": score
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)[:10]


# =========================
# 4. 실행
# =========================
if __name__ == "__main__":

    print("[LOAD USER DATA]")

    user_embedding, log, avg_bpm = analyze_user_folder()

    print("[INFO] songs = 55\n")

    results = recommend(user_embedding)

    print("🎵 TOP RESULT\n")

    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']} - {r['artist']} ({r['score']:.4f})")