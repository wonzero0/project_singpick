import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# 보안 설정 (사용자 설정에 맞춰 수정 가능)
SECRET_KEY = "your-very-secret-key-for-iot-project" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 

# 🚨 2. 복잡한 폼 대신 심플한 토큰 입력창을 띄우는 설정입니다.
security = HTTPBearer(auto_error=False)

# 토큰 생성 함수 (기존과 동일)
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 🚨 3. 선택적 인증 함수 수정: HTTPBearer에서 토큰 알맹이만 빼오도록 변경
def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        return None  # 토큰이 없어도 에러 대신 None을 돌려줌
    
    # Bearer 띄어쓰기 뒤에 있는 진짜 토큰 문자열만 가져옵니다.
    token = credentials.credentials 
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None  # 토큰이 유효하지 않아도 에러 대신 None을 돌려줌