import serial
import time

arduino = None

def connect():
    global arduino
    if arduino is None or not arduino.is_open:
        arduino = serial.Serial('COM8', 9600, timeout=1)
        time.sleep(2)

def send_command(cmd):
    connect()
    arduino.write((cmd + "\n").encode())

def start_scan():
    send_command("SCAN")

def next_step():
    send_command("EXPRESSION")

def system_ready():
    send_command("READY")
    
def access_granted():
    send_command("OPEN")

def access_denied():
    send_command("DENIED")

def next_challenge():
    send_command("CHALLENGE")

def start_registration():
    send_command("REGISTER")

def face_saved():
    send_command("SAVED")

def verifying():
    send_command("VERIFYING")