import os
import subprocess

def ensure_wav(input_path: str) -> str:
    """
    입력 파일이 wav가 아니면 wav로 변환해서 경로를 반환
    wav면 그대로 반환
    """
    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".wav":
        return input_path

    output_path = os.path.splitext(input_path)[0] + ".wav"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        output_path
    ]

    subprocess.run(command, check=True)
    return output_path