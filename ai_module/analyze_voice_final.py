import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from core.ai_engine import get_vocal_feedback, get_similarity_based_feedback

# ====== reference_songs.json 실제 위치 반영 ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCE_FILE = os.path.join(BASE_DIR, "reference_songs.json")
# =================================================

TOP_N = 3  # Top-N 유사 가수 / 유사곡 계산


def analyzeVoice(wav_path, user_bpm=120.0, reference_song="No_Doubt"):
    if not os.path.exists(wav_path):
        return {"error": "음성 파일이 존재하지 않습니다."}

    print(f"[System] 분석 시작 - 곡명: {reference_song}, 설정 BPM: {user_bpm}")

    # ------------------------------------------------------------------
    # AI 음성 분석 모듈(librosa, extract_basic_features, analyze_voice 등)은
    # 지금 잠시 비활성화한 상태.
    # 서버가 안 터지도록 더미 분석값으로만 동작하게 만든 버전.
    # ------------------------------------------------------------------

    voice_name = os.path.splitext(os.path.basename(wav_path))[0]

    user_features = {
        "pitch_max": 0.0,
        "pitch_min": 0.0,
        "pitch_hz_avg": 0.0,
        "tempo_bpm": float(user_bpm),
        "volume_rms_avg": 0.1,
    }

    user_timbre = np.zeros(10)

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
            ref_timbre = np.array(ref.get("timbre_vector", [0.0] * 10))

            # timbre similarity
            timbre_score = float(cosine_similarity([user_timbre], [ref_timbre])[0][0])

            # pitch
            pitch_diff = abs(user_features["pitch_hz_avg"] - ref.get("pitch_hz_avg", 0.0))
            pitch_score = max(0.0, 1 - pitch_diff / 200)

            # pitch range
            ref_range = ref.get("pitch_max", 0.0) - ref.get("pitch_min", 0.0)
            range_diff = abs(user_range - ref_range)
            range_score = max(0.0, 1 - range_diff / 2000)

            # tempo
            tempo_diff = abs(user_features["tempo_bpm"] - ref.get("tempo_bpm", 0.0))
            tempo_score = max(0.0, 1 - tempo_diff / 60)

            # volume
            volume_diff = abs(user_features["volume_rms_avg"] - ref.get("volume_rms_avg", 0.0))
            volume_score = max(0.0, 1 - volume_diff / 0.5)

            final_score = (
                timbre_score * 0.45
                + pitch_score * 0.20
                + range_score * 0.15
                + tempo_score * 0.10
                + volume_score * 0.10
            )
            final_score = min(final_score, 1.0)

            artist = ref.get("artist", "Unknown")
            artist_scores.setdefault(artist, []).append(final_score)

            scores_aggregate["timbre"].append(timbre_score)
            scores_aggregate["pitch"].append(pitch_score)
            scores_aggregate["range"].append(range_score)
            scores_aggregate["tempo"].append(tempo_score)
            scores_aggregate["volume"].append(volume_score)

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

    # 6. Top-N 가수
    similar_artists = []
    for artist, scores in artist_scores.items():
        avg_score = np.mean(scores)
        similar_artists.append({
            "artist": artist,
            "similarity": round(float(avg_score), 3)
        })
    similar_artists.sort(key=lambda x: x["similarity"], reverse=True)
    top_artists = similar_artists[:TOP_N]

    # 7. 최종 scores 계산
    final_scores = {k: round(float(np.mean(v)), 3) if v else 0.0 for k, v in scores_aggregate.items()}
    print(f"[System] 점수 계산 완료: {final_scores}")

    rms = user_features.get("volume_rms_avg", 0.0)

    print("[System] 제미나이 AI 피드백 생성 중... (잠시만 기다려주세요)")
    try:
        ai_feedback = get_vocal_feedback(
            pitch_score=final_scores["pitch"] * 100,
            tempo_score=final_scores["tempo"] * 100,
            avg_volume=rms * 100,
        )
        print("[System] 제미나이 피드백 생성 완료!")
    except Exception as e:
        print(f"[Error] 제미나이 피드백 생성 실패: {e}")
        ai_feedback = "AI 피드백을 생성할 수 없습니다."

    if top_artists:
        top_singer = top_artists[0]["artist"]
        top_sim = top_artists[0]["similarity"] * 100
        try:
            similarity_feedback = get_similarity_based_feedback(top_singer, top_sim)
        except Exception as e:
            print(f"[Error] 유사도 기반 피드백 생성 실패: {e}")
            similarity_feedback = "유사도 기반 피드백을 생성할 수 없습니다."
    else:
        similarity_feedback = "유사한 아티스트를 찾을 수 없습니다."

    # 8. 간단 피드백 생성
    feedback = []
    if top_artists:
        feedback.append(f"음색은 {', '.join([a['artist'] for a in top_artists])} 계열과 유사합니다.")
    if user_range < 300:
        feedback.append("고음 도달력이 조금 더 필요합니다.")
    if user_features.get("tempo_bpm", 0) < 60:
        feedback.append("템포 안정감을 조금 더 보완하면 완성도가 올라갑니다.")
    if rms < 0.08:
        feedback.append("성량 유지 연습이 필요합니다.")

    simple_tips = "\n".join(feedback) if feedback else "분석된 추가 팁이 없습니다."

    return {
        "file": voice_name,
        "analysis_values": user_features,
        "timbre_vector": user_timbre.tolist(),
        "scores": final_scores,
        "similar_artists": top_artists,
        "similar_songs": top_songs,
        "feedback": f"{ai_feedback}\n\n{similarity_feedback}\n\n[추가 가이드]\n{simple_tips}",
    }


if __name__ == "__main__":
    audio_dir = "audio"

    if os.path.exists(audio_dir):
        for file in os.listdir(audio_dir):
            if file.endswith((".wav", ".mp3", ".mp4", ".m4a", ".flac")):
                wav_path = os.path.join(audio_dir, file)
                print(f"\n[START] {file}")

                result = analyzeVoice(wav_path=wav_path)
                print(json.dumps(result, indent=4, ensure_ascii=False))
                print(f"[DONE] {file}")
    else:
        print("audio 폴더가 없습니다.")