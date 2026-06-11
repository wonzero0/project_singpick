from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import os
import importlib
import time
from schemas import RequestReserve
from utils import aes_encrypt
import models
from database import get_db
from state import (
    BOOTH_ID,
    BOOTH_STATUS_BUSY,
    BOOTH_STATUS_EMPTY,
    current_kiosk_state,
    set_booth_status,
)

# 라우터 설정
router = APIRouter(
    prefix="/kiosk",
    tags=["External Kiosk (외부 키오스크)"]
)

# =========================
# 데이터 모델
# =========================

class SongSelect(BaseModel):
    phone: str | None = None
    song_count: int


class LedCommand(BaseModel):
    color: str


# =========================
# Arduino 통신 로직
# =========================

serial = importlib.import_module("serial")


def normalize_serial_port(port: str) -> str:
    if os.name != "nt" and port and not port.startswith("/dev/"):
        return f"/dev/{port}"
    return port


SERIAL_PORT = normalize_serial_port(os.getenv("ARDUINO_SERIAL_PORT", "ttyACM1"))
SERIAL_BAUD = int(os.getenv("ARDUINO_SERIAL_BAUD", "9600"))
arduino_serial = None

COMMAND_MAPPING = {
    "RED": "RESERVATION",
    "SONG_SELECT": "RESERVATION",
    "RESERVATION": "RESERVATION",
    "GREEN": "AVAILABLE",
    "HOME": "RESET",
    "RESET": "RESET",
    "AVAILABLE": "AVAILABLE",
}

LED_STATUS_MAPPING = {
    "RESERVATION": "red",
    "AVAILABLE": "green",
    "RESET": "green",
}


def init_arduino():
    global arduino_serial

    if arduino_serial is not None:
        return

    try:
        arduino_serial = serial.Serial(
            SERIAL_PORT,
            SERIAL_BAUD,
            timeout=2
        )

        print(f"[Arduino] Serial opened: {SERIAL_PORT} @ {SERIAL_BAUD}")
        time.sleep(3)

        send_arduino_command("RESET", ensure_init=False)

    except Exception as e:
        arduino_serial = None
        print(f"[Arduino] Serial init failed: {e}")


def ensure_arduino_initialized():
    if arduino_serial is None:
        init_arduino()


def send_arduino_command(command: str, ensure_init: bool = True) -> bool:
    global arduino_serial

    if ensure_init:
        ensure_arduino_initialized()

    if arduino_serial is None:
        print("[Arduino] send failed: serial not initialized")
        return False

    try:
        if not arduino_serial.is_open:
            arduino_serial.open()
            print("[Arduino] Serial port opened")
            time.sleep(3)

        message = f"{command.strip()}\n"
        arduino_serial.reset_input_buffer()
        arduino_serial.write(message.encode())
        arduino_serial.flush()

        print(f"[Arduino] Sent: {command.strip()}")

        deadline = time.time() + 1.5
        while time.time() < deadline:
            if arduino_serial.in_waiting:
                line = arduino_serial.readline().decode(errors="ignore").strip()
                if line:
                    print(f"[Arduino] Received: {line}")
                    if any(token in line for token in [
                        "STATE_AVAILABLE",
                        "STATE_RESERVATION",
                        "STATE_UNAVAILABLE",
                        "GREEN LED ON",
                        "RED LED ON",
                        "RESET -> GREEN LED ON",
                    ]):
                        break
            else:
                time.sleep(0.05)

        return True

    except Exception as e:
        print(f"[Arduino] Serial write failed: {e}")
        return False


def update_server_led_state(arduino_command: str):
    current_kiosk_state["led_status"] = LED_STATUS_MAPPING.get(arduino_command, "green")


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

    crypto_phone = aes_encrypt(phone)

    user = (
        db.query(models.User)
        .filter(models.User.phone == crypto_phone)
        .first()
    )

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
    user_type = "회원" if selection.phone else "비회원"

    # 로그인/비회원 선택 후 곡 수 선택 창에 진입하면 1번 부스를 사용 중으로 저장합니다.
    set_booth_status(db, BOOTH_STATUS_BUSY)

    if selection.phone:
        crypto_phone = aes_encrypt(selection.phone)
        user = (
            db.query(models.User)
            .filter(models.User.phone == crypto_phone)
            .first()
        )

        if user:
            user.remaining_songs = selection.song_count
            db.commit()
            current_kiosk_state.update({
                "status": "member",
                "user_id": user.user_id,
                "phone": selection.phone,
                "remaining_songs": selection.song_count,
            })
        else:
            user_type = "비회원"
            current_kiosk_state.update({
                "status": "guest",
                "user_id": None,
                "phone": None,
                "remaining_songs": selection.song_count,
            })
    else:
        current_kiosk_state.update({
            "status": "guest",
            "user_id": None,
            "phone": None,
            "remaining_songs": selection.song_count,
        })

    if not send_arduino_command("RESERVATION"):
        return {
            "status": "error",
            "message": "Arduino 연결에 실패했습니다. 다시 시도해주세요.",
        }

    update_server_led_state("RESERVATION")

    return {
        "status": "success",
        "message": f"{user_type} 입장 처리 완료",
        "data": {
            "assigned_songs": selection.song_count,
            "room_status": "active",
        },
    }


@router.post("/led")
def set_led(command: LedCommand):
    color = command.color.strip().upper()
    arduino_cmd = COMMAND_MAPPING.get(color)

    if arduino_cmd is None:
        return {
            "status": "error",
            "message": "Invalid LED color",
        }

    if arduino_cmd == "AVAILABLE" and current_kiosk_state["status"] in ("member", "guest"):
        return {
            "status": "error",
            "message": "부스 이용 중에는 AVAILABLE/GREEN 명령을 허용하지 않습니다. 이용 종료 시 /reset를 사용하세요.",
        }

    if not send_arduino_command(arduino_cmd):
        return {
            "status": "error",
            "message": "Arduino 명령 전송에 실패했습니다.",
        }

    if arduino_cmd == "RESET":
        current_kiosk_state.update({
            "status": "none",
            "user_id": None,
            "phone": None,
            "remaining_songs": 0,
        })

    update_server_led_state(arduino_cmd)

    return {
        "status": "success",
        "message": f"LED command sent: {arduino_cmd}",
    }


@router.post("/reset")
def reset_kiosk(db: Session = Depends(get_db)):
    # 1. DB 부스 상태 초기화
    set_booth_status(db, BOOTH_STATUS_EMPTY)

    # 2. Arduino 통신
    send_arduino_command("RESET")
    
    # 3. 메모리 상태 초기화
    current_kiosk_state.update({
        "status": "none", 
        "user_id": None, 
        "phone": None, 
        "remaining_songs": 0,
        "led_status": "green"
    })
    
    return {"status": "success", "message": "이용 종료 및 초기화 완료"}

init_arduino()

@router.post("/reserve")
def reserve_song_endpoint(request: RequestReserve, db: Session = Depends(get_db)):
    """노래 예약 버튼 클릭 시 호출: DB에 예약 데이터 생성"""
    from state import get_current_reservation_user_id, BOOTH_ID
    user_id = get_current_reservation_user_id()
    
    print(f"[DEBUG /kiosk/reserve] 예약 시도 - Booth: {BOOTH_ID}, Song: {request.song_id}, User: {user_id}")
    
    try:
        new_reservation = models.Reservation(
            booth_id=BOOTH_ID,
            song_id=request.song_id,
            user_id=user_id,
            status="waiting"
        )
        db.add(new_reservation)
        db.commit()
        db.refresh(new_reservation)
        
        print(f"[SUCCESS /kiosk/reserve] DB 저장 완료: {BOOTH_ID}:{request.song_id}:{user_id}")
        return {
            "status": "success", 
            "reservation_key": f"{BOOTH_ID}:{request.song_id}:{user_id}"
        }
    except IntegrityError as e:
        db.rollback()
        print(f"[ERROR /kiosk/reserve] 데이터베이스 무결성 오류 발생: {e}")
        # 409 Conflict는 중복된 리소스 생성 시 적절한 HTTP 상태 코드입니다.
        raise HTTPException(status_code=409, detail=f"예약 중복 또는 제약 조건 위반: {str(e)}")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[ERROR /kiosk/reserve] SQLAlchemy 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"데이터베이스 연동 중 오류 발생: {str(e)}")
    except Exception as e: # 예상치 못한 다른 모든 오류를 처리합니다.
        db.rollback()
        print(f"[ERROR /kiosk/reserve] DB 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=f"예약 중 오류 발생: {str(e)}")

@router.post("/start")
def start_song_endpoint(song_id: int, db: Session = Depends(get_db)):
    """노래 시작 버튼 클릭 시 호출: DB 상태를 waiting -> playing으로 변경"""
    from state import BOOTH_ID
    
    print(f"[DEBUG /kiosk/start] 노래 시작 처리 - Booth: {BOOTH_ID}, Song: {song_id}")
    
    # 대기 중인 예약 중 가장 먼저 생성된 것을 찾음
    reservation = db.query(models.Reservation).filter(
        models.Reservation.booth_id == BOOTH_ID,
        models.Reservation.song_id == song_id,
        models.Reservation.status == "waiting"
    ).order_by(models.Reservation.created_at.asc()).first()
    
    if not reservation:
        print(f"[WARN /kiosk/start] 대기 중인 예약 정보를 찾을 수 없음: Song {song_id}")
        raise HTTPException(status_code=404, detail="대기 중인 예약 정보가 없습니다.")
        
    try:
        reservation.status = "playing"
        db.commit()
        db.refresh(reservation)
        print(f"[SUCCESS /kiosk/start] 상태 변경 완료: waiting -> playing")
        return {"status": "success", "message": "노래 시작 상태로 업데이트되었습니다."}
    except Exception as e:
        db.rollback()
        print(f"[ERROR /kiosk/start] DB 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"업데이트 중 오류 발생: {str(e)}")
