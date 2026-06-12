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
    
    # 🔍 디버깅: 현재 상태와 저장될 데이터 로깅
    print(f"[DEBUG reserve_song]")
    print(f"  - current_kiosk_state['status']: {current_kiosk_state['status']}")
    print(f"  - current_kiosk_state['user_id']: {current_kiosk_state['user_id']}")
    print(f"  - 계산된 current_user: {current_user}")
    print(f"  - song.song_id: {song.song_id}")
    print(f"  - song.ky_number: {song.ky_number}")

    if current_kiosk_state["status"] in ("member", "guest"):
        set_booth_status(db, BOOTH_STATUS_BUSY)

    # 데이터 타입 강제 변환 및 매핑 확인
    safe_user_id = str(current_user) if current_user else "GUEST"
    safe_booth_id = int(BOOTH_ID)
    safe_song_id = int(song.song_id)

    new_reservation = models.Reservation(
        user_id=safe_user_id,
        booth_id=safe_booth_id,
        song_id=safe_song_id,
        status="waiting"
    )

    try:
        print(f"\n🚀 [DB_RESERVE] 저장 시도: User={safe_user_id}, Booth={safe_booth_id}, Song={safe_song_id}")
        db.add(new_reservation)
        db.commit()  # 명시적 커밋
        db.refresh(new_reservation)
        
        print(f"✅ [DB_RESERVE] 저장 성공! 생성된 ID: {new_reservation.id}")
        
    except Exception as e:
        db.rollback()
        print("\n" + "!"*60)
        print("❌ [CRITICAL DB ERROR] Reservation 저장 실패!")
        print(f"Error Message: {str(e)}")
        print(f"매핑 시도 데이터:")
        print(f"  - user_id: {safe_user_id}")
        print(f"  - booth_id: {safe_booth_id}")
        print(f"  - song_id: {safe_song_id}")
        print("!"*60 + "\n")
        raise HTTPException(status_code=500, detail=f"예약 저장 실패: {str(e)}")

    return {
        "status": "success",
        "message": f"[{song.title}] 예약되었습니다. (방: {BOOTH_ID}번)",
        "reservation_key": f"{BOOTH_ID}:{song.song_id}:{current_user}",
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
