from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from utils import aes_encrypt
import models
from database import get_db

router = APIRouter(prefix="/kiosk", tags=["External Kiosk (외부 키오스크)"])


class SongSelect(BaseModel):
    phone: Optional[str] = None   # 비회원이면 None
    song_count: int               # 1 ~ 3곡


# 현재 키오스크 사용자 상태 저장용
current_user_state = {
    "status": "none",
    "user_id": None,
    "remaining_songs": 0,
    "phone": None,
}


@router.get("/user/{phone}")
def check_user_credits(phone: str, db: Session = Depends(get_db)):
    if not phone:
        raise HTTPException(status_code=400, detail="전화번호가 없습니다.")

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


@router.post("/entry")
def enter_booth(selection: SongSelect, db: Session = Depends(get_db)):
    if selection.song_count < 1 or selection.song_count > 3:
        raise HTTPException(status_code=400, detail="song_count는 1~3 사이여야 합니다.")

    # 회원 처리
    if selection.phone:
        crypto_phone = aes_encrypt(selection.phone)

        user = db.query(models.User).filter(
            models.User.phone == crypto_phone
        ).first()

        if not user:
            raise HTTPException(status_code=404, detail="회원 정보를 찾을 수 없습니다.")

        user.remaining_songs = selection.song_count
        db.commit()

        current_user_state["status"] = "member"
        current_user_state["user_id"] = user.user_id
        current_user_state["remaining_songs"] = user.remaining_songs
        current_user_state["phone"] = selection.phone

        return {
            "status": "success",
            "message": "회원 입장 처리 완료",
            "data": {
                "assigned_songs": selection.song_count,
                "room_status": "active",
                "user_id": user.user_id,
                "remaining_songs": user.remaining_songs
            }
        }

    # 비회원 처리
    current_user_state["status"] = "guest"
    current_user_state["user_id"] = "비회원"
    current_user_state["remaining_songs"] = selection.song_count
    current_user_state["phone"] = None

    return {
        "status": "success",
        "message": "비회원 입장 처리 완료",
        "data": {
            "assigned_songs": selection.song_count,
            "room_status": "active",
            "user_id": "비회원",
            "remaining_songs": selection.song_count
        }
    }


@router.get("/current_user")
def get_current_user():
    if current_user_state["status"] == "member":
        return {
            "status": "member",
            "user_id": current_user_state["user_id"],
            "remaining_songs": current_user_state["remaining_songs"]
        }

    if current_user_state["status"] == "guest":
        return {
            "status": "guest",
            "remaining_songs": current_user_state["remaining_songs"]
        }

    return {
        "status": "none"
    }

@router.get("/qr")
def get_qr_url():
    # 현재 로그인된 사용자 상태 가져오기 (기존 코드에서 쓰던 변수)
    if current_user_state["status"] == "none":
        return {"status": "fail"}

    user_id = current_user_state["user_id"]

    # ⚠️ 여기 IP는 네 맥북 IP로 바꿔야 함
    qr_url = f"http://172.30.1.11:5176/m/feedback/{user_id}"

    return {
        "status": "success",
        "qr_url": qr_url
    }