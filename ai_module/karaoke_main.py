import os
import time
import threading
import requests
import sounddevice as sd
import numpy as np
import traceback
from scipy.io.wavfile import write
from ai_module.analyze_voice_final import analyzeVoice
import queue


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
SERVER_URL_CANDIDATES = [
    "http://192.168.0.236:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]
USER_ID = os.getenv("USER_ID", "GUEST")

def set_user_id(uid=None):
    global USER_ID
    USER_ID = uid if uid else "GUEST"

resolved_server_url = None
stop_flag = threading.Event()

session_results = []
analysis_queue = queue.Queue()
result_queue = queue.Queue()

SAMPLE_RATE = 44100
OUTPUT_DIR = os.path.abspath("user_audio")


def get_server_url():
    global resolved_server_url

    if resolved_server_url is not None:
        return resolved_server_url

    for url in SERVER_URL_CANDIDATES:
        try:
            r = requests.get(f"{url}/session/status", timeout=1.0)
            if r.status_code == 200:
                resolved_server_url = url
                print(f"✅ SERVER_URL resolved to {url}")
                return resolved_server_url
        except Exception:
            print(f"⚠️ SERVER_URL unreachable: {url}")

    raise ConnectionError(
        "No backend server available. Start the FastAPI server on one of: "
        + ", ".join(SERVER_URL_CANDIDATES)
    )


# =========================
# 상태 체크
# =========================
def check_session_finished():
    try:
        r = requests.get(f"{get_server_url()}/session/status")
        data = r.json()

        return data.get("session_active", True) is False
    except:
        return False

def check_session_active():
    try:
        r = requests.get(f"{get_server_url()}/session/status")
        data = r.json()
        return data.get("session_active", True)
    except:
        return False

def get_total_songs():

    try:
        r = requests.get(
            f"{get_server_url()}/session/status"
        )

        return r.json().get(
            "total_songs",
            1
        )

    except:
        return 1


def wait_for_start(song_number):

    print("⏳ MR 시작 대기 중...")

    while True:
        try:
            res = requests.get(f"{get_server_url()}/session/status")
            data = res.json()

            recording = data.get("recording")
            song = data.get("song")
            session_active = data.get("session_active")

            print(f"recording={recording} song={song}")

            if session_active is False:
                print("🏁 세션 종료 감지")
                return False

            if song == song_number and recording:
                print(f"🎤 {song_number}곡 시작")
                return True

            if song == song_number and not recording:
                print(f"🎤 {song_number}곡 대기 중... 녹음 신호 대기")

        except Exception as e:
            print("status error:", e)

        time.sleep(0.2)


# =========================
# 녹음
# =========================
def record_audio(song_number, start_immediately=False):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"song_{song_number}.wav")

    device_id = get_device_id()   # 항상 여기서 결정

    print(f"🎤 using device_id = {device_id}")

    if not start_immediately:
        while True:
            try:
                res = requests.get(f"{get_server_url()}/session/status")
                data = res.json()
                if data.get("song") == song_number and data.get("recording"):
                    break
                if not data.get("session_active", True):
                    print("🏁 세션 종료 감지, 녹음 중지")
                    return None
                print(f"🎤 녹음 시작 대기 중 ({song_number}곡) ...")
            except Exception as e:
                print("status error while waiting for record start:", e)
            time.sleep(0.1)

    audio_data = []

    def callback(indata, frames, time_info, status):
        if status:
            print(status)
        audio_data.append(indata.copy())

    print(f"🎤 record_audio thread 시작: song={song_number}, start_immediately={start_immediately}")

    attempt = 0
    while True:
        try:
            with sd.InputStream(
                device=device_id,
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                callback=callback
            ):
                print(f"🎤 InputStream 열림: song={song_number}")
                while True:
                    if stop_flag.is_set():
                        break

                    if check_stop():
                        print("🛑 서버에서 녹음 종료")
                        break

                    if not check_session_active():
                        break

                    time.sleep(0.1)
            break

        except Exception as e:
            attempt += 1
            print(f"❌ InputStream 열기 실패 (attempt {attempt}): {e}")
            if attempt >= 10:
                print("❌ 녹음 장치 열기 재시도 한계 도달")
                return None
            if not check_session_active():
                print("🏁 세션이 비활성화되어 녹음 재시도를 중단합니다")
                return None
            time.sleep(0.2)

    if not audio_data:
        print(f"⚠️ 녹음 데이터 없음: {path}")
        return None

    audio = np.concatenate(audio_data, axis=0)
    write(path, SAMPLE_RATE, audio)

    print(f"✅ 녹음 완료: {path}")
    analysis_queue.put(path)
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


def result_collector():
    print("📥 result_collector started")

    while True:

        result = result_queue.get()

        if result == "STOP":
            print("🛑 collector 종료")
            break

        session_results.append(result)

        print("✅ Queue 결과 수신")
        print(result)

        try:
            requests.post(
                f"{get_server_url()}/result",
                json={
                    "user_id": USER_ID,
                    "score": result["score"],
                    "pitch": result["pitch"],
                    "tempo": result["tempo"],
                    "volume": result["volume"],
                    "feedback": result["feedback"],
                    "artist": result["artist"],
                    "song": result["song"]
                }
            )

            print("📤 서버 전송 완료")

        except Exception as e:
            print("SERVER SEND ERROR:", e)


# =========================
# 곡 분석 (핵심)
# =========================
def analyze_song(wav_path, result_queue):

    print(f"\n🧠 분석 시작: {wav_path}")

    try:
        print("STEP1")

        result = analyzeVoice(wav_path)

        print("STEP2")
        print(type(result))
        print(result)

        a = result["analysis_values"]

        recommendations = result.get("recommendations", [])
        similar_artists = result.get("similar_artists", [])

        pitch = a["pitch_hz_avg"]
        tempo = a["tempo_bpm"]
        volume = a["volume_rms_avg"]

        # 무음 처리
        if volume < 0.02:
            result_queue.put({
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

        # 점수 계산
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

        result_queue.put({
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

        print("✅ Queue 전송 완료")

    except Exception:
        with open("process_error.log", "a", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        print("❌ process_error.log 확인")

    finally:
        try:
            abs_path = os.path.abspath(wav_path)
            print(f"🗑 삭제 시도: {abs_path}")
            if os.path.exists(abs_path):
                os.remove(abs_path)
                print(f"🗑 삭제 완료: {abs_path}")
            else:
                print(f"⚠️ 삭제 대상 없음: {abs_path}")
        except Exception as e:
            print("❌ wav 삭제 실패", e)

# =========================
# 🔥 분석 워커 (추가)
# =========================
def analysis_worker():
    print("🧠 analysis_worker started")
    while True:
        wav_path = analysis_queue.get()
        print(f"🧠 analysis_worker received: {wav_path}")

        if wav_path == "STOP":
            print("🛑 analysis_worker 종료")
            break

        analyze_song(wav_path, result_queue)


# =========================
# 최종 결과
# =========================
def finalize_session():

    valid_results = [r for r in session_results if not r.get("is_silent", False)]
    print(f"📊 수집된 결과 개수: {len(session_results)} (유효 {len(valid_results)})")

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

        # 무음 감지 시에도 최종 결과 전송
        try:
            requests.post(
                f"{get_server_url()}/session/final_result",
                json={
                    "final_score": 0,
                    "avg_pitch": 0,
                    "avg_tempo": 0,
                    "avg_volume": 0,
                    "top_artist": "없음",
                    "top_song": "없음",
                    "feedback": "음성이 감지되지 않아 분석할 수 없습니다."
                }
            )
            print("📤 무음 최종 결과 서버 전송 완료")
        except Exception as e:
            print("FINAL RESULT SEND ERROR (SILENT):", e)
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
        final_feedback = generate_feedback({
            "pitch_hz_avg": avg_pitch,
            "tempo_bpm": avg_tempo,
            "volume_rms_avg": avg_volume
        })

        requests.post(
            f"{get_server_url()}/session/final_result",
            json={
                "final_score": final_score,
                "avg_pitch": avg_pitch,
                "avg_tempo": avg_tempo,
                "avg_volume": avg_volume,
                "top_artist": top_artist,
                "top_song": top_song,
                "feedback": final_feedback
            }
        )

    
    except Exception as e:
        print("FINAL RESULT SEND ERROR:", e)

def check_stop():
    try:
        r = requests.get(f"{get_server_url()}/session/status")
        return not r.json()["recording"]
    except:
        return False

# =========================
# 실행
# =========================
def run_session():

    session_results.clear()
    total_songs = get_total_songs()

    # 분석 워커는 별도 스레드로 실행하여 프로세스 간 큐/포크 문제를 제거합니다.
    analysis_thread = threading.Thread(target=analysis_worker, daemon=False)
    analysis_thread.start()

    collector_thread = threading.Thread(target=result_collector, daemon=False)
    collector_thread.start()

    active_recordings = []
    active_recording_song = None
    last_recording = None
    last_song = None

    while True:
        if check_session_finished():
            print("🏁 세션 종료 감지")
            break

        try:
            res = requests.get(f"{get_server_url()}/session/status")
            status = res.json()
        except Exception as e:
            print("status poll error:", e)
            time.sleep(0.2)
            continue

        recording = status.get("recording", False)
        song = status.get("song", 0)
        session_active = status.get("session_active", True)

        if song != last_song or recording != last_recording:
            print(f"🔁 status update: song={song}, recording={recording}, active_recording_song={active_recording_song}")
            last_song = song
            last_recording = recording

        if not session_active:
            print("🏁 세션 inactive 감지")
            break

        if recording and active_recording_song != song:
            print(f"🎤 녹음 시작 이벤트 감지: song={song}")
            active_recording_song = song

            recording_thread = threading.Thread(
                target=record_audio,
                args=(song, True),
                daemon=False
            )
            active_recordings.append(recording_thread)
            recording_thread.start()

        if not recording and active_recording_song is not None:
            print(f"🎤 녹음 종료 이벤트 감지: song={song}")
            active_recordings = [t for t in active_recordings if t.is_alive()]
            active_recording_song = None

        time.sleep(0.1)

    for recording_thread in active_recordings:
        if recording_thread.is_alive():
            recording_thread.join()

    # 분석 워커 중지 신호 전송 및 종료 대기
    analysis_queue.put("STOP")
    analysis_thread.join()

    # 결과 수집기 중지 신호 전송 및 종료 대기
    result_queue.put("STOP")
    collector_thread.join()

    finalize_session()


if __name__ == "__main__":
    run_session()