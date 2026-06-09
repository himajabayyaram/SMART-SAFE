import cv2
import random
import mediapipe as mp
import time
import math

mp_face_mesh=mp.solutions.face_mesh

def dist(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def generate_challenge_frames():
    challenges = [
        "MOVE AWAY",
        "MOVE UP",
        "MOVE DOWN",
        "MOVE CLOSER",
        "MOVE LEFT",
        "MOVE RIGHT"
    ]

    challenge = random.choice(challenges)

    max_attempts = 3
    attempts = 0

    HOLD_SECONDS = 1.5
    TIME_LIMIT = 8
    TOTAL_TIME_LIMIT = 120
    total_start_time = time.time()

    DARK = (40, 40, 40)
    YELLOW = (0, 255, 255)
    GREEN = (0, 255, 0)
    RED = (0, 0, 255)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh:

        while attempts < max_attempts:
            start_time = time.time()
            hold_start = None
            success = False

            base_nose_x = None
            base_nose_y = None
            base_face_width = None

            while True:
                ret, frame = cap.read()
                if not ret:
                    continue

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = face_mesh.process(rgb)

                remaining = int(TOTAL_TIME_LIMIT - (time.time() - total_start_time))

                if remaining <= 0:
                    cv2.putText(frame, "ACCESS DENIED", (80, 300),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, RED, 3)

                    cv2.imwrite("challenge_failed.jpg", frame)

                    with open("challenge_result.txt", "w") as f:
                        f.write("denied")

                    ret, buffer = cv2.imencode(".jpg", frame)
                    if ret:
                        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"

                    cap.release()
                    return

                cv2.putText(frame, f"Challenge: {challenge}", (30, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, YELLOW, 2)

                cv2.putText(frame, f"Attempt: {attempts + 1}/3", (30, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, DARK, 2)

                cv2.putText(frame, "Hold movement for 1.5 sec", (30, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, DARK, 2)

                cv2.putText(frame, f"Time left: {remaining}s", (30, 160),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, DARK, 2)

                detected_correct_expression = False

                if result.multi_face_landmarks:
                    lm = result.multi_face_landmarks[0].landmark

                    nose = lm[1]
                    left_cheek = lm[234]
                    right_cheek = lm[454]

                    face_width = dist(left_cheek, right_cheek)

                    if base_nose_x is None:
                        base_nose_x = nose.x
                        base_nose_y = nose.y
                        base_face_width = face_width

                    move_closer = face_width > base_face_width + 0.04
                    move_away = face_width < base_face_width - 0.04
                    move_left = nose.x < base_nose_x - 0.05
                    move_right = nose.x > base_nose_x + 0.05
                    move_up = nose.y < base_nose_y - 0.05
                    move_down = nose.y > base_nose_y + 0.05

                    if challenge == "MOVE CLOSER":
                        detected_correct_expression = move_closer
                    elif challenge == "MOVE AWAY":
                        detected_correct_expression = move_away
                    elif challenge == "MOVE LEFT":
                        detected_correct_expression = move_left
                    elif challenge == "MOVE RIGHT":
                        detected_correct_expression = move_right
                    elif challenge == "MOVE UP":
                        detected_correct_expression = move_up
                    elif challenge == "MOVE DOWN":
                        detected_correct_expression = move_down

                    if detected_correct_expression:
                        if hold_start is None:
                            hold_start = time.time()

                        held = time.time() - hold_start

                        cv2.putText(frame, f"Good! Hold... {held:.1f}s", (30, 210),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, GREEN, 2)

                        if held >= HOLD_SECONDS:
                            success = True
                            break
                    else:
                        hold_start = None
                        cv2.putText(frame, "Not detected yet", (30, 210),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, RED, 2)

                else:
                    cv2.putText(frame, "No face detected", (30, 210),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, RED, 2)

                if time.time() - start_time > TIME_LIMIT:
                    attempts += 1
                    cv2.putText(frame, "TRY AGAIN", (130, 300),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, RED, 3)
                    break

                ret, buffer = cv2.imencode(".jpg", frame)
                if ret:
                    yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"

            if success:
                cv2.putText(frame, "ACCESS GRANTED", (70, 300),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, GREEN, 3)

                with open("challenge_result.txt", "w") as f:
                    f.write("granted")

                ret, buffer = cv2.imencode(".jpg", frame)
                if ret:
                    yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"

                time.sleep(2)
                cap.release()
                return

        cv2.putText(frame, "ACCESS DENIED", (80, 300),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, RED, 3)

        cv2.imwrite("challenge_failed.jpg", frame)

        with open("challenge_result.txt", "w") as f:
            f.write("denied")

        ret, buffer = cv2.imencode(".jpg", frame)
        if ret:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"

        time.sleep(2)
        cap.release()