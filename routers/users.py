from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from database import get_db
import models
from utils import aes_encrypt
from typing import Optional 
from core.auth import create_access_token, get_current_user_optional
import bcrypt  # 🚨 에러투성이 passlib을 버리고 순수 bcrypt로 복구!

router = APIRouter(prefix="/users", tags=["👤 Users (회원관리)"])

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

# ===============================
# 1️⃣ 회원가입 API (순수 bcrypt로 복구)
# ===============================
@router.post("/signup", summary="회원가입")
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        crypto_phone = aes_encrypt(user_data.phone)
        if db.query(models.User).filter(models.User.phone == crypto_phone).first():
            raise HTTPException(status_code=400, detail="이미 가입된 전화번호입니다.")
        
        # 원영님의 오리지널 로직: 순수 bcrypt 해싱 (버그 원천 차단)
        password_bytes = user_data.password.encode('utf-8')
        if len(password_bytes) > 72:  # 만약 진짜로 72바이트가 넘으면 안전하게 자르기
            password_bytes = password_bytes[:72]
            
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        new_user = models.User(user_id=user_data.user_id, phone=crypto_phone, password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {"status": "success", "message": "회원가입 완료", "user_id": new_user.user_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===============================
# 2️⃣ 로그인 API (순수 bcrypt로 복구)
# ===============================
@router.post("/login", summary="로그인")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    try:
        crypto_phone = aes_encrypt(user_data.phone)
        db_user = db.query(models.User).filter(models.User.phone == crypto_phone).first()

        if not db_user:
            raise HTTPException(status_code=401, detail="전화번호 또는 비밀번호가 일치하지 않습니다.")

        # 비밀번호 검증도 순수 bcrypt로 처리
        password_bytes = user_data.password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            
        if not bcrypt.checkpw(password_bytes, db_user.password.encode('utf-8')):
            raise HTTPException(status_code=401, detail="전화번호 또는 비밀번호가 일치하지 않습니다.")

        # 로그인 성공 시 JWT 토큰 생성
        access_token = create_access_token(data={"sub": db_user.user_id})

        return {
            "status": "success",
            "message": f"안녕하세요, {db_user.user_id}님!",
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": db_user.user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print("로그인 오류:", e)
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")

# ===============================
# 3️⃣ 내 점수 기록 조회 (그대로 유지)
# ===============================
@router.get("/history", summary="마이페이지 - 내 과거 기록 조회")
def get_user_history(
    current_user: Optional[str] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    if not current_user:
        return {"status": "fail", "message": "로그인이 필요한 서비스입니다."}

    records = db.query(models.AnalysisResult)\
                .filter(models.AnalysisResult.user_id == current_user)\
                .order_by(models.AnalysisResult.id.desc())\
                .all()

    history_list = []
    for record in records:
        history_list.append({
            "id": record.id,
            "filename": record.filename,
            "scores": {
                "pitch": record.pitch_score,
                "tempo": record.tempo_score,
                "volume": record.volume_score
            },
            "feedback_summary": record.feedback[:100] + "..." if record.feedback else "피드백 없음"
        })

    return {
        "status": "success",
        "message": f"{current_user}님의 누적 기록을 불러왔습니다.",
        "data": {
            "history": history_list
        }
    }