from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import importlib

from utils import aes_encrypt
import models
from database import get_db

# 라우터 설정
router = APIRouter(prefix="/kiosk", tags=["External Kiosk (외부 키오스크)"])

# 데이터 모델
class SongSelect(BaseModel):
    phone: str | None = None
    song_count: int

class LedCommand(BaseModel):
    color: str

# 키오스크 상태 관리
current_kiosk_state = {
    "status": "none",
    "user_id": None,
    "phone": None,
    "remaining_songs": 0,
    "led_status": "green",
}

# =========================
# Arduino 통신 로직 (Lazy Initialization)
# =========================
serial = importlib.import_module("serial")
SERIAL_PORT = os.getenv("ARDUINO_SERIAL_PORT", "COM3")
SERIAL_BAUD = int(os.getenv("ARDUINO_SERIAL_BAUD", "9600"))

arduino_serial = None

def init_arduino():
    global arduino_serial
    if arduino_serial is not None:
        return
    try:
        arduino_serial = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
        print("[Arduino] 연결 성공")
    except Exception as e:
        arduino_serial = None
        print(f"[Arduino] Serial init failed: {e}")

def send_arduino_command(command: str):
    global arduino_serial
    if arduino_serial is None:
        init_arduino()
    if arduino_serial is None:
        return

    try:
        if not arduino_serial.is_open:
            arduino_serial.open()
        arduino_serial.write(f"{command}\n".encode())
    except Exception as e:
        print(f"[Arduino] Serial write failed: {e}")

# =========================
# API 엔드포인트
# =========================

@router.get("/current_user")
def get_current_user():
    if current_kiosk_state["status"] == "member":
        return {
            "status": "member",
            "user_id": current_kiosk_state["user_id"],
            "remaining_songs": current_kiosk_state["remaining_songs"],
            "led_status": current_kiosk_state["led_status"],
        }
    if current_kiosk_state["status"] == "guest":
        return {
            "status": "guest",
            "user_id": "비회원",
            "remaining_songs": current_kiosk_state["remaining_songs"],
            "led_status": current_kiosk_state["led_status"],
        }
    return {
        "status": "none",
        "user_id": "-",
        "remaining_songs": 0,
        "led_status": current_kiosk_state["led_status"],
    }

@router.get("/user/{phone}")
def check_user_credits(phone: str, db: Session = Depends(get_db)):
    crypto_phone = aes_encrypt(phone)  # 오타 수정 완료
    user = db.query(models.User).filter(models.User.phone == crypto_phone).first()
    if user:
        return {"phone": phone, "is_member": True, "remaining_songs": user.remaining_songs}
    return {"phone": phone, "is_member": False, "remaining_songs": 0}

@router.post("/entry")
def enter_booth(selection: SongSelect, db: Session = Depends(get_db)):
    user_type = "회원" if selection.phone else "비회원"
    if selection.phone:
        crypto_phone = aes_encrypt(selection.phone)
        user = db.query(models.User).filter(models.User.phone == crypto_phone).first()
        if user:
            user.remaining_songs = selection.song_count
            db.commit()
            current_kiosk_state.update({
                "status": "member", "user_id": user.user_id, "phone": selection.phone,
                "remaining_songs": selection.song_count, "led_status": "red"
            })
        else:
            user_type = "비회원"
            current_kiosk_state.update({
                "status": "guest", "user_id": None, "phone": None,
                "remaining_songs": selection.song_count, "led_status": "red"
            })
    else:
        current_kiosk_state.update({
            "status": "guest", "user_id": None, "phone": None,
            "remaining_songs": selection.song_count, "led_status": "red"
        })

    send_arduino_command("RESERVATION")
    return {
        "status": "success", "message": f"{user_type} 입장 처리 완료",
        "data": {"assigned_songs": selection.song_count, "room_status": "active"}
    }

@router.post("/led")
def set_led(command: LedCommand):
    color = command.color.strip().upper()
    mapping = {
        "RED": "RESERVATION", "SONG_SELECT": "RESERVATION", "RESERVATION": "RESERVATION",
        "GREEN": "AVAILABLE", "HOME": "AVAILABLE", "RESET": "AVAILABLE", "AVAILABLE": "AVAILABLE"
    }
    arduino_cmd = mapping.get(color)
    if arduino_cmd is None:
        return {"status": "error", "message": "Invalid LED color"}
    send_arduino_command(arduino_cmd)
    return {"status": "success", "message": f"LED command sent: {arduino_cmd}"}

@router.post("/reset")
def reset_kiosk():
    current_kiosk_state.update({
        "status": "none", "user_id": None, "phone": None,
        "remaining_songs": 0, "led_status": "green"
    })
    send_arduino_command("AVAILABLE")
    return {"status": "success", "message": "키오스크 상태가 초기화되었습니다."}