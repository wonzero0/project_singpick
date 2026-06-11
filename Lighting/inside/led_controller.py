import serial
import platform
import time
import os

# 1. 포트 설정
port = os.getenv("INTERNAL_LED_PORT", 'COM4' if platform.system() == 'Windows' else '/dev/ttyACM0')

# 2. 아두이노 객체를 None으로 초기화
arduino = None

# 3. 연결 시도 (예외 처리 추가)
try:
    # 9600 baud rate로 시리얼 포트 열기 시도
    arduino = serial.Serial(port, 9600, timeout=1)
    time.sleep(2) # 아두이노 부팅 대기
    print(f"✅ 아두이노 연결 성공: {port}")
except (serial.SerialException, FileNotFoundError):
    print(f"⚠️ 경고: 포트 {port}를 찾을 수 없습니다. LED 기능을 비활성화합니다.")

def start_led():
    if arduino is not None:
        try:
            arduino.flush()
            arduino.write(b'PLAY\n')
        except Exception as e:
            print(f"LED 전송 오류: {e}")
    else:
        print("LED 모듈이 연결되지 않아 동작을 건너뜁니다 (PLAY).")

def stop_led():
    if arduino is not None:
        try:
            arduino.flush()
            arduino.write(b'STOP\n')
        except Exception as e:
            print(f"LED 전송 오류: {e}")
    else:
        print("LED 모듈이 연결되지 않아 동작을 건너뜁니다 (STOP).")
