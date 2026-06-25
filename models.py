from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, PrimaryKeyConstraint, Text, JSON, UniqueConstraint
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
    filename = Column(String(255), nullable=True)
    score = Column(Float, nullable=True)          
    pitch_hz_avg = Column(Float, nullable=True)
    tempo_bpm = Column(Float, nullable=True)
    volume_rms_avg = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)        
    feature_path = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ==================================================
# 🌟 6. 사용자 누적 추천 데이터 테이블 (Web.tsx 연동용)
# ==================================================
class UserRecommendation(Base):
    __tablename__ = "user_recommendations"

    user_id = Column(String(50), primary_key=True, nullable=False)
    recommended_songs = Column(JSON, nullable=False)       
    recommended_artists = Column(JSON, nullable=False)     
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ==================================================
# 🌟 [수정 완료] 7. 라즈베리파이 연동용 음원 임베딩 테이블
# ==================================================
class SongEmbedding(Base):
    __tablename__ = "song_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=True, index=True)            # user_id 추가
    analysis_result_id = Column(Integer, nullable=True)                # 분석 결과 매핑 ID 추가
    x = Column(Float, nullable=False)                                  # embedding_x 대신 x
    y = Column(Float, nullable=False)                                  # embedding_y 대신 y
    z = Column(Float, nullable=True, default=0.0)                      # embedding_z 대신 z
    created_at = Column(DateTime(timezone=True), server_default=func.now())