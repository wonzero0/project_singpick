from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from database import get_db
import models
from utils import aes_encrypt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/users", tags=["👤 Users (회원관리)"])

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

# -------------------------------
# Pydantic 모델
# -------------------------------
class UserCreate(BaseModel):
    user_id: str = Field(..., pattern=r"^[a-zA-Z]{4,20}$")
    phone: str = Field(..., pattern=r"^010\d{8}$")
    password: str = Field(..., pattern=r"^\d{1,6}$")

    @field_validator("user_id")
    def validate_user_id(cls, v):
        if not v.isalpha():
            raise ValueError("아이디는 영문만 가능합니다.")
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
        safe_password = truncate_password(user_data.password)
        hashed_password = pwd_context.hash(safe_password)
        new_user = models.User(user_id=user_data.user_id, phone=crypto_phone, password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"status": "success", "message": "회원가입 완료", "user_id": new_user.user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------
# 로그인
# -------------------------------
@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    try:
        crypto_phone = aes_encrypt(user_data.phone)
        db_user = db.query(models.User).filter(models.User.phone == crypto_phone).first()
        if not db_user:
            raise HTTPException(status_code=401, detail="전화번호 또는 비밀번호가 일치하지 않습니다.")
        safe_password = truncate_password(user_data.password)
        if not pwd_context.verify(safe_password, db_user.password):
            raise HTTPException(status_code=401, detail="전화번호 또는 비밀번호가 일치하지 않습니다.")
        return {"status": "success", "message": f"안녕하세요, {db_user.user_id}님!", "user_id": db_user.user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------
# 내 점수 기록 조회
# -------------------------------
@router.get("/{user_id}/history")
def get_user_history(user_id: str, db: Session = Depends(get_db)):
    history = db.query(models.AnalysisResult).filter(models.AnalysisResult.user_id == user_id).order_by(models.AnalysisResult.id.desc()).all()
    return {"status": "success", "data": history}