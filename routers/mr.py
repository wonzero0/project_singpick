import os
from fastapi import APIRouter
import yt_dlp
from ai_module import extract_basic_features

router = APIRouter()

DOWNLOAD_DIR = "downloaded_mrs"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@router.get("/search_mr", summary="금영노래방 영상 리스트 검색")
async def search_youtube_mr(keyword: str):
    search_query = f"KY Karaoke {keyword}"
    
    ydl_opts = {
        'format': 'best',
        'noplaylist': True,
        'extract_flat': True,
        'quiet': True,  
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 상위 5개
            info = ydl.extract_info(f"ytsearch5:{search_query}", download=False)
            
            songs_list = []
            
            if 'entries' in info and len(info['entries']) > 0:
                for entry in info['entries']:
                    title = entry.get('title', '')
                    # 금영 영상만 골라담기 (필터링)
                    if 'KY' in title or '금영' in title:
                        songs_list.append({
                            "video_id": entry.get('id'),
                            "title": title,
                            "embed_url": f"https://www.youtube.com/embed/{entry.get('id')}?autoplay=1"
                        })
                
                # 만약 금영 필터링 결과가 너무 적으면 전체 검색 결과에서 보충
                if len(songs_list) < 3:
                    for entry in info['entries']:
                        if entry.get('id') not in [s['video_id'] for s in songs_list]:
                            songs_list.append({
                                "video_id": entry.get('id'),
                                "title": entry.get('title'),
                                "embed_url": f"https://www.youtube.com/embed/{entry.get('id')}?autoplay=1"
                            })

                print(f"✅ 검색 완료! 총 {len(songs_list)}개의 검색 결과를 찾았습니다.")
                return {
                    "status": "success",
                    "count": len(songs_list),
                    "results": songs_list 
                }
            else:
                return {"status": "fail", "message": "검색 결과가 없습니다."}
                
    except Exception as e:
        return {"status": "error", "message": f"검색 중 오류 발생: {str(e)}"}



@router.post("/download_mr", summary="선택한 영상 오디오 다운로드")
async def download_youtube_mr(video_id: str):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # yt-dlp 설정: 오디오만 추출해서 mp3로 변환
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s', # 저장 경로와 파일명 규칙
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False, # 다운로드 과정을 터미널에서 보기 위해 일시적으로 on
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"🚀 다운로드 시작: {video_url}")
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            
            return {
                "status": "success",
                "message": "다운로드 완료!",
                "file_path": filename,
                "title": info.get('title')
            }
            
    except Exception as e:
        return {"status": "error", "message": f"다운로드 중 오류 발생: {str(e)}"}