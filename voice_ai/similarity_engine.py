import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# ===============================
# 1. 코사인 유사도 계산
# ===============================
def calculate_similarity(user_vector, song_vector):
    user_vec = np.array(user_vector).reshape(1, -1)
    song_vec = np.array(song_vector).reshape(1, -1)
    return round(float(cosine_similarity(user_vec, song_vec)[0][0]), 4)

# ===============================
# 2. 편안한 음역 기반 점수 계산
# ===============================
def comfort_range_score(user_features, song_features):
    u_min = user_features.get("pitch_comfort_min", 0)
    u_max = user_features.get("pitch_comfort_max", 0)
    s_min = song_features.get("pitch_min", 0)
    s_max = song_features.get("pitch_max", 0)

    overlap_min = max(u_min, s_min)
    overlap_max = min(u_max, s_max)
    overlap = max(0, overlap_max - overlap_min)

    user_range = u_max - u_min
    range_score = overlap / user_range if user_range > 0 else 0

    user_avg = user_features.get("pitch_hz_avg", 0)
    song_avg = song_features.get("pitch_hz_avg", 0)
    avg_diff = abs(user_avg - song_avg)
    avg_score = max(0, 1 - (avg_diff / 300))

    return round(0.7 * range_score + 0.3 * avg_score, 3)

# ===============================
# 3. Top-N 추천 (timbre + comfort score)
# ===============================
def recommend_songs(user_vector, user_features, songs, top_n=5):
    results = []
    for song in songs:
        if not song.get("timbre_vector"):
            continue
        sim_score = calculate_similarity(user_vector, song["timbre_vector"])
        comfort_score = comfort_range_score(user_features, song)
        final_score = 0.6 * sim_score + 0.4 * comfort_score
        results.append({
            "artist": song["artist"],
            "song": song["title"],
            "similarity": round(final_score, 4)
        })
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_n]

# ===============================
# 4. 실제 WAV 기반 실행
# ===============================
if __name__ == "__main__":
    from analyze_voice import analyze_voice  # 최신 analyze_voice.py 임포트

    wav_feature_dir = "features/voice6_big"
    result = analyze_voice(wav_feature_dir)
    user_vector = result["timbre_vector"]
    user_features = result["analysis_values"]

    # reference_songs.json 로드
    with open("reference_songs.json", "r", encoding="utf-8") as f:
        songs_json = json.load(f)

    songs_list = []
    for song_id, song in songs_json.items():
        songs_list.append({
            "artist": song.get("artist"),
            "title": song.get("title"),
            "timbre_vector": song.get("timbre_vector"),
            "pitch_min": song.get("pitch_min", 0),
            "pitch_max": song.get("pitch_max", 0),
            "pitch_hz_avg": song.get("pitch_hz_avg", 0)
        })

    # 추천 실행
    top_songs = recommend_songs(user_vector, user_features, songs_list, top_n=10)

    # 결과 출력
    print("🎤 추천 가수 결과 (음색 + 음역대 반영)")
    print(f"사용자 편안 음역: {user_features['pitch_comfort_min']} ~ {user_features['pitch_comfort_max']} Hz")
    for i, r in enumerate(top_songs, start=1):
        print(f"Top-{i}: {r['artist']} - {r['song']} (유사도: {r['similarity']})")