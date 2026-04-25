import os
import sounddevice as sd
import scipy.io.wavfile as wav

from extract_user_features import extract_user_features
from analyze_voice_total import analyze_voice_total
from extract_user_embedding import extract_user_embedding
from make_user_session_embedding import make_user_session_embedding
from recommend_by_similarity import recommend_by_similarity
import karaoke_scoring


# =========================
# 설정
# =========================
AUDIO_DIR = "user_audio"
SR = 22050

os.makedirs(AUDIO_DIR, exist_ok=True)


# =========================
# 🎤 실제 마이크 녹음
# =========================
def record_audio(song_id, duration=10):
    print(f"\n🎤 녹음 시작: {song_id} ({duration}초)")

    audio = sd.rec(
        int(duration * SR),
        samplerate=SR,
        channels=1,
        dtype="float32"
    )

    sd.wait()

    wav_path = os.path.join(AUDIO_DIR, f"{song_id}.wav")
    wav.write(wav_path, SR, audio)

    print(f"✅ 저장 완료: {wav_path}")

    return wav_path


# =========================
# 🎵 1곡 처리 파이프라인
# =========================
def process_song(song_id):

    wav_path = record_audio(song_id)

    print(f"🔧 feature 추출: {song_id}")
    feature = extract_user_features(wav_path)

    print(f"🧠 음성 분석: {song_id}")
    analysis = analyze_voice_total(feature)

    print(f"🧬 embedding 생성: {song_id}")
    embedding = extract_user_embedding(feature)

    return embedding, analysis


# =========================
# 🎤 메인 실행
# =========================
def run():

    print("\n🎤 라즈베리파이 노래방 시스템 시작\n")

    song_ids = ["song1", "song2", "song3"]

    embeddings = []
    analyses = []

    # 🎵 1~3곡 반복 처리
    for i, sid in enumerate(song_ids, 1):

        emb, ana = process_song(sid)

        embeddings.append(emb)
        analyses.append(ana)

        print(f"🎵 {i}곡 완료: {sid}")

    # 👤 사용자 평균 음색
    print("\n👤 사용자 평균 음색 생성")
    user_embedding = make_user_session_embedding(embeddings)

    # 🎯 추천
    print("\n🎯 가수/곡 추천 실행")
    recommend_by_similarity(user_embedding)

    # 🎤 최종 점수 (TJ 스타일)
    print("\n🎤 최종 점수 출력")
    karaoke_scoring.run(analyses)


# =========================
# 실행
# =========================
if __name__ == "__main__":
    run()