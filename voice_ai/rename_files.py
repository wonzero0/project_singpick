import os
import json

EMBEDDING_DIR = "embedding_vectors"
JSON_PATH = "reference_songs.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# {파일명: 가수} 매핑
file_to_singer = {}

for item in data:
    file_name = item["embedding_file"]
    singer = item["artist"]  # ✅ 여기 수정됨

    base = file_name.replace("_recommend_embedding.npy", "")
    file_to_singer[base] = singer

# 파일 이름 변경
for file in os.listdir(EMBEDDING_DIR):
    if not file.endswith(".npy"):
        continue

    old_path = os.path.join(EMBEDDING_DIR, file)

    base = file.replace("_recommend_embedding.npy", "")

    if base not in file_to_singer:
        print(f"[SKIP] 매칭 없음: {base}")
        continue

    singer = file_to_singer[base]

    new_name = f"{singer}_{base}_recommend_embedding.npy"
    new_path = os.path.join(EMBEDDING_DIR, new_name)

    os.rename(old_path, new_path)
    print(f"[RENAME] {file} → {new_name}")

print("\n[완료] 파일 이름 변경 완료")