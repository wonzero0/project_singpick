# routers/library.py 위쪽 부분
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
import models
import os
import yt_dlp

router = APIRouter(
    prefix="/library",
    tags=["📖 Library (노래 검색/예약)"]
)

@router.get("/search", summary="노래 검색 및 전체 목록")
def search_song(keyword: Optional[str] = "", db: Session = Depends(get_db)):
    query = db.query(models.Song)
    
    if keyword:
        # 2. 검색어가 있으면? -> 50곡 DB 안에서 해당 노래 찾기!
        query = query.filter(
            (models.Song.title.like(f"%{keyword}%")) |
            (models.Song.singer.like(f"%{keyword}%"))
        )
        results = query.all()
    else:
        # 1. 검색어가 없으면(처음 켜졌을 때)? -> 깔끔하게 딱 10개만 보여주기!
        results = query.limit(10).all()
        
    return {"count": len(results), "results": results}


@router.post("/reserve", summary="노래 예약")
def reserve_song(booth_id: int, ky_number: int, db: Session = Depends(get_db)):
    song = db.query(models.Song).filter(models.Song.ky_number == ky_number).first()
    
    if not song:
        raise HTTPException(status_code=404, detail="존재하지 않는 노래 번호입니다.")

    new_reservation = models.Reservation(
        booth_id=booth_id,
        song_id=song.song_id,
        status="waiting"
    )
    db.add(new_reservation)
    db.commit()
    
    return {"status": "success", "message": f"[{song.title}] 예약 완료!"}


# ==========================================
# 🚨 MR 다운로드 및 재생 준비 API 
# ==========================================
@router.get("/download_mr", summary="MR 실시간 다운로드", description="시작 버튼을 누르면 자동으로 검색 및 다운로드합니다.")
def download_mr_for_play(song_info: str):
    print(f"📥 [{song_info}] 실시간 MR 다운로드 요청 들어옴!")
    
    DOWNLOAD_DIR = "downloaded_mrs"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # 파일 이름에 특수문자나 공백이 들어가면 에러가 날 수 있어서 깔끔하게 바꿔줍니다.
    safe_filename = song_info.replace(" | ", "_").replace(" ", "_")
    file_path = f"{DOWNLOAD_DIR}/{safe_filename}.mp3"
    audio_url = f"http://127.0.0.1:8000/{DOWNLOAD_DIR}/{safe_filename}.mp3"

    # 🌟 꿀팁 기능: 이미 전에 다운받았던 노래면 다시 다운받지 않고 0초 만에 바로 넘겨줍니다!
    if os.path.exists(file_path):
        print(f"⚡ 이미 다운로드된 곡입니다. 바로 재생합니다: {file_path}")
        return {"status": "success", "audio_url": audio_url}

    # 1. 유튜브에서 자동으로 'TJ 노래방 MR' 1등 영상 찾기
    search_query = f"금영 노래방 {song_info}"
    search_opts = {'format': 'best', 'noplaylist': True, 'extract_flat': True, 'quiet': True}
    
    try:
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            # 딱 1개만 검색해서 가져오기
            info = ydl.extract_info(f"ytsearch1:{search_query}", download=False)
            
            if not info or 'entries' not in info or len(info['entries']) == 0:
                return {"status": "fail", "message": "유튜브에서 MR을 찾을 수 없습니다."}
            
            video_id = info['entries'][0]['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"🔍 1등 영상 찾음! 다운로드 시작: {video_url}")

        # 2. 찾은 영상 다운로드 (MP3 변환)
        download_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_DIR}/{safe_filename}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            ydl.download([video_url])
            
        print("✅ MR 다운로드 및 MP3 변환 완료!")
        return {"status": "success", "audio_url": audio_url}
        
    except Exception as e:
        print(f"❌ 다운로드 에러: {e}")
        return {"status": "error", "message": str(e)}