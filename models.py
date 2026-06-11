from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, PrimaryKeyConstraint
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
# 4. 예약 (복합 기본키: booth_id, song_id, user_id)
# =========================

class Reservation(Base):
    __tablename__ = "reservations"

    # 사용자 코멘트에 따라 복합 기본키 (booth_id, song_id, user_id)를 사용하도록 수정합니다.
    # 만약 'id' 컬럼을 별도의 고유 식별자로 유지하고 싶다면, 'id = Column(Integer, unique=True, autoincrement=True)'와 같이 변경해야 합니다.
    __table_args__ = (
        PrimaryKeyConstraint('booth_id', 'song_id', 'user_id'),
    )

    booth_id = Column(Integer, index=True) # 복합 기본키의 일부로, 성능 향상을 위해 인덱스 추가
    song_id = Column(Integer, index=True) # 복합 기본키의 일부로, 성능 향상을 위해 인덱스 추가
    user_id = Column(String(50), index=True) # 복합 기본키의 일부로, 성능 향상을 위해 인덱스 추가
    status = Column(String(20), default="waiting")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# =========================
# 5. AI 분석 결과
# =========================
class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=True)
    filename = Column(String(100))
    score = Column(Float)
    pitch_hz_avg = Column(Float)
    tempo_bpm = Column(Float)
    volume_rms_avg = Column(Float)
    feedback = Column(String(500))
    feature_path = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())