import os
import json
import numpy as np
import librosa
import time

from ai_module.extract_basic_features import extract_single_wav
from ai_module.analyze_voice import analyze_voice
from ai_module.audio_utils import ensure_wav

from sklearn.metrics.pairwise import cosine_similarity
from resemblyzer import VoiceEncoder, preprocess_wav

REFERENCE_DATA = None
encoder = VoiceEncoder()


def cosine_sim(a, b):
    a = np.array(a).reshape(1, -1)
    b = np.array(b).reshape(1, -1)
    return float(cosine_similarity(a, b)[0][0])


def load_reference():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(BASE_DIR, "reference_songs.json")

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_embedding(path):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return np.load(os.path.join(BASE_DIR, "embedding_vectors", path)).flatten()


def recommend(user_embedding):

    preload_reference()

    results = []

    for item in REFERENCE_DATA:

        score = cosine_sim(
            user_embedding,
            item["embedding"]
        )

        results.append({
            "title": item["title"],
            "artist": item["artist"],
            "score": score
        })

    return sorted(
        results,
        key=lambda x: x["score"],
        reverse=True
    )[:10]


def analyzeVoice(wav_path):

    print("STEP1")

    wav_path = ensure_wav(wav_path)

    print("STEP2")

    voice_name = os.path.splitext(
        os.path.basename(wav_path)
    )[0]

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    feature_dir = os.path.join(
        BASE_DIR,
        "features",
        voice_name
    )

    print("STEP3")

    if os.path.exists(feature_dir):
        import shutil
        shutil.rmtree(feature_dir)

    print("STEP4")

    extract_single_wav(wav_path)

    print("STEP5")

    result = analyze_voice(
        feature_dir=feature_dir
    )

    print("STEP6")

    wav = preprocess_wav(wav_path)

    print("STEP7")
    print("START EMBEDDING")
    t = time.time()

    embedding = encoder.embed_utterance(wav)

    print("END EMBEDDING", time.time() - t)

    print("STEP8")

    y, sr = librosa.load(wav_path, sr=None)

    print("STEP9")

    tempo = librosa.beat.tempo(y=y, sr=sr)

    print("STEP10")

    bpm = float(tempo[0])

    result["analysis_values"]["tempo_bpm"] = bpm

    recs = recommend(embedding)

    return {
        "analysis_values": result["analysis_values"],
        "feedback": "분석 완료",
        "recommendations": recs,
        "similar_songs": recs,
        "similar_artists": list(set([r["artist"] for r in recs]))
    }

def preload_reference():

    global REFERENCE_DATA

    if REFERENCE_DATA is not None:
        return

    print("📦 Reference Loading...")

    data = load_reference()

    REFERENCE_DATA = []

    for item in data:

        try:
            REFERENCE_DATA.append({
                "title": item["title"],
                "artist": item["artist"],
                "embedding": load_embedding(
                    item["embedding_file"]
                )
            })

        except Exception as e:
            print(e)

    print(
        f"✅ Reference Loaded "
        f"({len(REFERENCE_DATA)} songs)"
    )

if __name__ == "__main__":

    print("MAIN START")

    result = analyzeVoice("user_audio/song_1.wav")

    print("RESULT DONE")
    print(result)