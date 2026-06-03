import base64
import os
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
# 원래 환경변수에서 가져온 값(문자열)을 바이트로 변환
raw_key = (os.getenv("AES_SECRET_KEY") or "test_secret_key").encode()

# 허용되는 AES 키 길이(16,24,32)가 아니면 자동 보정 시도
if len(raw_key) not in (16, 24, 32):
    # 흔한 원인: base64로 인코딩된 키를 넣었을 경우(예: 32바이트 -> base64 길이 44)
    try:
        decoded = base64.b64decode(raw_key)
        if len(decoded) in (16, 24, 32):
            SECRET_KEY = decoded
        else:
            # 그 외에는 SHA-256 해시를 사용해 32바이트 키를 생성
            SECRET_KEY = hashlib.sha256(raw_key).digest()
    except Exception:
        SECRET_KEY = hashlib.sha256(raw_key).digest()
else:
    SECRET_KEY = raw_key

class AESCipher:
    def __init__(self, key):
        self.key = key

    def encrypt(self, raw_text):
        if not raw_text: return None
        iv = os.urandom(16)  # 매번 새로운 IV 생성 
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        ct_bytes = cipher.encrypt(pad(raw_text.encode('utf-8'), AES.block_size))
        return base64.b64encode(iv + ct_bytes).decode('utf-8')

    def decrypt(self, enc_text):
        if not enc_text: return None
        enc_bytes = base64.b64decode(enc_text)
        iv = enc_bytes[:16]
        ct = enc_bytes[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return pt.decode('utf-8')

cipher = AESCipher(SECRET_KEY)