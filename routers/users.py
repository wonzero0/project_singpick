from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from database import get_db
import models
from utils import aes_encrypt
from routers.kiosk import current_kiosk_state
import bcrypt
from datetime import datetime, timedelta

router = APIRouter(prefix="/users", tags=["👤 Users (회원관리)"])

# 🛡️ [로그인 제한 시스템을 위한 메모리 저장소]
# 구조: {"전화번호": {"fail_count": 실패횟수, "lockout_until": 잠금해제시간}}
login_attempts = {}

# 비밀번호 안전하게 72바이트로 자르기
def truncate_password(password: str, max_bytes: int = 72) -> str:
    encoded = password.encode('utf-8')
    if len(encoded) <= max_bytes:
        return password
    truncated = encoded[:max_bytes]
    while True:
        try:
            return truncated.decode('utf-8')
        except UnicodeDecodeError:
            truncated = truncated[:-1]


def hash_password(password: str) -> str:
    safe_password = truncate_password(password)
    hashed = bcrypt.hashpw(safe_password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    safe_password = truncate_password(password)
    return bcrypt.checkpw(safe_password.encode('utf-8'), hashed_password.encode('utf-8'))

# -------------------------------
# Pydantic 모델
# -------------------------------
class UserCreate(BaseModel):
    user_id: str = Field(..., pattern=r"^[a-zA-Z0-9]{4,20}$")
    phone: str = Field(..., pattern=r"^010\d{8}$")
    password: str = Field(..., pattern=r"^\d{1,6}$")

    @field_validator("user_id")
    def validate_user_id(cls, v):
        if not v.isalnum():
            raise ValueError("아이디는 영문과 숫자만 가능합니다.")
        return v

class UserLogin(BaseModel):
    phone: str = Field(..., pattern=r"^010\d{8}$")
    password: str

# -------------------------------
# 회원가입
# -------------------------------
@router.post("/signup")
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        crypto_phone = aes_encrypt(user_data.phone)
        if db.query(models.User).filter(models.User.phone == crypto_phone).first():
            raise HTTPException(status_code=400, detail="이미 가입된 전화번호입니다.")
        hashed_password = hash_password(user_data.password)
        new_user = models.User(user_id=user_data.user_id, phone=crypto_phone, password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"status": "success", "message": "회원가입 완료", "user_id": new_user.user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------
# 로그인 (5회 실패 시 1분 차단 로직 복구 완료!)
# -------------------------------
@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    phone = user_data.phone
    now = datetime.now()

    # 1. 해당 전화번호의 계정이 현재 잠금 상태인지 먼저 체크합니다.
    if phone in login_attempts:
        attempt_info = login_attempts[phone]
        if attempt_info["lockout_until"] and now < attempt_info["lockout_until"]:
            remaining_time = int((attempt_info["lockout_until"] - now).total_seconds())
            raise HTTPException(
                status_code=403, 
                detail=f"로그인 5회 실패로 인해 계정이 잠겼습니다. {remaining_time}초 후 다시 시도해주세요."
            )
        
        # 잠금 시간이 지났다면 실패 횟수와 잠금 상태를 초기화해줍니다.
        if attempt_info["lockout_until"] and now >= attempt_info["lockout_until"]:
            login_attempts[phone] = {"fail_count": 0, "lockout_until": None}

    try:
        crypto_phone = aes_encrypt(phone)
        db_user = db.query(models.User).filter(models.User.phone == crypto_phone).first()
        
        # 존재하지 않는 회원 정보이거나 비밀번호가 틀렸을 때의 공통 예외 처리
        if not db_user or not verify_password(user_data.password, db_user.password):
            
            # 실패 기록 관리
            if phone not in login_attempts:
                login_attempts[phone] = {"fail_count": 1, "lockout_until": None}
            else:
                login_attempts[phone]["fail_count"] += 1

            # 실패 횟수가 5회에 도달하면 1분간 잠금 타임스탬프를 찍어버립니다.
            if login_attempts[phone]["fail_count"] >= 5:
                login_attempts[phone]["lockout_until"] = now + timedelta(minutes=1)
                raise HTTPException(
                    status_code=403,
                    detail="비밀번호를 5회 연속 틀렸습니다. 보안을 위해 1분간 로그인이 제한됩니다."
                )

            current_fails = login_attempts[phone]["fail_count"]
            raise HTTPException(
                status_code=401, 
                detail=f"전화번호 또는 비밀번호가 일치하지 않습니다. (현재 {current_fails}/5회 실패)"
            )

        # 2. 로그인 최종 성공 시 해당 전화번호의 실패 기록을 완전히 삭제(초기화)합니다.
        if phone in login_attempts:
            del login_attempts[phone]

        # 🔥 현재 키오스크 사용자 상태 저장
        current_kiosk_state["status"] = "member"
        current_kiosk_state["user_id"] = db_user.user_id
        
        return {
            "status": "success",
            "message": f"안녕하세요, {db_user.user_id}님!",
            "user_id": db_user.user_id
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------
# 내 점수 기록 조회
# -------------------------------
@router.get("/{user_id}/history")
def get_user_history(user_id: str, db: Session = Depends(get_db)):
    history = db.query(models.AnalysisResult).filter(models.AnalysisResult.user_id == user_id).order_by(models.AnalysisResult.id.desc()).all()
    return {"status": "success", "data": history}