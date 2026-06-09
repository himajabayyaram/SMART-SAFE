import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import cv2
import subprocess
import time
from arduino_control import access_granted, access_denied,next_challenge, arduino

email_sent = False


def send_intruder_email(image_path):
    sender_email = "himajabayyaram06@gmail.com"
    sender_password = "eityfkcxatnaggme"
    with open("owner_email.txt", "r") as f:
        receiver_email = f.read().strip()

    msg = MIMEMultipart()
    msg["Subject"] = "⚠ Intruder Alert"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    body = "Unknown person detected at the gate."
    msg.attach(MIMEText(body, "plain"))

    with open(image_path, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-Disposition", "attachment", filename="intruder.jpg")
        msg.attach(img)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.send_message(msg)
    server.quit()

    print("Email Sent")


def generate_recognition_frames(on_success_url=None):
    global email_sent
    email_sent=False

    front = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    profile = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_profileface.xml"
    )

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("trainer.yml")

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    attempts = 0
    max_attempts = 3

    state = "WAIT_FACE"
    message_text = ""
    message_color = (255, 255, 255)
    message_until = 0

    smooth_box = None
    alpha = 0.85

    scan_start = None
    results = []

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        best_face = None

        if state not in ["DONE", "DENIED", "MESSAGE"]:
            faces = []

            for f in front.detectMultiScale(gray, 1.1, 3, minSize=(60, 60)):
                faces.append(f)

            for f in profile.detectMultiScale(gray, 1.1, 3, minSize=(60, 60)):
                faces.append(f)

            flipped = cv2.flip(gray, 1)
            for (x, y, w, h) in profile.detectMultiScale(flipped, 1.1, 3, minSize=(60, 60)):
                real_x = gray.shape[1] - x - w
                faces.append((real_x, y, w, h))

            if faces:
                best_face = max(faces, key=lambda r: r[2] * r[3])

                if smooth_box is None:
                    smooth_box = list(best_face)
                else:
                    for i in range(4):
                        smooth_box[i] = int(alpha * smooth_box[i] + (1 - alpha) * best_face[i])

        if state == "WAIT_FACE":
            cv2.putText(frame, "SHOW YOUR FACE", (120, 50),
                        cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 0), 2)

            if best_face is not None:
                state = "SCANNING"
                if arduino is not None:
                    arduino.write(b"SCAN\n")
                else:
                    print("Arduino not connected, skipping SCAN")
                scan_start = time.time()
                results = []

        elif state == "SCANNING":
            if best_face is None:
                state = "WAIT_FACE"
            else:
                x, y, w, h = smooth_box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

                cv2.putText(frame, "SCANNING...", (180, 50),
                            cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 255), 2)

                face = gray[y:y + h, x:x + w]
                face = cv2.equalizeHist(face)
                face = cv2.resize(face, (200, 200))

                label, confidence = recognizer.predict(face)

                ok = 1 if (label == 0 and confidence < 90) else 0
                results.append(ok)

                if time.time() - scan_start >= 2:
                    if sum(results) >= len(results) * 0.6:
                        state = "DONE"
                    else:
                        attempts += 1

                        if attempts >= max_attempts:
                            state = "DENIED"
                        else:
                            state = "MESSAGE"
                            message_text = f"TRY AGAIN ({attempts}/3)"
                            message_color = (0, 165, 255)
                            message_until = time.time() + 2

        elif state == "MESSAGE":
            cv2.putText(frame, message_text, (120, 240),
                        cv2.FONT_HERSHEY_DUPLEX, 1.4, message_color, 3)

            if time.time() >= message_until:
                state = "WAIT_FACE"
                smooth_box = None

        elif state == "DONE":
            cv2.putText(frame, "FACE AUTHORIZED", (80, 240),cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 255, 0), 4)
            cv2.putText(frame, "NEXT CHALLENGE", (90, 300),cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 255, 255), 3)

            ret, buffer = cv2.imencode(".jpg", frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )

            time.sleep(2)

            with open("recognition_done.txt", "w") as f:
                f.write("done")
            cap.release()
            break

        elif state == "DENIED":
            if not email_sent:
                access_denied()
                cv2.imwrite("intruder.jpg", frame)
                send_intruder_email("intruder.jpg")
                email_sent = True

            cv2.putText(frame, "ACCESS DENIED", (90, 240),
                        cv2.FONT_HERSHEY_DUPLEX, 1.7, (0, 0, 255), 4)

            cv2.putText(frame, "UNAUTHORIZED", (140, 300),
                        cv2.FONT_HERSHEY_DUPLEX, 1.1, (0, 0, 255), 3)

        cv2.putText(frame, "SMART SAFE", (10, 470),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        ret, buffer = cv2.imencode(".jpg", frame)

        if not ret:
            continue

        frame = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        )

    cap.release()