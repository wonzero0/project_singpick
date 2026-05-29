from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database import get_db
import models
from state import (
    BOOTH_ID,
    BOOTH_STATUS_BUSY,
    current_kiosk_state,
    get_current_reservation_user_id,
    set_booth_status,
)

router = APIRouter(
    prefix="/library",
    tags=["📖 Library (노래 검색/예약)"]
)


@router.get("/search", summary="노래 검색", description="가수나 제목으로 노래를 찾습니다.")
def search_song(keyword: str = "", db: Session = Depends(get_db)):
    query = db.query(models.Song)
    if keyword:
        query = query.filter(
            (models.Song.title.like(f"%{keyword}%")) |
            (models.Song.singer.like(f"%{keyword}%"))
        )
    results = query.all()
    return {
        "count": len(results),
        "results": [
            {
                "song_id": song.song_id,
                "title": song.title,
                "singer": song.singer,
                "ky_number": song.ky_number,
            }
            for song in results
        ],
    }


@router.post("/reserve", summary="노래 예약")
def reserve_song(ky_number: int, db: Session = Depends(get_db)):
    song = db.query(models.Song).filter(models.Song.ky_number == ky_number).first()
    if not song:
        raise HTTPException(status_code=404, detail="존재하지 않는 노래 번호입니다.")

    # 현재 키오스크에 입장한 사용자의 ID 또는 비회원 식별자 가져오기
    current_user = get_current_reservation_user_id()

    if current_kiosk_state["status"] in ("member", "guest"):
        set_booth_status(db, BOOTH_STATUS_BUSY)

    new_reservation = models.Reservation(
        user_id=current_user,
        booth_id=BOOTH_ID,
        song_id=song.song_id,
        status="waiting"
    )

    try:
        db.add(new_reservation)
        db.commit()
        db.refresh(new_reservation)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="예약 정보를 DB에 저장하지 못했습니다.")

    return {
        "status": "success",
        "message": f"[{song.title}] 예약되었습니다. (방: {BOOTH_ID}번)",
        "reservation_id": new_reservation.id,
        "song_id": song.song_id,
        "title": song.title,
        "singer": song.singer,
        "ky_number": song.ky_number,
    }


@router.get("/reservations/{booth_id}", summary="예약 목록 확인")
def get_reservations(booth_id: int, db: Session = Depends(get_db)):
    return db.query(models.Reservation).filter(
        models.Reservation.booth_id == booth_id,
        models.Reservation.status == "waiting"
    ).all()
