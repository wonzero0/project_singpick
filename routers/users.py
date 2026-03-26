from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from database import get_db
import models
from utils import aes_encrypt
import bcrypt 
from typing import Optional 
from core.auth import create_access_token, get_current_user_optional
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

# ===============================
# 1️⃣ 회원가입 API
# ===============================

@router.post("/signup", summary="회원가입")
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        crypto_phone = aes_encrypt(user_data.phone)
        existing_user = db.query(models.User).filter(models.User.phone == crypto_phone).first()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="이미 가입된 전화번호입니다."
            )

        password_bytes = user_data.password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

        new_user = models.User(
            user_id=user_data.user_id,
            phone=crypto_phone,
            password=hashed_password
        )

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

# ===============================
# 2️⃣ 로그인 API (보안 강화 버전)
# ===============================

@router.post("/login", summary="로그인")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    try:
        # 1. 전화번호 암호화 후 조회
        crypto_phone = aes_encrypt(user_data.phone)
        db_user = db.query(models.User).filter(models.User.phone == crypto_phone).first()

        # 2. 유저 검증 및 비밀번호 확인
        if not db_user or not bcrypt.checkpw(user_data.password.encode('utf-8'), db_user.password.encode('utf-8')):
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="전화번호 또는 비밀번호가 일치하지 않습니다."
            )

        # 3. 로그인 성공 시 JWT 토큰 생성 (핵심!)
        access_token = create_access_token(data={"sub": db_user.user_id})

        return {
            "status": "success",
            "message": f"안녕하세요, {db_user.user_id}님!",
            "access_token": access_token,  # 발급된 토큰 전달
            "token_type": "bearer",
            "user_id": db_user.user_id
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print("로그인 오류:", e)
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")

# ===============================
# 3️⃣ 내 점수 기록 조회
# ===============================

@router.get("/history", summary="마이페이지 - 내 과거 기록 조회")
def get_user_history(
    current_user: Optional[str] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    # 1. 로그인 확인 (비회원 차단)
    if not current_user:
        return {"status": "fail", "message": "로그인이 필요한 서비스입니다."}

    # 2. DB 조회 (토큰에서 뽑아낸 안전한 current_user 사용)
    records = db.query(models.AnalysisResult)\
                .filter(models.AnalysisResult.user_id == current_user)\
                .order_by(models.AnalysisResult.id.desc())\
                .all()

    # 3. 프론트엔드가 화면(history)에 뿌리기 편하게 가공
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
            # 피드백 텍스트가 너무 길면 UI가 망가지므로 100자까지만 자르고 "..." 붙이기
            "feedback_summary": record.feedback[:100] + "..." if record.feedback else "피드백 없음"
        })

    # 4. JSON 최종 응답
    return {
        "status": "success",
        "message": f"{current_user}님의 누적 기록을 불러왔습니다.",
        "data": {
            "history": history_list
        }
    }
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
