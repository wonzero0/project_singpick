import os
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav

# =========================
# 경로 설정
# =========================
USER_SEGMENT_DIR = "user_segments"
USER_EMBEDDING_DIR = "user_embedding_vectors"

os.makedirs(USER_EMBEDDING_DIR, exist_ok=True)

# =========================
# 모델 로드
# =========================
print("[MODEL LOAD] Resemblyzer VoiceEncoder 로딩 중...")
encoder = VoiceEncoder()
print("[MODEL READY] 모델 로딩 완료")


# =========================
# 1. 전체 자동 embedding + 평균
# =========================
def extract_all_user_embeddings():

    embeddings = []
    file_list = []

    # 🎯 user_segments 전체 자동 탐색
    for file in os.listdir(USER_SEGMENT_DIR):
        if file.endswith(".wav"):
            file_path = os.path.join(USER_SEGMENT_DIR, file)

            print(f"[LOAD] {file}")

            try:
                wav = preprocess_wav(file_path)
                embedding = encoder.embed_utterance(wav)

                # 저장
                save_path = os.path.join(
                    USER_EMBEDDING_DIR,
                    file.replace(".wav", "_embedding.npy")
                )

                np.save(save_path, embedding)

                embeddings.append(embedding)
                file_list.append(file)

                print(f"[SAVE] {save_path}")

            except Exception as e:
                print(f"[ERROR] {file}: {e}")

    # =========================
    # 2. 평균 embedding 생성
    # =========================
    if len(embeddings) == 0:
        print("[ERROR] 처리된 파일 없음")
        return False

    final_embedding = np.mean(embeddings, axis=0)

    np.save("user_session_embedding.npy", final_embedding)

    print("\n[COMPLETE]")
    print(f"✔ 처리 개수: {len(embeddings)}")
    print("✔ 평균 embedding 저장 완료 → user_session_embedding.npy")

    return True


# =========================
# 2. 실행
# =========================
if __name__ == "__main__":
    print("\n[START] 전체 사용자 음성 자동 처리 시작\n")

    ok = extract_all_user_embeddings()

    if ok:
        print("\n[완료] 6개(또는 전체) 자동 embedding + 평균 생성 성공")
    else:
        print("\n[실패] 처리 실패")