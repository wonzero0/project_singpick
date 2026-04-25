import json
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from sklearn.manifold import TSNE
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from collections import defaultdict
import warnings
import sys

warnings.filterwarnings("ignore")

# =========================
# matplotlib 설정
# =========================
matplotlib.use('TkAgg')
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# =========================
# 경로
# =========================
EMBEDDING_DIR = "embedding_vectors"
USER_EMBEDDING_DIR = "user_embedding_vectors"
REFERENCE_JSON = "reference_songs.json"   # 🔥 여기 수정됨

TOP_K = 5
N_CLUSTERS = 4

# =========================
# 1. JSON 로드
# =========================
with open(REFERENCE_JSON, "r", encoding="utf-8") as f:
    reference_data = json.load(f)

# =========================
# 2. embedding + metadata 로드
# =========================
song_vectors = []
song_names = []

for item in reference_data:
    path = os.path.join(EMBEDDING_DIR, item["embedding_file"])

    if not os.path.exists(path):
        print(f"[WARNING] missing file: {path}")
        continue

    vec = np.load(path)

    if vec is None or len(vec) == 0:
        continue

    song_vectors.append(vec)
    song_names.append(f'{item["artist"]} - {item["title"]}')

song_vectors = np.array(song_vectors)

if len(song_vectors) < 5:
    raise ValueError("embedding 데이터가 너무 적습니다 (최소 5개 이상 필요)")

print(f"총 곡 수: {len(song_vectors)}")
sys.stdout.flush()

# =========================
# 3. 사용자 벡터
# =========================
user_files = [
    os.path.join(USER_EMBEDDING_DIR, f)
    for f in os.listdir(USER_EMBEDDING_DIR)
    if f.endswith(".npy")
]

user_vectors = np.array([np.load(f) for f in user_files])
user_vector = np.mean(user_vectors, axis=0)

print(f"사용자 음성 개수: {len(user_vectors)}")
sys.stdout.flush()

# =========================
# 4. 추천
# =========================
similarities = cosine_similarity(user_vector.reshape(1, -1), song_vectors)[0]
top_indices = np.argsort(similarities)[-TOP_K:][::-1]

print("\n===== 🎧 추천 결과 =====")
for i, idx in enumerate(top_indices):
    print(f"{i+1}. {song_names[idx]} ({similarities[idx]:.4f})")

sys.stdout.flush()

# =========================
# 5. KMeans
# =========================
kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(song_vectors)

user_cluster = kmeans.predict(user_vector.reshape(1, -1))[0]
print(f"\n⭐ USER 클러스터: {user_cluster}")
sys.stdout.flush()

# =========================
# 6. 클러스터 그룹
# =========================
cluster_songs = defaultdict(list)

for i, name in enumerate(song_names):
    cluster_songs[cluster_labels[i]].append(name)

# =========================
# 7. 음색 라벨
# =========================
pca = PCA(n_components=2)
pca_result = pca.fit_transform(song_vectors)

cluster_score = {
    c: np.mean(pca_result[cluster_labels == c, 0])
    for c in range(N_CLUSTERS)
}

sorted_clusters = sorted(cluster_score.items(), key=lambda x: x[1], reverse=True)

tone_labels = [
    "감성적 / 부드러운 음색",
    "따뜻 / 안정적인 음색",
    "중립 / 밸런스 음색",
    "파워풀 / 강한 음색"
]

cluster_to_label = {}
for i, (c, _) in enumerate(sorted_clusters):
    cluster_to_label[c] = tone_labels[i]

# =========================
# 8. 클러스터 출력
# =========================
print("\n===== 🎨 클러스터 음색 + 곡 리스트 =====")

for c in range(N_CLUSTERS):
    print(f"\n[{cluster_to_label[c]}]")
    for s in cluster_songs[c]:
        print("-", s)

sys.stdout.flush()

# =========================
# 9. t-SNE (안정화)
# =========================
all_vec = np.vstack([song_vectors, user_vector])

perplexity = min(10, len(song_vectors) - 1)

tsne = TSNE(
    n_components=2,
    random_state=42,
    perplexity=perplexity
)

tsne_result = tsne.fit_transform(all_vec)

song_tsne = tsne_result[:-1]
user_tsne = tsne_result[-1]

# =========================
# 10. 시각화
# =========================
plt.figure(figsize=(11, 8))

colors = ['red', 'blue', 'green', 'purple']

# 곡
for i in range(len(song_tsne)):
    plt.scatter(
        song_tsne[i, 0],
        song_tsne[i, 1],
        color=colors[cluster_labels[i] % len(colors)],
        alpha=0.6
    )

# 추천 강조
for idx in top_indices:
    x, y = song_tsne[idx]
    plt.scatter(x, y, color='yellow', edgecolors='black', s=160)
    plt.text(x, y, song_names[idx], fontsize=9)

# USER
plt.scatter(
    user_tsne[0],
    user_tsne[1],
    color='black',
    marker='*',
    s=300
)

# 범례
from matplotlib.lines import Line2D

legend_elements = [
    Line2D([0], [0], marker='o', color='w',
           label=cluster_to_label[i],
           markerfacecolor=colors[i],
           markersize=10)
    for i in range(N_CLUSTERS)
]

legend_elements.append(
    Line2D([0], [0], marker='*', color='w',
           label='USER',
           markerfacecolor='black',
           markersize=15)
)

plt.legend(handles=legend_elements, loc='lower right')

plt.title("Voice Similarity (t-SNE + Cluster Tone Map)")
plt.grid(True)

plt.savefig("tsne_result.png", dpi=300)
plt.show()

input("그래프 확인 후 엔터 누르면 종료...")