import os
import sys
from sqlalchemy.exc import IntegrityError

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from database import engine, SessionLocal
import models

def debug_analysis_db():
    print("--- 분석 결과(AnalysisResult) 테이블 디버깅 시작 ---")
    
    db = SessionLocal()
    try:
        # 1. 테스트용 데이터 생성
        test_user_id = "debug_user_999"
        
        new_analysis = models.AnalysisResult(
            user_id=test_user_id,
            filename="test_audio.wav",
            score=88.5,
            pitch_hz_avg=250.0,
            tempo_bpm=120.0,
            volume_rms_avg=0.5,
            feedback="테스트용 상세 피드백입니다."
        )
        
        # 2. DB 삽입 시도
        db.add(new_analysis)
        db.commit() # 여기서 실제 DB에 물리적으로 저장되는지 확인
        db.refresh(new_analysis)
        
        print(f"✅ 새 분석 결과 성공적으로 삽입: ID={new_analysis.id}, 사용자={new_analysis.user_id}, 점수={new_analysis.score}")

        # 3. 데이터 조회 확인
        print("\n--- DB 저장 데이터 조회 ---")
        results = db.query(models.AnalysisResult).filter(models.AnalysisResult.user_id == test_user_id).all()
        
        if results:
            for res in results:
                print(f"조회된 데이터: ID={res.id}, 사용자={res.user_id}, 피드백={res.feedback}, 생성시각={res.created_at}")
        else:
            print("❌ 데이터가 조회되지 않습니다 (저장 실패).")

    except IntegrityError as e:
        db.rollback()
        print(f"❌ 데이터베이스 무결성 오류 발생: {e}")
    except Exception as e:
        db.rollback()
        print(f"❌ 예상치 못한 오류 발생: {e}")
    finally:
        db.close()
    
    print("\n--- 분석 결과 디버깅 완료 ---")

if __name__ == "__main__":
    debug_analysis_db()