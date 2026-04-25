import os
import numpy as np
from collections import defaultdict

EMBEDDING_DIR = "embedding_vectors"
OUTPUT_DIR = "singer_db"

# =========================
# 가수 목록 (공백/표기 통일 버전)
# =========================
VALID_SINGERS = {
    "아이유",
    "태연",
    "한로로",
    "최유리",
    "헤이즈",
    "청하",
    "최예나",
    "백예린",
    "볼빨간사춘기",
    "비비",
    "에일리"
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

singer_vectors = defaultdict(list)

print("\n===== FINAL CLEAN (STRICT FILTER) =====")

# =========================
# 1. embedding 로드
# =========================
files = os.listdir(EMBEDDING_DIR)

if len(files) == 0:
    print("[ERROR] embedding_vectors 폴더가 비어있음")
    exit()

for file in files:

    if not file.endswith("_embedding.npy"):
        continue

    name = file.replace("_embedding.npy", "")

    # 가수_곡이름 구조 강제
    if "_" not in name:
        continue

    parts = name.split("_", 1)  # 🔥 핵심 수정 (곡명 '_' 안전 처리)

    singer = parts[0].strip()

    # =========================
    # 2. 가수 필터 (공백 제거 후 비교)
    # =========================
    singer_clean = singer.replace(" ", "")

    valid_match = None
    for v in VALID_SINGERS:
        if v.replace(" ", "") == singer_clean:
            valid_match = v
            break

    if valid_match is None:
        continue

    path = os.path.join(EMBEDDING_DIR, file)

    try:
        vec = np.load(path)
    except:
        continue

    singer_vectors[valid_match].append(vec)

# =========================
# 3. singer DB 생성
# =========================
total = 0

for singer, vecs in singer_vectors.items():

    if len(vecs) == 0:
        continue

    mean = np.mean(vecs, axis=0)

    np.save(os.path.join(OUTPUT_DIR, f"{singer}.npy"), mean)

    total += len(vecs)

    print(f"[SAVE] {singer}.npy ({len(vecs)}곡)")

print("\n===== DONE =====")
print("TOTAL SONGS:", total)
print("TOTAL SINGERS:", len(singer_vectors))