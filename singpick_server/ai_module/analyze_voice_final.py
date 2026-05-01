import os
import json
import numpy as np
import librosa

from ai_module.extract_basic_features import extract_single_wav
from ai_module.analyze_voice import analyze_voice
from ai_module.audio_utils import ensure_wav

from sklearn.metrics.pairwise import cosine_similarity
from resemblyzer import VoiceEncoder, preprocess_wav

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
    data = load_reference()
    results = []

    for item in data:
        try:
            emb = load_embedding(item["embedding_file"])
            score = cosine_sim(user_embedding, emb)

            results.append({
                "title": item["title"],
                "artist": item["artist"],
                "score": score
            })

        except Exception as e:
            print(f"[ERROR] {e}")
            continue

    return sorted(results, key=lambda x: x["score"], reverse=True)[:10]


def analyzeVoice(wav_path):

    wav_path = ensure_wav(wav_path)
    voice_name = os.path.splitext(os.path.basename(wav_path))[0]

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    feature_dir = os.path.join(BASE_DIR, "features", voice_name)

    if not os.path.exists(feature_dir):
        extract_single_wav(wav_path)

    result = analyze_voice(feature_dir=feature_dir)

    wav = preprocess_wav(wav_path)
    embedding = encoder.embed_utterance(wav)

    y, sr = librosa.load(wav_path, sr=None)
    tempo = librosa.beat.tempo(y=y, sr=sr)
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