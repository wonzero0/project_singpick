from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
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
    tj_number = Column(Integer, unique=True)


# =========================
# 4. 예약
# =========================
class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    booth_id = Column(Integer)
    song_id = Column(Integer)
    status = Column(String(20), default="waiting")


# =========================
# 5. AI 분석 결과 (🔥 핵심 수정)
# =========================
class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String(50), nullable=True)
    filename = Column(String(100))

    # =========================
    # 🎯 점수 (통합)
    # =========================
    score = Column(Float)

    # =========================
    # 📊 분석 값
    # =========================
    pitch_hz_avg = Column(Float)
    tempo_bpm = Column(Float)
    volume_rms_avg = Column(Float)

    feedback = Column(String(500))
    feature_path = Column(String(200))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )