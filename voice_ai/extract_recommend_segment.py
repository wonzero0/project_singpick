import os
import numpy as np
import librosa
import soundfile as sf

SR = 22050

AUDIO_DIR = "audio"
TEMP_DIR = "temp"
RECOMMEND_DIR = "recommend_segments"

os.makedirs(RECOMMEND_DIR, exist_ok=True)


# =========================
# 0. 곡 이름 추출
# =========================
def get_song_base_name(vocals_path):
    """
    temp/htdemucs/A_good_day/vocals.mp3
    -> A_good_day 추출
    """
    parent_dir = os.path.basename(os.path.dirname(vocals_path))

    if parent_dir.lower() == "htdemucs":
        return "unknown_song"

    return parent_dir


# =========================
# 1. 보컬 가능성 점수 계산
# =========================
def get_voice_score(segment, sr):
    """
    segment(짧은 오디오 구간)가
    '사람 목소리일 가능성'이 얼마나 되는지 점수 계산

    기준:
    - RMS(볼륨)가 어느 정도 있는가?
    - pitch(f0)가 얼마나 잘 잡히는가?
    """

    if len(segment) < sr // 2:
        return 0.0

    # (1) RMS
    rms = librosa.feature.rms(y=segment)[0]
    rms_mean = float(np.mean(rms))

    # (2) pitch
    try:
        f0, _, _ = librosa.pyin(
            segment,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7")
        )
        voiced_ratio = np.sum(~np.isnan(f0)) / len(f0) if len(f0) > 0 else 0.0
    except:
        voiced_ratio = 0.0

    # (3) 최종 점수
    score = (rms_mean * 10.0) + (voiced_ratio * 2.0)

    return score


# =========================
# 2. 추천용 대표 구간 추출
# =========================
def extract_recommend_segment(
    vocals_path,
    out_dir=RECOMMEND_DIR,
    target_duration_sec=30,
    chunk_sec=1.0,
    top_ratio=0.7
):
    """
    Demucs로 분리된 vocals.wav / vocals.mp3 에서
    추천용 대표 보컬 구간만 뽑아서 저장
    """

    if not os.path.exists(vocals_path):
        raise FileNotFoundError(f"파일 없음: {vocals_path}")

    # 곡명 추출
    name = get_song_base_name(vocals_path)

    print(f"[LOAD] {vocals_path}")

    # 1) 오디오 로드
    y, sr = librosa.load(vocals_path, sr=SR, mono=True)

    # 2) 앞뒤 무음 제거
    y, _ = librosa.effects.trim(y, top_db=20)

    if len(y) < sr:
        raise ValueError("보컬 길이가 너무 짧아서 추천 구간 추출 불가")

    # 3) 1초 단위 자르기
    chunk_size = int(chunk_sec * sr)
    chunks = []

    for start in range(0, len(y), chunk_size):
        end = start + chunk_size
        segment = y[start:end]

        if len(segment) < chunk_size * 0.8:
            continue

        score = get_voice_score(segment, sr)

        chunks.append({
            "start": start,
            "end": end,
            "score": score,
            "audio": segment
        })

    if len(chunks) == 0:
        raise ValueError("추천용으로 사용할 오디오 구간이 없음")

    # 4) 상위 점수 구간 선택
    scores = [c["score"] for c in chunks]
    threshold = np.quantile(scores, 1 - top_ratio)

    selected_chunks = [c for c in chunks if c["score"] >= threshold]
    selected_chunks = sorted(selected_chunks, key=lambda x: x["start"])

    if len(selected_chunks) == 0:
        raise ValueError("선택된 추천용 보컬 구간이 없음")

    # 5) 이어붙이기
    recommend_audio = np.concatenate([c["audio"] for c in selected_chunks])

    # 6) 너무 길면 중간 30초만 사용
    target_samples = target_duration_sec * sr

    if len(recommend_audio) > target_samples:
        mid = len(recommend_audio) // 2
        half = target_samples // 2
        recommend_audio = recommend_audio[mid - half: mid + half]

    # 7) 저장
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{name}_recommend.wav")

    sf.write(out_path, recommend_audio, sr, subtype="PCM_16")

    print(f"[DONE] 추천용 대표 구간 저장 완료 → {out_path}")
    print(f"[INFO] 최종 길이: {len(recommend_audio)/sr:.2f}초")

    return out_path


# =========================
# 3. audio 폴더 기준으로 vocals.mp3 경로 찾기
# =========================
def get_vocals_path_from_audio_filename(audio_filename):
    """
    audio/A_good_day.wav
    -> temp/htdemucs/A_good_day/vocals.mp3
    """
    base_name = os.path.splitext(audio_filename)[0]
    vocals_path = os.path.join(TEMP_DIR, "htdemucs", base_name, "vocals.mp3")
    return vocals_path


# =========================
# 4. 전체 자동 처리
# =========================
def process_all_recommend_segments(audio_dir=AUDIO_DIR):
    if not os.path.exists(audio_dir):
        print(f"[ERROR] audio 폴더 없음: {audio_dir}")
        return

    audio_files = [
        f for f in os.listdir(audio_dir)
        if f.lower().endswith((".wav", ".mp3", ".m4a", ".flac", ".mp4"))
    ]

    if not audio_files:
        print("[ERROR] audio 폴더에 오디오 파일이 없습니다.")
        return

    print(f"[START] 총 {len(audio_files)}개 곡 추천용 구간 생성 시작\n")

    success = 0
    fail = 0

    for f in audio_files:
        vocals_path = get_vocals_path_from_audio_filename(f)

        try:
            extract_recommend_segment(vocals_path)
            success += 1
        except Exception as e:
            fail += 1
            print(f"[SKIP] {f} 처리 실패: {e}")

        print("-" * 50)

    print("\n===== 추천용 구간 생성 완료 =====")
    print(f"[SUCCESS] 성공: {success}개")
    print(f"[FAIL] 실패: {fail}개")
    print(f"[SAVE] 저장 폴더: {RECOMMEND_DIR}")


# =========================
# 5. 외부 호출용
# =========================
def extract_single_recommend_segment(vocals_path):
    return extract_recommend_segment(vocals_path)


# =========================
# 6. 단독 실행
# =========================
if __name__ == "__main__":
    process_all_recommend_segments()