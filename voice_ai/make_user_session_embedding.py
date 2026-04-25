import os
import numpy as np

# =========================
# 설정
# =========================
USER_EMBEDDING_DIR = "user_embedding_vectors"
OUTPUT_PATH = "user_session_embedding.npy"

# =========================
# 사용자 임베딩 불러오기
# =========================
if not os.path.exists(USER_EMBEDDING_DIR):
    raise FileNotFoundError(f"[ERROR] 폴더가 없습니다: {USER_EMBEDDING_DIR}")

user_embeddings = []
user_files = []

for file in os.listdir(USER_EMBEDDING_DIR):
    if file.endswith(".npy"):
        file_path = os.path.join(USER_EMBEDDING_DIR, file)

        try:
            emb = np.load(file_path)

            if emb.shape == (256,):
                user_embeddings.append(emb)
                user_files.append(file)
            else:
                print(f"[WARNING] shape 이상 제외: {file} / shape={emb.shape}")

        except Exception as e:
            print(f"[WARNING] 로드 실패: {file} / {e}")

# =========================
# 예외 처리
# =========================
if len(user_embeddings) == 0:
    raise ValueError("[ERROR] 사용자 임베딩이 하나도 없습니다.")

user_embeddings = np.array(user_embeddings)

print(f"[INFO] 사용자 임베딩 개수: {len(user_files)}")
print("\n[DEBUG] 평균에 사용된 파일 목록:")
for uf in user_files:
    print(" -", uf)

# =========================
# 평균 세션 벡터 생성
# =========================
user_session_embedding = np.mean(user_embeddings, axis=0)

print(f"\n[INFO] 평균 세션 벡터 생성 완료")
print(f"[INFO] 벡터 shape: {user_session_embedding.shape}")

# =========================
# 저장
# =========================
np.save(OUTPUT_PATH, user_session_embedding)

print(f"[DONE] 저장 완료: {OUTPUT_PATH}")