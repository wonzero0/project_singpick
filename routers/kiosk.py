from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from utils import aes_encrypt
import models

# DB 연결
from database import get_db
from models import User

# 키오스크 관련 기능만 모아두는 곳
router = APIRouter(prefix="/kiosk", tags=["External Kiosk (외부 키오스크)"])

# 요청 데이터 양식 (곡 수 선택)
class SongSelect(BaseModel):
    phone: str | None = None  # 비회원이면 None(비어있음)
    song_count: int  # 1 ~ 3곡

current_kiosk_state = {
    "status": "none",
    "user_id": None,
    "phone": None,
    "remaining_songs": 0,
}


# 1. 잔여 곡 수 / 회원 상태 확인 API
from database import SessionLocal

@router.get("/current_user")
def get_current_user():
    if current_kiosk_state["status"] == "member":
        return {
            "status": "member",
            "user_id": current_kiosk_state["user_id"],
            "remaining_songs": current_kiosk_state["remaining_songs"],
        }
    if current_kiosk_state["status"] == "guest":
        return {
            "status": "guest",
            "user_id": "비회원",
            "remaining_songs": current_kiosk_state["remaining_songs"],
        }
    return {"status": "none", "user_id": "-", "remaining_songs": 0}


@router.get("/user/{phone}")
def check_user_credits(phone: str, db: Session = Depends(get_db)):

    crypto_phone = aes_encrypt(phone)

    user = db.query(models.User).filter(models.User.phone == crypto_phone).first()

    if user:
        return {
            "phone": phone,
            "is_member": True,
            "remaining_songs": user.remaining_songs
        }

    return {
        "phone": phone,
        "is_member": False,
        "remaining_songs": 0
    }


# 2. 곡 수 결제 및 입장 처리 API
@router.post("/entry")
def enter_booth(selection: SongSelect, db: Session = Depends(get_db)):

    user_type = "회원" if selection.phone else "비회원"

    if selection.phone:
        crypto_phone = aes_encrypt(selection.phone)

        user = db.query(models.User).filter(
            models.User.phone == crypto_phone
        ).first()

        if user:
            user.remaining_songs = selection.song_count
            db.commit()
            current_kiosk_state.update(
                {
                    "status": "member",
                    "user_id": user.user_id,
                    "phone": selection.phone,
                    "remaining_songs": selection.song_count,
                }
            )
        else:
            user_type = "비회원"
            current_kiosk_state.update(
                {
                    "status": "guest",
                    "user_id": None,
                    "phone": None,
                    "remaining_songs": selection.song_count,
                }
            )
    else:
        current_kiosk_state.update(
            {
                "status": "guest",
                "user_id": None,
                "phone": None,
                "remaining_songs": selection.song_count,
            }
        )

    return {
        "status": "success",
        "message": f"{user_type} 입장 처리 완료",
        "data": {
            "assigned_songs": selection.song_count,
            "room_status": "active"
        }
    }


# 3. 키오스크 상태 초기화 API
@router.post("/reset")
def reset_kiosk():
    current_kiosk_state.update({
        "status": "none",
        "user_id": None,
        "phone": None,
        "remaining_songs": 0,
    })
    return {"status": "success", "message": "키오스크 상태가 초기화되었습니다."}