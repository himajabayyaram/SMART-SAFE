import serial
import time

arduino = serial.Serial('COM8', 9600, timeout=1)
time.sleep(2)

arduino.write(b'SCAN\n')
print("Sent")

arduino.close()