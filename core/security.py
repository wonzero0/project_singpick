import base64
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
SECRET_KEY = (os.getenv("AES_SECRET_KEY") or "test_secret_key").encode()

class AESCipher:
    def __init__(self, key):
        self.key = key

    def encrypt(self, raw_text):
        if not raw_text: return None
        iv = os.urandom(16)  # 매번 새로운 IV 생성 (보안 핵심!)
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