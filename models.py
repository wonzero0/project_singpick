from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, PrimaryKeyConstraint, Text
from sqlalchemy.sql import func
from database import Base

# =========================
# 1. 사용자 테이블
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50))
    phone = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    remaining_songs = Column(Integer, default=0)

# =========================
# 2. 노래방 부스
# =========================
class Booth(Base):
    __tablename__ = "booths"

    booth_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    status = Column(String(20), default="empty")

# =========================
# 3. 노래 데이터
# =========================
class Song(Base):
    __tablename__ = "songs"

    song_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True)
    singer = Column(String(50), index=True)
    ky_number = Column(Integer, unique=True)

# =========================
# 4. 예약 (복합 기본키: booth_id, song_id, user_id)
# =========================

class Reservation(Base):
    __tablename__ = "reservations"

    # 중복 예약 허용 및 안정적인 연동을 위해 고유 ID를 기본키로 설정합니다.
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    booth_id = Column(Integer, index=True)
    song_id = Column(Integer, index=True)
    user_id = Column(String(50), index=True)
    status = Column(String(20), default="waiting")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# =========================
# 5. AI 분석 결과
# =========================
class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), nullable=True)
    filename = Column(String(255), nullable=True) # 파일명이 없을 때를 대비해 nullable=True 추가
    score = Column(Float, nullable=True)          # nullable=True 추가
    pitch_hz_avg = Column(Float, nullable=True)
    tempo_bpm = Column(Float, nullable=True)
    volume_rms_avg = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)        # String(500) 대신 Text로 변경 (용량 무제한급)
    feature_path = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())