import numpy as np
import json
import os

# =========================
# 1. 경로
# =========================
EMBEDDING_PATH = "user_session_embedding.npy"
OUTPUT_PATH = "results/analysis_result.json"

os.makedirs("results", exist_ok=True)

# =========================
# 2. embedding 로드
# =========================
if not os.path.exists(EMBEDDING_PATH):
    print("[ERROR] user_session_embedding.npy 없음")
    exit()

embedding = np.load(EMBEDDING_PATH)

print("[LOAD] embedding shape:", embedding.shape)

# =========================
# 3. JSON 변환 (numpy → list)
# =========================
result = {
    "user_session_embedding": embedding.tolist()
}

# =========================
# 4. 저장
# =========================
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=4, ensure_ascii=False)

print("[SUCCESS] analysis_result.json 생성 완료")