import os
import time
import threading
import requests
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from ai_module.analyze_voice_final import analyzeVoice


# 2. DEVICE_ID를 모듈 로딩 시점에 고정합니다. (이게 핵심입니다)
def get_device_id():
    import sounddevice as sd
    devices = sd.query_devices()

    print("\n=== AUDIO DEVICES ===")
    for i, d in enumerate(devices):
        print(i, d["name"], d["max_input_channels"])

    # 1순위: USB 마이크
    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0:
            if "USB" in d["name"] or "Microphone" in d["name"]:
                print("SELECT USB MIC:", i)
                return i

    # 2순위: 실제 hardware input (중요)
    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0:
            if "sysdefault" not in d["name"].lower():
                print("SELECT NORMAL INPUT:", i)
                return i

    raise Exception("No valid mic device")

# =========================
# 서버 / 설정
# =========================
SERVER_URL = "http://192.168.0.251:8000"
USER_ID = "abc"

stop_flag = threading.Event()

analysis_threads = []
session_results = []
lock = threading.Lock()

SAMPLE_RATE = 44100
OUTPUT_DIR = "user_audio"


# =========================
# 상태 체크
# =========================
def check_session_finished():
    try:
        r = requests.get(f"{SERVER_URL}/session/status")
        data = r.json()

        return data.get("finished", False)
    except:
        return False


def wait_for_start(song_number):

    print("⏳ MR 시작 대기 중...")

    while True:

        try:
            res = requests.get(f"{SERVER_URL}/session/status")
            data = res.json()

            print(
                f"recording={data.get('recording')} "
                f"song={data.get('song')}"
            )

            if (
                data.get("recording")
                and data.get("song") == song_number
            ):
                print(f"🎤 {song_number}곡 녹음 시작")
                return True

        except Exception as e:
            print(e)

        time.sleep(0.2)


# =========================
# 녹음
# =========================
def record_audio(song_number):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"song_{song_number}.wav")

    device_id = get_device_id()   # 항상 여기서 결정

    print(f"🎤 using device_id = {device_id}")

    audio_data = []

    def callback(indata, frames, time_info, status):
        if status:
            print(status)
        audio_data.append(indata.copy())

    try:
        with sd.InputStream(
            device=device_id,
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            callback=callback
        ):
            while True:

                if stop_flag.is_set():
                    break

                if check_stop():
                    print("🛑 서버에서 녹음 종료")
                    break

                time.sleep(0.1)

    except Exception as e:
        print(f"❌ 녹음 실패: {e}")
        return None

    if not audio_data:
        return None

    audio = np.concatenate(audio_data, axis=0)
    write(path, SAMPLE_RATE, audio)

    print(f"✅ 녹음 완료: {path}")
    return path


# =========================
# 피드백
# =========================
def generate_feedback(a):
    pitch = a["pitch_hz_avg"]
    tempo = a["tempo_bpm"]
    volume = a["volume_rms_avg"]

    if pitch < 150:
        base = "저음 중심의 안정적인 보컬"
    elif pitch > 400:
        base = "고음이 돋보이는 밝은 보컬"
    else:
        base = "중음이 안정적인 균형 잡힌 보컬"

    if tempo < 90:
        rhythm = "템포가 다소 느린 편"
    elif tempo > 130:
        rhythm = "템포가 빠른 편"
    else:
        rhythm = "박자감이 안정적"

    if volume < 0.05:
        vol = "발성이 약한 편"
    elif volume > 0.2:
        vol = "발성이 강한 편"
    else:
        vol = "발성 밸런스가 좋음"

    return f"{base}이며 {rhythm}, {vol}입니다."


# =========================
# 곡 분석 (핵심)
# =========================
def analyze_song(wav_path):
    print(f"\n🧠 분석 시작: {wav_path}")

    try:
        result = analyzeVoice(wav_path)

        print("✅ analyzeVoice 성공")
        print(result)

        a = result["analysis_values"]

        recommendations = result.get("recommendations", [])
        similar_artists = result.get("similar_artists", [])

        pitch = a["pitch_hz_avg"]
        tempo = a["tempo_bpm"]
        volume = a["volume_rms_avg"]

        # =========================
        # 무음 처리
        # =========================
        if volume < 0.02:
            print("⚠️ 무음 감지 - 분석 제외")

            with lock:
                session_results.append({
                    "score": 0,
                    "pitch": pitch,
                    "tempo": tempo,
                    "volume": volume,
                    "feedback": "음성 감지 실패",
                    "artist": "없음",
                    "song": "없음",
                    "song_artist": "없음",
                    "is_silent": True
                })
            return

        # =========================
        # 점수 계산
        # =========================
        score = 55

        if volume > 0.01:
            score += 8
        else:
            score -= 10

        if 90 <= tempo <= 140:
            score += 15
        else:
            score -= 5

        if 80 <= pitch <= 800:
            score += 10
        else:
            score -= 10

        score = max(0, min(score, 100))

        top_song = recommendations[0] if recommendations else None
        top_artist = similar_artists[0] if similar_artists else "없음"

        # =========================
        # 저장
        # =========================
        with lock:
            session_results.append({
                "score": score,
                "pitch": pitch,
                "tempo": tempo,
                "volume": volume,
                "feedback": generate_feedback(a),
                "artist": top_artist,
                "song": top_song["title"] if top_song else "없음",
                "song_artist": top_song["artist"] if top_song else "없음",
                "is_silent": False
            })

        print(
            f"✅ 결과 저장 완료 "
            f"(현재 곡 수={len(session_results)})"
        )

        print("현재 저장 결과")
        print(session_results)

        # 서버 전송
        requests.post(
            f"{SERVER_URL}/result",
            json={
                "user_id": USER_ID,
                "score": score,
                "pitch": pitch,
                "tempo": tempo,
                "volume": volume,
                "feedback": generate_feedback(a),
                "artist": top_artist,
                "song": top_song["title"] if top_song else "없음"
            }
        )

    except Exception as e:
        print("❌ analyze_song 오류")
        print(e)

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


# =========================
# 최종 결과
# =========================
def finalize_session():

    valid_results = [r for r in session_results if not r.get("is_silent", False)]

    print("\n==============================")
    print("🏆 최종 노래방 결과")
    print("==============================")

    if not valid_results:
        print("\n🎯 최종 총점: 0점")
        print("\n📚 종합 음성 분석")
        print("- 음성이 감지되지 않아 데이터를 집계할 수 없습니다.")
        print("\n👤 전체 유사 가수 TOP 1\n- 없음")
        print("\n🎵 전체 추천곡 TOP 1\n- 없음")
        print("\n📝 종합 피드백\n- 음성이 감지되지 않아 분석할 수 없습니다.")
        print("\n🎉 전체 세션 완료")
        return

    total_score = sum(r["score"] for r in valid_results)
    total_pitch = sum(r["pitch"] for r in valid_results)
    total_tempo = sum(r["tempo"] for r in valid_results)
    total_volume = sum(r["volume"] for r in valid_results)

    final_score = round(total_score / len(valid_results))
    avg_pitch = round(total_pitch / len(valid_results), 2)
    avg_tempo = round(total_tempo / len(valid_results), 1)
    avg_volume = round(total_volume / len(valid_results), 4)

    print(f"\n🎯 최종 총점: {final_score}점")
    print("\n📚 종합 음성 분석")
    print(f"- 평균 피치: {avg_pitch} Hz")
    print(f"- 평균 템포: {avg_tempo} BPM")
    print(f"- 평균 볼륨: {avg_volume}")

    artist_count = {}
    for r in valid_results:
        if r["artist"] == "없음":
            continue
        artist_count[r["artist"]] = artist_count.get(r["artist"], 0) + 1

    top_artist = max(artist_count, key=artist_count.get) if artist_count else "없음"

    song_counter = {}
    for r in valid_results:
        if r["song"] == "없음":
            continue
        if r["song"] not in song_counter:
            song_counter[r["song"]] = {
                "count": 0,
                "artist": r["song_artist"]
            }
        song_counter[r["song"]]["count"] += 1

    if song_counter:
        top_song = max(song_counter, key=lambda x: song_counter[x]["count"])
        top_song_artist = song_counter[top_song]["artist"]
    else:
        top_song = "없음"
        top_song_artist = "없음"

    print(f"\n👤 전체 유사 가수 TOP 1\n- {top_artist}")
    print("\n🎵 전체 추천곡 TOP 1")
    if top_song == "없음":
        print("- 없음")
    else:
        print(f"- {top_song} ({top_song_artist})")

    print("\n📝 종합 피드백")
    print(f"- {generate_feedback({'pitch_hz_avg': avg_pitch, 'tempo_bpm': avg_tempo, 'volume_rms_avg': avg_volume})}")
    print("\n🎉 전체 세션 완료")

    try:
        requests.post(f"{SERVER_URL}/session/final_result", json={
            "final_score": final_score,
            "avg_pitch": avg_pitch,
            "avg_tempo": avg_tempo,
            "avg_volume": avg_volume,
            "top_artist": top_artist,
            "top_song": top_song
        })
    except Exception as e:
        print("FINAL RESULT SEND ERROR:", e)

def check_stop():
    try:
        r = requests.get(f"{SERVER_URL}/session/status")
        return not r.json()["recording"]
    except:
        return False

# =========================
# 실행
# =========================
def run_session():

    song_number = 1
    session_results.clear()

    while True:

        # ✅ 세션 종료 체크 추가
        if check_session_finished():
            print("🏁 세션 종료 감지")
            break

        started = wait_for_start(song_number)

        if not started:
            break

        wav_path = record_audio(song_number)

        if wav_path:
            t = threading.Thread(
                target=analyze_song,
                args=(wav_path,),
            )
            t.start()
            analysis_threads.append(t)

        song_number += 1

    for t in analysis_threads:
        t.join()

    finalize_session()


if __name__ == "__main__":
    run_session()


