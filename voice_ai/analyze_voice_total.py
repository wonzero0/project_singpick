import os
import numpy as np
import json
from sklearn.metrics.pairwise import cosine_similarity

from analyze_voice_multi import analyze_all_voices


# ===============================
# reference songs 로드
# ===============================
def load_reference_songs(path="reference_songs.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ===============================
# cosine similarity 안전 처리
# ===============================
def cosine_safe(a, b):
    a = np.array(a).flatten()
    b = np.array(b).flatten()

    if a.shape[0] != b.shape[0]:
        return 0.0

    return float(cosine_similarity(
        a.reshape(1, -1),
        b.reshape(1, -1)
    )[0][0])


# ===============================
# voice profile 생성
# ===============================
def voice_profile(feat):

    pitch = feat["pitch_hz_avg"]
    rms = feat["volume_rms_avg"]
    bpm = feat["tempo_bpm"]

    # 보컬 타입
    if pitch > 420:
        voice_type = "고음형 보컬"
    elif pitch > 320:
        voice_type = "중음형 보컬"
    else:
        voice_type = "저음형 보컬"

    # 에너지
    if rms > 0.13:
        energy = "높음"
    elif rms > 0.09:
        energy = "중간"
    else:
        energy = "낮음"

    # 템포 성향
    if bpm > 130:
        tempo_type = "빠른 템포 선호"
    elif bpm > 100:
        tempo_type = "중간 템포 선호"
    else:
        tempo_type = "느린 템포 선호"

    return {
        "voice_type": voice_type,
        "energy": energy,
        "tempo_type": tempo_type
    }


# ===============================
# comfort score
# ===============================
def comfort_score(user, song):

    umin = user.get("pitch_comfort_min", 0)
    umax = user.get("pitch_comfort_max", 0)
    smin = song.get("pitch_min", 0)
    smax = song.get("pitch_max", 0)

    overlap = max(0, min(umax, smax) - max(umin, smin))
    user_range = umax - umin

    return overlap / user_range if user_range > 0 else 0.0


# ===============================
# 🔥 embedding load (최종)
# ===============================
def load_song_embedding(song):
    file = song["embedding_file"]  # ✅ 그대로 사용

    path = os.path.join("embedding_vectors", file)

    if not os.path.exists(path):
        print(f"[WARNING] 임베딩 없음: {file}")
        return None

    return np.load(path).flatten()


# ===============================
# 추천
# ===============================
def recommend(user_vec, user_feat, songs):

    results = []

    for s in songs:

        song_vec = load_song_embedding(s)

        if song_vec is None:
            continue

        sim = cosine_safe(user_vec, song_vec)

        # 👉 embedding 중심 추천
        score = 0.7 * sim + 0.3 * comfort_score(user_feat, s)

        results.append({
            "title": s["title"],
            "artist": s["artist"],
            "score": round(score, 4)
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)


# ===============================
# MAIN
# ===============================
if __name__ == "__main__":

    print("\n==============================")
    print("🎤 최종 음성 분석 리포트")
    print("==============================")

    # =========================
    # 1. 사용자 feature 평균
    # =========================
    user_feat = analyze_all_voices()

    # =========================
    # 2. 사용자 embedding 평균
    # =========================
    user_vec = np.load("user_session_embedding.npy").flatten()

    # =========================
    # 3. 분석 결과 출력
    # =========================
    print("\n📊 [1] 음성 분석 결과")
    print(f"- 평균 음높이(Hz): {user_feat['pitch_hz_avg']}")
    print(f"- 템포(BPM): {user_feat['tempo_bpm']}")
    print(f"- 평균 음량(RMS): {user_feat['volume_rms_avg']}")
    print(f"- 최소 음역: {user_feat['pitch_min']}")
    print(f"- 최대 음역: {user_feat['pitch_max']}")
    print(f"- 편안한 음역 (최소): {user_feat['pitch_comfort_min']}")
    print(f"- 편안한 음역 (최대): {user_feat['pitch_comfort_max']}")

    # =========================
    # 4. 음성 스타일
    # =========================
    profile = voice_profile(user_feat)

    print("\n🎧 [2] 음성 스타일 분석")
    print(f"- 보컬 타입: {profile['voice_type']}")
    print(f"- 에너지: {profile['energy']}")
    print(f"- 템포 성향: {profile['tempo_type']}")

    # =========================
    # 5. 추천
    # =========================
    songs = load_reference_songs()

    print("\n🎵 [3] 추천 노래")

    top = recommend(user_vec, user_feat, songs)

    if len(top) == 0:
        print("❌ 추천 결과 없음 (embedding_vectors 폴더 확인)")
    else:
        for i, r in enumerate(top[:10], 1):
            print(f"{i}. {r['title']} - {r['artist']} (유사도: {r['score']})")

    print("\n==============================")
    print("분석 완료")
    print("==============================")