BOOTH_ID = 1
BOOTH_STATUS_BUSY = "busy"
BOOTH_STATUS_EMPTY = "empty"
GUEST_USER_ID = "GUEST"

current_kiosk_state = {
    "status": "none",
    "user_id": None,
    "phone": None,
    "remaining_songs": 0,
    "led_status": "green",
}


def get_current_reservation_user_id() -> str:
    """현재 키오스크 상태에서 예약할 사용자의 ID 반환"""
    if current_kiosk_state["status"] == "member" and current_kiosk_state["user_id"]:
        result = current_kiosk_state["user_id"]
        print(f"[DEBUG get_current_reservation_user_id] Member: {result}")
        return result
    
    result = GUEST_USER_ID
    print(f"[DEBUG get_current_reservation_user_id] Guest or None: {result}")
    return result


def set_booth_status(db, status: str):
    import models

    booth = db.query(models.Booth).filter(models.Booth.booth_id == BOOTH_ID).first()

    if booth is None:
        booth = models.Booth(
            booth_id=BOOTH_ID,
            name=f"{BOOTH_ID}번 부스",
            status=status,
        )
        db.add(booth)
    else:
        booth.status = status

    db.commit()
    db.refresh(booth)
    return booth
