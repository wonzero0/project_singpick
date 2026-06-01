import serial
import platform

arduino = None
port = 'COM4' if platform.system() == 'Windows' else '/dev/ttyACM0'

try:
    arduino = serial.Serial(port, 9600)
except Exception as e:
    print("[Arduino] init failed:", e)
    arduino = None


def start_led():
    if arduino:
        arduino.write(b'PLAY\n')
    else:
        print("[Arduino] skip start_led (no device)")


def stop_led():
    if arduino:
        arduino.write(b'STOP\n')
    else:
        print("[Arduino] skip stop_led (no device)")