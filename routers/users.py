from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from database import get_db
import models
from utils import aes_encrypt
from typing import Optional 
from core.auth import create_access_token, get_current_user_optional
import bcrypt 
from datetime import datetime, timedelta

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
# 🚨 추가: 로그인 실패 횟수 및 차단 시간 기록용 딕셔너리 (메모리)
# ===============================
login_attempts = {}

# ===============================
# 2️⃣ 로그인 API (친절한 안내 문구 적용)
# ===============================
@router.post("/login", summary="로그인")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    try:
        crypto_phone = aes_encrypt(user_data.phone)
        
        # 1. 🛑 차단 상태인지 먼저 확인
        if crypto_phone in login_attempts:
            record = login_attempts[crypto_phone]
            if record["block_until"]:
                if datetime.now() < record["block_until"]:
                    remain_time = int((record["block_until"] - datetime.now()).total_seconds())
                    # 🌟 수정 1: 남은 시간 안내 문구
                    raise HTTPException(status_code=403, detail=f"5회 연속 실패로 로그인이 제한되었습니다.\n{remain_time}초 후에 다시 시도해주세요. 🚫")
                else:
                    login_attempts[crypto_phone] = {"count": 0, "block_until": None}

        db_user = db.query(models.User).filter(models.User.phone == crypto_phone).first()

        # 2. 🧐 로그인 실패 판별
        is_fail = False
        if not db_user:
            is_fail = True
        else:
            password_bytes = user_data.password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            if not bcrypt.checkpw(password_bytes, db_user.password.encode('utf-8')):
                is_fail = True

        # 3. 📉 실패했을 경우의 처리
        if is_fail:
            if crypto_phone not in login_attempts:
                login_attempts[crypto_phone] = {"count": 1, "block_until": None}
            else:
                login_attempts[crypto_phone]["count"] += 1
            
            fail_count = login_attempts[crypto_phone]["count"]
            
            if fail_count >= 5:
                login_attempts[crypto_phone]["block_until"] = datetime.now() + timedelta(minutes=1)
                # 🌟 수정 2: 5회 딱 틀렸을 때 뜨는 문구
                raise HTTPException(status_code=403, detail="5회 연속 실패하여 1분간 로그인이 제한됩니다. 🚫")
            else:
                # 🌟 수정 3: 1~4회 틀렸을 때 미리 경고해 주는 문구
                raise HTTPException(status_code=401, detail=f"정보가 일치하지 않습니다.\n(5회 실패 시 1분간 로그인이 제한됩니다. 실패: {fail_count}/5)")

        # 4. 🎉 성공했을 경우: 카운트 싹 다 깨끗하게 초기화
        login_attempts[crypto_phone] = {"count": 0, "block_until": None}

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


# ===============================
# 4️⃣ 분석 결과 DB 저장 API (새로 추가)
# ===============================
class ResultSaveRequest(BaseModel):
    user_id: str
    filename: str
    pitch_score: int
    tempo_score: int
    volume_score: int
    feedback: str

@router.post("/history/save", summary="분석 결과 DB에 저장하기")
def save_analysis_result(data: ResultSaveRequest, db: Session = Depends(get_db)):
    try:
        # DB의 AnalysisResult 테이블에 새 줄 만들기
        new_record = models.AnalysisResult(
            user_id=data.user_id,
            filename=data.filename,
            pitch_score=data.pitch_score,
            tempo_score=data.tempo_score,
            volume_score=data.volume_score,
            feedback=data.feedback
        )
        
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        
        return {"status": "success", "message": "성공적으로 저장되었습니다."}
        
    except Exception as e:
        db.rollback() # 에러 나면 되돌리기
        print("결과 저장 중 에러:", e)
        raise HTTPException(status_code=500, detail="데이터베이스 저장에 실패했습니다.")