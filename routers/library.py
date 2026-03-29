from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks # 🚨 BackgroundTasks 추가!
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
import models
import downloaded_mrs

router = APIRouter(
    prefix="/library",
    tags=["📖 Library (노래 검색/예약)"]
)

@router.get("/search", summary="노래 검색 및 전체 목록", description="검색어가 없으면 전체 곡(최신순)을 보여줍니다.")
def search_song(keyword: Optional[str] = "", db: Session = Depends(get_db)):
    # 기본 쿼리 준비
    query = db.query(models.Song)
    
    # 1. 만약 검색어(keyword)가 들어왔다면? -> 기존처럼 검색 실행
    if keyword:
        query = query.filter(
            (models.Song.title.like(f"%{keyword}%")) |
            (models.Song.singer.like(f"%{keyword}%"))
        )
    
    # 2. 검색어가 없으면? -> 전체 곡을 보여주되, 최신순(id 역순)으로 정렬해서 50개만! 
    results = query.order_by(models.Song.tj_number.desc()).limit(50).all()
    
    return {"count": len(results), "results": results}

@router.post("/reserve", summary="노래 예약", description="부스 번호와 노래방 번호(TJ 번호)를 받아 예약합니다.")
def reserve_song(booth_id: int, tj_number: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    song = db.query(models.Song).filter(models.Song.tj_number == tj_number).first()

    if not song:
        raise HTTPException(status_code=404, detail="존재하지 않는 노래 번호입니다.")

    new_reservation = models.Reservation(
        booth_id=booth_id,
        song_id=song.song_id,
        status="waiting" # 상태: MR 다운로드 대기 중
    )
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)

    # 🚨 예약이 성공적으로 DB에 저장된 후에, 백그라운드에서 MR 다운로드 작업을 시작하도록 요청
    background_tasks.add_task(downloaded_mrs, song.title, song.singer, new_reservation.reservation_id)


    return {
        "status": "success",
        "message": f"[{song.title}] 예약 완료 및 MR 다운로드 준비 중!",
        "reservation_id": new_reservation.reservation_id
    }