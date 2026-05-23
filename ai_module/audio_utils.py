import os
from pydub import AudioSegment


def ensure_wav(input_path, output_dir=None):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"{input_path} 파일이 존재하지 않습니다.")

    # 🔥 기준 경로 (ai_module 기준)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # 🔥 output_dir 기본값을 ai_module 내부로 설정
    if output_dir is None:
        output_dir = os.path.join(BASE_DIR, "converted_audio")

    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.wav")

    ext = os.path.splitext(input_path)[1].lower()

    # 이미 wav면 그대로 사용
    if ext == ".wav":
        return input_path

    # 변환
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio.export(output_path, format="wav")

    return output_path