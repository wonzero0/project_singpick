from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import hashlib

# 팀원이 .env 파일 주면 os.getenv("SECRET_KEY")로 바꾸기
SECRET_KEY = "my_super_secret_key_for_aes_256!!" 

# 키를 32바이트(256비트)로 맞추는 작업
def get_key():
    return hashlib.sha256(SECRET_KEY.encode()).digest()

# 1. 암호화 함수 (문자 -> 암호)
def aes_encrypt(plain_text: str):
    # 친구가 추가한 예외 처리: 데이터가 없을 경우 방어
    if plain_text is None:
        raise ValueError("aes_encrypt에 전달된 값이 None입니다.")
    if not isinstance(plain_text, str):
        plain_text = str(plain_text)

    key = get_key()
    # CBC 모드 사용 (보안성 높음), IV는 0으로 고정
    iv = bytes([0] * 16) 
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_bytes = cipher.encrypt(pad(plain_text.encode("utf-8"), AES.block_size))
    # DB에 저장하기 좋게 문자열로 변환
    return base64.b64encode(encrypted_bytes).decode("utf-8")

# 2. 복호화 함수 (암호 -> 문자)
def aes_decrypt(encrypted_text: str):
    try:
        if encrypted_text is None:
            raise ValueError("aes_decrypt에 전달된 값이 None입니다.")

        key = get_key()
        iv = bytes([0] * 16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decoded_bytes = base64.b64decode(encrypted_text)
        decrypted_bytes = unpad(cipher.decrypt(decoded_bytes), AES.block_size)
        return decrypted_bytes.decode("utf-8")
    except Exception:
        return "복호화 실패"

if __name__ == "__main__":
    original = "01012345678"
    encrypted = aes_encrypt(original)
    decrypted = aes_decrypt(encrypted)

    print(f"원본: {original}")
    print(f"암호화: {encrypted}")
    print(f"복호화: {decrypted}")