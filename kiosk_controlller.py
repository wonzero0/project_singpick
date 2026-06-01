import threading
import sounddevice as sd
from scipy.io.wavfile import write
import os

SAMPLE_RATE = 44100

recording = False
audio_data = None
thread = None


def _record_loop():
    global audio_data, recording

    frames = []

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1) as stream:
        while recording:
            data, _ = stream.read(1024)
            frames.append(data)

    audio_data = frames


def start_recording():
    global recording, thread

    if recording:
        return

    recording = True
    thread = threading.Thread(target=_record_loop)
    thread.start()

    print("🎤 녹음 시작")


def stop_recording():
    global recording, audio_data

    recording = False

    if thread:
        thread.join()

    path = "temp.wav"
    audio = b"".join(audio_data)

    print("🎤 녹음 종료 -> 분석 시작")

    # 여기서 바로 AI 연결
    from ai_module.analyze_voice_final import analyzeVoice
    result = analyzeVoice(path)

    print(result)