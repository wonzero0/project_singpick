import os
import sys
from datetime import datetime
from sqlalchemy.exc import IntegrityError

# 프로젝트 루트를 sys.path에 추가하여 database 및 models 모듈을 임포트할 수 있도록 합니다.
# 이 스크립트가 project_singpick 디렉토리 내에 있다고 가정합니다.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from database import engine, Base, SessionLocal
import models

def debug_reservation_interaction():
    print("--- 예약 테이블 디버깅 시작 ---")

    # 1. 모든 테이블 생성 시도 (존재하지 않을 경우)
    #    경고: 이 함수는 테이블이 존재하지 않을 경우 새로 생성합니다.
    #    만약 기존 데이터가 있고 스키마가 다를 경우 문제가 발생할 수 있습니다.
    #    운영 환경에서는 Alembic과 같은 마이그레이션 도구를 사용해야 합니다.
    print("모든 테이블 생성 시도 중 (존재하지 않을 경우)...")
    Base.metadata.create_all(bind=engine)
    print("테이블 생성 시도 완료.")

    db = SessionLocal()
    try:
        # 2. 예약 생성을 위한 샘플 노래 및 부스 확인/생성
        print("\n샘플 노래 및 부스 확인 중...")
        sample_song = db.query(models.Song).filter(models.Song.ky_number == 12345).first()
        if not sample_song:
            sample_song = models.Song(title="테스트 노래", singer="테스트 가수", ky_number=12345)
            db.add(sample_song)
            db.commit()
            db.refresh(sample_song)
            print(f"  - 샘플 노래 생성됨: {sample_song.title}")
        else:
            print(f"  - 기존 샘플 노래 발견: {sample_song.title}")

        sample_booth = db.query(models.Booth).filter(models.Booth.booth_id == 99).first()
        if not sample_booth:
            sample_booth = models.Booth(booth_id=99, name="테스트 부스", status="empty")
            db.add(sample_booth)
            db.commit()
            db.refresh(sample_booth)
            print(f"  - 샘플 부스 생성됨: {sample_booth.name}")
        else:
            print(f"  - 기존 샘플 부스 발견: {sample_booth.name}")

        # 3. 샘플 예약 삽입 시도
        print("\n샘플 예약 삽입 시도 중...")
        test_user_id = "debug_user_001"
        test_booth_id = sample_booth.booth_id
        test_song_id = sample_song.song_id

        # 복합 기본키 중복 방지를 위해 기존 예약이 있는지 확인
        existing_reservation = db.query(models.Reservation).filter(
            models.Reservation.booth_id == test_booth_id,
            models.Reservation.song_id == test_song_id,
            models.Reservation.user_id == test_user_id
        ).first()

        if existing_reservation:
            print(f"  - 사용자 '{test_user_id}'의 부스 {test_booth_id} 노래 {test_song_id}에 대한 예약이 이미 존재합니다. 삽입 건너뜀.")
        else:
            new_reservation = models.Reservation(
                booth_id=test_booth_id,
                song_id=test_song_id,
                user_id=test_user_id,
                status="waiting"
            )
            db.add(new_reservation)
            db.commit()
            db.refresh(new_reservation)
            print(f"  - 새 예약 성공적으로 삽입: 부스 ID={new_reservation.booth_id}, 노래 ID={new_reservation.song_id}, 사용자 ID={new_reservation.user_id}, 상태={new_reservation.status}")

        # 4. 모든 예약 조회
        print("\n모든 예약 조회 결과:")
        all_reservations = db.query(models.Reservation).all()
        if all_reservations:
            for res in all_reservations:
                print(f"  - 예약: 부스 ID={res.booth_id}, 노래 ID={res.song_id}, 사용자 ID={res.user_id}, 상태={res.status}, 생성 시각={res.created_at}")
        else:
            print("  - 예약이 없습니다.")

        # 5. 특정 부스 ID로 예약 조회
        print(f"\n부스 ID {test_booth_id}에 대한 예약 조회 결과:")
        booth_reservations = db.query(models.Reservation).filter(models.Reservation.booth_id == test_booth_id).all()
        if booth_reservations:
            for res in booth_reservations:
                print(f"  - 부스 예약: 부스 ID={res.booth_id}, 노래 ID={res.song_id}, 사용자 ID={res.user_id}, 상태={res.status}")
        else:
            print(f"  - 부스 ID {test_booth_id}에 대한 예약이 없습니다.")

    except IntegrityError as e:
        db.rollback()
        print(f"❌ 데이터베이스 무결성 오류 발생: {e}")
        print("이는 중복된 기본키를 삽입하거나 다른 제약 조건을 위반할 때 발생할 수 있습니다.")
    except Exception as e:
        db.rollback()
        print(f"❌ 예상치 못한 오류 발생: {e}")
    finally:
        db.close()
    print("\n--- 예약 테이블 디버깅 완료 ---")

if __name__ == "__main__":
    debug_reservation_interaction()