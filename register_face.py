import cv2
import time
from arduino_control import start_registration, face_saved

front_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
profile_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_profileface.xml"
)

def generate_register_frames():
    cap = cv2.VideoCapture(0)
    start_registration()

    count = 1
    max_images = 35
    smooth_box = None
    alpha = 0.8
    last_save_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = []

        for f in front_cascade.detectMultiScale(gray, 1.1, 3, minSize=(60, 60)):
            faces.append(f)

        for f in profile_cascade.detectMultiScale(gray, 1.1, 3, minSize=(60, 60)):
            faces.append(f)

        flipped = cv2.flip(gray, 1)
        for (x, y, w, h) in profile_cascade.detectMultiScale(flipped, 1.1, 3, minSize=(60, 60)):
            real_x = gray.shape[1] - x - w
            faces.append((real_x, y, w, h))

        if faces:
            best_face = max(faces, key=lambda r: r[2] * r[3])

            if smooth_box is None:
                smooth_box = list(best_face)
            else:
                for i in range(4):
                    smooth_box[i] = int(alpha * smooth_box[i] + (1 - alpha) * best_face[i])

        if smooth_box is not None:
            x, y, w, h = smooth_box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            if time.time() - last_save_time >= 0.5 and count <= max_images:
                face_img = gray[y:y+h, x:x+w]
                cv2.imwrite(f"owner_{count}.jpg", face_img)
                face_saved()
                count += 1
                last_save_time = time.time()

        cv2.putText(frame, f"Captured: {count-1}/{max_images}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.putText(frame, "Registering owner face...", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        if count > max_images:
            cv2.putText(frame, "REGISTRATION DONE", (100, 250),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

            ret, buffer = cv2.imencode(".jpg", frame)
            if ret:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"

            time.sleep(2)
            cap.release()
            return

        ret, buffer = cv2.imencode(".jpg", frame)
        if ret:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"