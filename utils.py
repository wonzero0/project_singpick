from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import hashlib

SECRET_KEY = "my_super_secret_key_for_aes_256!!"

def get_key():
    return hashlib.sha256(SECRET_KEY.encode()).digest()

def aes_encrypt(plain_text: str):
    if plain_text is None:
        raise ValueError("aes_encrypt에 전달된 값이 None입니다.")
    if not isinstance(plain_text, str):
        plain_text = str(plain_text)

    key = get_key()
    iv = bytes([0] * 16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_bytes = cipher.encrypt(pad(plain_text.encode("utf-8"), AES.block_size))
    return base64.b64encode(encrypted_bytes).decode("utf-8")

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