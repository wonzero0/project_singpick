import os
import numpy as np
import librosa
import soundfile as sf

SR = 22050

USER_AUDIO_DIR = "user_audio"
USER_SEGMENT_DIR = "user_segments"

os.makedirs(USER_SEGMENT_DIR, exist_ok=True)


# =========================
# 1. 목소리 가능성 점수 계산
# =========================
def get_voice_score(segment, sr):
    """
    짧은 오디오 구간이
    사람 목소리일 가능성을 점수화

    기준:
    - RMS (볼륨)
    - pitch 검출 비율
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
# 2. 사용자 대표 구간 추출
# =========================
def extract_user_segment(
    audio_path,
    out_dir=USER_SEGMENT_DIR,
    target_duration_sec=30,
    chunk_sec=1.0,
    top_ratio=0.7
):
    """
    사용자 음성 파일에서
    추천/임베딩용 대표 30초 구간 추출
    """

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"파일 없음: {audio_path}")

    base_name = os.path.splitext(os.path.basename(audio_path))[0]

    print("=" * 50)
    print(f"[LOAD] {audio_path}")

    # 1) 오디오 로드
    y, sr = librosa.load(audio_path, sr=SR, mono=True)

    # 2) 앞뒤 무음 제거
    y, _ = librosa.effects.trim(y, top_db=20)

    if len(y) < sr:
        raise ValueError("오디오 길이가 너무 짧아서 대표 구간 추출 불가")

    # 3) 1초 단위로 자르기
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
        raise ValueError("사용 가능한 음성 구간이 없음")

    # 4) 상위 점수 구간 선택
    scores = [c["score"] for c in chunks]
    threshold = np.quantile(scores, 1 - top_ratio)

    selected_chunks = [c for c in chunks if c["score"] >= threshold]
    selected_chunks = sorted(selected_chunks, key=lambda x: x["start"])

    if len(selected_chunks) == 0:
        raise ValueError("선택된 대표 음성 구간이 없음")

    # 5) 이어붙이기
    segment_audio = np.concatenate([c["audio"] for c in selected_chunks])

    # 6) 길이 맞추기 (중간 30초 사용)
    target_samples = target_duration_sec * sr

    if len(segment_audio) > target_samples:
        mid = len(segment_audio) // 2
        half = target_samples // 2
        segment_audio = segment_audio[mid - half: mid + half]

    # 너무 짧으면 그대로 저장
    final_duration = len(segment_audio) / sr

    # 7) 저장
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{base_name}.wav")

    sf.write(out_path, segment_audio, sr, subtype="PCM_16")

    print(f"[SAVE] {out_path}")
    print(f"[INFO] 최종 길이: {final_duration:.2f}초")

    return out_path


# =========================
# 3. 전체 사용자 파일 자동 처리
# =========================
def process_all_user_segments(user_audio_dir=USER_AUDIO_DIR):
    if not os.path.exists(user_audio_dir):
        print(f"[ERROR] user_audio 폴더 없음: {user_audio_dir}")
        return

    audio_files = [
        f for f in os.listdir(user_audio_dir)
        if f.lower().endswith((".wav", ".mp3", ".m4a", ".flac", ".mp4"))
    ]

    if not audio_files:
        print("[ERROR] user_audio 폴더에 오디오 파일이 없습니다.")
        return

    print(f"[START] 총 {len(audio_files)}개 사용자 음성 대표 구간 생성 시작\n")

    success = 0
    fail = 0

    for f in audio_files:
        audio_path = os.path.join(user_audio_dir, f)

        try:
            extract_user_segment(audio_path)
            success += 1
        except Exception as e:
            fail += 1
            print(f"[SKIP] {f} 처리 실패: {e}")

        print("-" * 50)

    print("\n===== 사용자 대표 구간 생성 완료 =====")
    print(f"[SUCCESS] 성공: {success}개")
    print(f"[FAIL] 실패: {fail}개")
    print(f"[SAVE] 저장 폴더: {USER_SEGMENT_DIR}")


# =========================
# 4. 외부 호출용
# =========================
def extract_single_user_segment(audio_path):
    return extract_user_segment(audio_path)


# =========================
# 5. 단독 실행
# =========================
if __name__ == "__main__":
    process_all_user_segments()