from led_controller import start_led, stop_led
import time

print("노래 시작")

start_led()

time.sleep(10)

print("노래 종료")

stop_led()