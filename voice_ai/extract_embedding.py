import os
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav

AUDIO_DIR = "audio"
OUTPUT_DIR = "embedding_vectors"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("[MODEL LOAD]")
encoder = VoiceEncoder()
print("[READY]\n")


def parse(filename):
    name = filename.replace(".wav", "")
    parts = name.split("_")

    if len(parts) < 2:
        return None, None  # ❗ 무조건 버림

    singer = parts[0]
    song = "_".join(parts[1:])

    return singer, song


def process():
    files = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".wav")]

    print("\n===== START =====\n")

    total = 0

    for f in files:
        singer, song = parse(f)

        if singer is None:
            print(f"[SKIP INVALID] {f}")
            continue

        path = os.path.join(AUDIO_DIR, f)

        try:
            wav = preprocess_wav(path)
            emb = encoder.embed_utterance(wav)

            save_name = f"{singer}_{song}_embedding.npy"
            save_path = os.path.join(OUTPUT_DIR, save_name)

            np.save(save_path, emb)

            print(f"[SAVE] {save_name}")
            total += 1

        except Exception as e:
            print(f"[ERROR] {f}: {e}")

    print("\n===== DONE =====")
    print("TOTAL:", total)


if __name__ == "__main__":
    process()