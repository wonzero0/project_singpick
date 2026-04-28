from core.security import cipher, SECRET_KEY
import os

def run_final_test():
    print("--- 🛡️ Sing Pick 보안 시스템 최종 테스트 ---")
    
    # 1. .env 키 로드 확인
    if SECRET_KEY:
        # 보안을 위해 앞 4자리만 출력해봅니다.
        print(f"✅ .env 키 로드 성공! (Key 시작부분: {SECRET_KEY[:4].decode()}...)")
    else:
        print("❌ .env 키 로드 실패! 파일을 확인해주세요.")
        return

    # 2. 테스트 데이터
    original_data = "C3-G5 / Vocal: Power"
    
    # 3. 암호화 수행
    try:
        encrypted = cipher.encrypt(original_data)
        print(f"🔒 암호화 완료: {encrypted}")
        
        # 4. 복호화 수행
        decrypted = cipher.decrypt(encrypted)
        print(f"🔓 복호화 완료: {decrypted}")
        
        if original_data == decrypted:
            print("\n✨ [최종 결과] 보안 모듈이 완벽하게 작동합니다!")
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")

if __name__ == "__main__":
    run_final_test()