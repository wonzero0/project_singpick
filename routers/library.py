from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter(
    prefix="/library",
    tags=["📖 Library (노래 검색/예약)"]
)


@router.get("/search", summary="노래 검색", description="가수나 제목으로 노래를 찾습니다.")
def search_song(keyword: str, db: Session = Depends(get_db)):
    results = db.query(models.Song).filter(
        (models.Song.title.like(f"%{keyword}%")) |
        (models.Song.singer.like(f"%{keyword}%"))
    ).all()
    return {"count": len(results), "results": results}


@router.post("/reserve", summary="노래 예약", description="부스 번호와 노래방 번호(TJ 번호)를 받아 예약합니다.")
def reserve_song(booth_id: int, tj_number: int, db: Session = Depends(get_db)):
    song = db.query(models.Song).filter(models.Song.tj_number == tj_number).first()

    if not song:
        raise HTTPException(status_code=404, detail="존재하지 않는 노래 번호입니다.")

    new_reservation = models.Reservation(
        booth_id=booth_id,
        song_id=song.song_id,
        status="waiting"
    )
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)

    return {
        "status": "success",
        "message": f"[{song.title}] 예약되었습니다. (방: {booth_id}번)",
        "reservation_id": new_reservation.id,
        "song_id": song.song_id,
        "title": song.title,
        "singer": song.singer,
        "tj_number": song.tj_number
    }


@router.get("/reservations/{booth_id}", summary="예약 목록 확인")
def get_reservations(booth_id: int, db: Session = Depends(get_db)):
    return db.query(models.Reservation).filter(
        models.Reservation.booth_id == booth_id,
        models.Reservation.status == "waiting"
    ).all()