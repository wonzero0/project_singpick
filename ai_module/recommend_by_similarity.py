import os
import json
import numpy as np
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity

# =========================
# 🔥 기준 경로 추가
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================
# 설정
# =========================
REFERENCE_JSON = os.path.join(BASE_DIR, "reference_songs.json")
REFERENCE_EMBEDDING_DIR = os.path.join(BASE_DIR, "embedding_vectors")
USER_EMBEDDING_DIR = os.path.join(BASE_DIR, "user_embedding_vectors")

TOP_SONG_N = 5
TOP_ARTIST_N = 5

USER_PREFIXES = ["voice", "user"]


# =========================
# 1. cosine similarity
# =========================
def cosine_sim(vec1, vec2):
    vec1 = np.array(vec1, dtype=np.float32).reshape(1, -1)
    vec2 = np.array(vec2, dtype=np.float32).reshape(1, -1)

    min_dim = min(vec1.shape[1], vec2.shape[1])
    vec1 = vec1[:, :min_dim]
    vec2 = vec2[:, :min_dim]

    return float(cosine_similarity(vec1, vec2)[0][0])


# =========================
# 2. reference JSON
# =========================
def load_reference_metadata():
    with open(REFERENCE_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================
# 3. user embedding 평균
# =========================
def load_user_session_embedding():
    user_vectors = []

    for file in os.listdir(USER_EMBEDDING_DIR):
        if file.endswith(".npy"):
            vec = np.load(os.path.join(USER_EMBEDDING_DIR, file))

            if len(vec.shape) != 1:
                vec = vec.flatten()

            user_vectors.append(vec.astype(np.float32))

    if len(user_vectors) == 0:
        raise ValueError("user embedding 없음")

    print(f"[INFO] 사용자 임베딩 개수: {len(user_vectors)}")

    user_session = np.mean(user_vectors, axis=0).astype(np.float32)

    # 🔥 저장 경로 수정
    session_path = os.path.join(BASE_DIR, "user_session_embedding.npy")
    np.save(session_path, user_session)

    print(f"[SAVE] {session_path} 저장 완료")

    return user_session


# =========================
# 4. reference embedding
# =========================
def load_reference_embedding(file_name):
    path = os.path.join(REFERENCE_EMBEDDING_DIR, file_name)

    if not os.path.exists(path):
        raise FileNotFoundError(path)

    emb = np.load(path)

    if len(emb.shape) != 1:
        emb = emb.flatten()

    return emb.astype(np.float32)


# =========================
# 5. song 추천
# =========================
def recommend_songs(user_embedding, top_n=TOP_SONG_N):
    data = load_reference_metadata()
    results = []

    for item in data:
        try:
            emb = load_reference_embedding(item["embedding_file"])
            score = cosine_sim(user_embedding, emb)

            results.append({
                "title": item["title"],
                "artist": item["artist"],
                "score": round(score, 4)
            })

        except Exception as e:
            print(f"[SKIP] {item['title']}: {e}")

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


# =========================
# 6. artist 추천
# =========================
def recommend_artists(user_embedding, top_n=TOP_ARTIST_N):
    data = load_reference_metadata()

    artist_scores = defaultdict(list)
    artist_best = {}

    for item in data:
        try:
            emb = load_reference_embedding(item["embedding_file"])
            score = cosine_sim(user_embedding, emb)

            artist = item["artist"]

            artist_scores[artist].append(score)

            if artist not in artist_best or score > artist_best[artist][1]:
                artist_best[artist] = (item["title"], score)

        except Exception as e:
            print(f"[SKIP] {item['title']}: {e}")

    results = []

    for artist, scores in artist_scores.items():
        avg_score = np.mean(scores)
        best_song, best_score = artist_best[artist]

        results.append({
            "artist": artist,
            "score": round(float(avg_score), 4),
            "best_song": best_song,
            "song_count": len(scores)
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


# =========================
# 7. 전체 실행
# =========================
def run():
    print("[LOAD USER DATA]")
    user_embedding = load_user_session_embedding()

    songs = recommend_songs(user_embedding)
    artists = recommend_artists(user_embedding)

    return songs, artists


# =========================
# 8. 출력
# =========================
def print_result(songs, artists):

    print("\n==============================")
    print("🎵 추천 곡")
    print("==============================")

    for i, s in enumerate(songs, 1):
        print(f"{i}. {s['title']} - {s['artist']}")
        print(f"   - 점수 : {s['score']}")
        print("-" * 50)

    print("\n==============================")
    print("🎤 추천 가수")
    print("==============================")

    for i, a in enumerate(artists, 1):
        print(f"{i}. {a['artist']}")
        print(f"   - 점수 : {a['score']}")
        print(f"   - 대표곡 : {a['best_song']}")
        print(f"   - 곡 수 : {a['song_count']}")
        print("-" * 50)


# =========================
# 9. 실행
# =========================
if __name__ == "__main__":
    songs, artists = run()
    print_result(songs, artists)