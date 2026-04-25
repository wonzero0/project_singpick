import os
import json

EMBEDDING_DIR = "embedding_vectors"
OUTPUT_JSON = "reference_songs.json"

reference_list = []

for file in os.listdir(EMBEDDING_DIR):
    if not file.endswith("_recommend_embedding.npy"):
        continue

    # 파일명 예: 아이유_Blueming_recommend_embedding.npy
    base = file.replace("_recommend_embedding.npy", "")

    parts = base.split("_")

    if len(parts) < 2:
        print(f"[SKIP] 형식 이상: {file}")
        continue

    singer = parts[0]                      # 가수
    song = "_".join(parts[1:])             # 곡명 복원

    # 혹시 남아있으면 제거 (안전 처리)
    song = song.replace("_recommend", "")

    reference_list.append({
        "title": song,
        "artist": singer,
        "embedding_file": file
    })

    print(f"[ADD] {singer} - {song}")

# JSON 저장
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(reference_list, f, ensure_ascii=False, indent=2)

print("\n===================================")
print("[DONE] reference_songs.json 생성 완료")
print(f"[INFO] 총 곡 수: {len(reference_list)}")
print("===================================")