import serial
import time

arduino = serial.Serial('/dev/cu.usbmodem1101', 9600)

time.sleep(2)

# 🎵 노래 시작
def start_led():
    arduino.write(b'PLAY\n')

# ⏹ 노래 종료
def stop_led():
    arduino.write(b'STOP\n')