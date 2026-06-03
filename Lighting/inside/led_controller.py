import serial
import platform
import time

port = 'COM4' if platform.system() == 'Windows' else '/dev/ttyACM0'
#arduino = serial.Serial(port, 9600)

time.sleep(2)

# 🎵 노래 시작
def start_led():
    arduino.write(b'PLAY\n')

# ⏹ 노래 종료
def stop_led():
    arduino.write(b'STOP\n')