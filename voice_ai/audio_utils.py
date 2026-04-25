import os
from pydub import AudioSegment

def ensure_wav(input_path, output_dir="converted_audio"):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"{input_path} 파일이 존재하지 않습니다.")

    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.wav")

    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".wav":
        return input_path

    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio.export(output_path, format="wav")

    return output_path