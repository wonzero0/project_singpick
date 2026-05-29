BOOTH_ID = 1
BOOTH_STATUS_BUSY = "busy"
BOOTH_STATUS_EMPTY = "empty"
GUEST_USER_ID = "비회원"

current_kiosk_state = {
    "status": "none",
    "user_id": None,
    "phone": None,
    "remaining_songs": 0,
    "led_status": "green",
}


def get_current_reservation_user_id() -> str:
    if current_kiosk_state["status"] == "member" and current_kiosk_state["user_id"]:
        return current_kiosk_state["user_id"]
    return GUEST_USER_ID


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
