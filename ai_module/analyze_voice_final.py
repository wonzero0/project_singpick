import os
import json
import librosa
import numpy as np
from ai_module.extract_basic_features import extract_single_wav
from ai_module.analyze_voice import analyze_voice
from ai_module.audio_utils import ensure_wav
from sklearn.metrics.pairwise import cosine_similarity

# ====== reference_songs.json 실제 위치 반영 ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # ai_module 폴더 기준
REFERENCE_FILE = os.path.join(BASE_DIR, "reference_songs.json")  # ai_module 안 reference_songs.json
# =================================================

TOP_N = 3  # Top-N 유사 가수 / 유사곡 계산

def analyzeVoice(wav_path):
    if not os.path.exists(wav_path):
        return {"error": "음성 파일이 존재하지 않습니다."}

    wav_path = ensure_wav(wav_path)

    # 1. feature 추출
    extract_single_wav(wav_path)
    voice_name = os.path.splitext(os.path.basename(wav_path))[0]
    feature_dir = os.path.join("features", voice_name)

    if not os.path.exists(feature_dir):
        return {"error": "feature 생성 실패"}

    analysis_result = analyze_voice(feature_dir=feature_dir)
    user_features = analysis_result["analysis_values"]
    user_timbre = np.array(analysis_result["timbre_vector"])

    # 2. 실제 BPM 계산
    try:
        y_full, sr_full = librosa.load(wav_path, sr=None)
        tempo = librosa.beat.beat_track(y=y_full, sr=sr_full)[0]
        tempo = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)
        user_features["tempo_bpm"] = tempo
    except Exception as e:
        print(f"[WARNING] BPM 계산 실패: {e}")
        user_features["tempo_bpm"] = 0.0

    rms = user_features.get("volume_rms_avg", 0.0)
    if rms < 0.01:
        return {"error": "음성이 거의 감지되지 않습니다."}

    # 3. reference_songs.json 로드
    if not os.path.exists(REFERENCE_FILE):
        return {"error": f"reference_songs.json 파일이 없습니다. 경로: {REFERENCE_FILE}"}

    with open(REFERENCE_FILE, "r", encoding="utf-8") as f:
        reference_db = json.load(f)

    # 4. 유사도 계산 + scores + 유사곡
    artist_scores = {}
    scores_aggregate = {"timbre": [], "pitch": [], "range": [], "tempo": [], "volume": []}
    similar_songs = []

    user_range = user_features["pitch_max"] - user_features["pitch_min"]

    for song_id, ref in reference_db.items():
        try:
            ref_timbre = np.array(ref["timbre_vector"])
            timbre_score = float(cosine_similarity([user_timbre], [ref_timbre])[0][0])

            # pitch
            pitch_diff = abs(user_features["pitch_hz_avg"] - ref["pitch_hz_avg"])
            pitch_score = max(0.0, 1 - pitch_diff / 200)

            # pitch range
            ref_range = ref["pitch_max"] - ref["pitch_min"]
            range_diff = abs(user_range - ref_range)
            range_score = max(0.0, 1 - range_diff / 2000)  # 2000Hz 기준

            # tempo
            tempo_diff = abs(user_features["tempo_bpm"] - ref["tempo_bpm"])
            tempo_score = max(0.0, 1 - tempo_diff / 60)

            # volume
            volume_diff = abs(user_features["volume_rms_avg"] - ref["volume_rms_avg"])
            volume_score = max(0.0, 1 - volume_diff / 0.5)

            # 최종 score (유사곡용)
            final_score = (
                timbre_score * 0.45 +
                pitch_score * 0.20 +
                range_score * 0.15 +
                tempo_score * 0.10 +
                volume_score * 0.10
            )
            final_score = min(final_score, 1.0)  # 1 이상 클리핑 방지

            # Top-N 가수 집계용: final_score 기준
            artist = ref.get("artist", "Unknown")
            artist_scores.setdefault(artist, []).append(final_score)

            # scores aggregate
            scores_aggregate["timbre"].append(timbre_score)
            scores_aggregate["pitch"].append(pitch_score)
            scores_aggregate["range"].append(range_score)
            scores_aggregate["tempo"].append(tempo_score)
            scores_aggregate["volume"].append(volume_score)

            # 유사곡 리스트 (title, artist, similarity만 포함)
            similar_songs.append({
                "song_id": song_id,
                "title": ref.get("title", song_id),
                "artist": artist,
                "similarity": round(final_score, 3)
            })

        except Exception as e:
            print(f"[WARNING] {song_id} 비교 실패: {e}")
            continue

    # 5. Top-N 유사곡
    similar_songs.sort(key=lambda x: x["similarity"], reverse=True)
    top_songs = similar_songs[:TOP_N]

    # 6. Top-N 가수 (곡 추천과 동일한 점수 기준)
    similar_artists = []
    for artist, scores in artist_scores.items():
        avg_score = np.mean(scores)
        similar_artists.append({
            "artist": artist,
            "similarity": round(avg_score, 3)
        })
    similar_artists.sort(key=lambda x: x["similarity"], reverse=True)
    top_artists = similar_artists[:TOP_N]

    # 7. 최종 scores 계산
    final_scores = {k: round(np.mean(v), 3) if v else 0.0 for k, v in scores_aggregate.items()}

    # 8. 피드백 생성
    feedback = []
    if top_artists:
        feedback.append(f"음색은 {', '.join([a['artist'] for a in top_artists])} 계열과 유사합니다.")
    if user_range < 300:
        feedback.append("고음 도달력이 조금 더 필요합니다.")
    if user_features.get("tempo_bpm", 0) < 60:
        feedback.append("템포 안정감을 조금 더 보완하면 완성도가 올라갑니다.")
    if rms < 0.08:
        feedback.append("성량 유지 연습이 필요합니다.")

    # ✅ 최종 반환
    return {
        "file": voice_name,
        "analysis_values": user_features,
        "timbre_vector": analysis_result["timbre_vector"],
        "scores": final_scores,
        "similar_artists": top_artists,
        "similar_songs": top_songs,
        "feedback": feedback
    }


if __name__ == "__main__":
    audio_dir = "audio"

    for file in os.listdir(audio_dir):
        if file.endswith((".wav", ".mp3", ".mp4", ".m4a", ".flac")):
            wav_path = os.path.join(audio_dir, file)
            print(f"\n[START] {file}")

            result = analyzeVoice(wav_path=wav_path)
            print(json.dumps(result, indent=4, ensure_ascii=False))
            print(f"[DONE] {file}")