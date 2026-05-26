import os
import cv2
import easyocr
import yt_dlp
import json
import re

# =========================
# 기존 영상 삭제
# =========================

if os.path.exists("video.mp4"):
    os.remove("video.mp4")

# =========================
# 유튜브 영상 다운로드
# =========================

youtube_url = "https://www.youtube.com/watch?v=RUAPeE3mJdM"

ydl_opts = {
    'format': 'mp4',
    'outtmpl': 'video.mp4',
    'quiet': False,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([youtube_url])

# =========================
# OCR 설정
# =========================

reader = easyocr.Reader(['ko'])

cap = cv2.VideoCapture("video.mp4")

fps = cap.get(cv2.CAP_PROP_FPS)

lyrics = []

last_text = ""

# =========================
# 0.5초마다 OCR
# =========================

frame_interval = int(fps * 0.5)

frame_count = 0

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # =========================
    # 일정 간격마다 OCR
    # =========================

    if frame_count % frame_interval == 0:

        current_time = round(
            frame_count / fps,
            2
        )

        height, width, _ = frame.shape

        # =========================
        # 🔥 가사 영역 crop
        # =========================

        crop = frame[
            int(height * 0.45):int(height * 0.78),
            int(width * 0.22):int(width * 0.78)
        ]

        # =========================
        # 흑백 변환
        # =========================

        gray = cv2.cvtColor(
            crop,
            cv2.COLOR_BGR2GRAY
        )

        # =========================
        # 밝은 글씨 강조
        # =========================

        _, thresh = cv2.threshold(
            gray,
            170,
            255,
            cv2.THRESH_BINARY
        )

        # =========================
        # OCR
        # =========================

        results = reader.readtext(
            thresh,
            detail=1,
            paragraph=False
        )

        detected = []

        for r in results:

            text = r[1].strip()

            # =========================
            # 영어 제거
            # =========================

            text = re.sub(
                r'[a-zA-Z]',
                '',
                text
            )

            # =========================
            # 한글/숫자/공백만 남김
            # =========================

            text = re.sub(
                r'[^가-힣0-9\s]',
                '',
                text
            )

            # 공백 정리
            text = " ".join(
                text.split()
            )

            # =========================
            # 불필요 단어 제거
            # =========================

            ignore_words = [
                "금영",
                "노래방",
                "작사",
                "작곡",
                "엔터테인먼트"
            ]

            if any(
                word in text
                for word in ignore_words
            ):
                continue

            # =========================
            # 짧은 글 제거
            # =========================

            if len(text) >= 2:
                detected.append(text)

        # =========================
        # 한 줄로 합치기
        # =========================

        final_text = " ".join(
            detected
        )

        # =========================
        # 중복 제거
        # =========================

        if (
            final_text
            and final_text != last_text
        ):

            lyrics.append({
                "time": current_time,
                "text": final_text
            })

            print(
                current_time,
                final_text
            )

            last_text = final_text

        # =========================
        # 디버그 이미지 저장
        # =========================

        cv2.imwrite(
            "debug_crop.png",
            crop
        )

        cv2.imwrite(
            "debug_thresh.png",
            thresh
        )

    frame_count += 1

cap.release()

# =========================
# JSON 저장
# =========================

with open(
    "lyrics.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        lyrics,
        f,
        ensure_ascii=False,
        indent=2
    )

print("완료!")