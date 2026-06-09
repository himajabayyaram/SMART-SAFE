from flask import Flask, render_template,Response,jsonify,redirect,request
import subprocess
import os
import time
import cv2
from recognize_face import send_intruder_email
from recognize_face import generate_recognition_frames
from challenge_auth import generate_challenge_frames
from register_face import generate_register_frames
from update_owner import delete_old_owner
from arduino_control import start_scan,access_granted,access_denied,next_challenge,start_registration,face_saved,next_step,system_ready,verifying
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD']=True
app.jinja_env.auto_reload=True

OWNER_REGISTERED_FILE = "owner_registered.txt"

def owner_already_registered():
    return os.path.exists("owner_registered.txt") and (
        os.path.exists("owner_1.jpg") or
        os.path.exists("owner_images") or
        os.path.exists("known_faces")
    )
    

def mark_owner_registered():
    with open(OWNER_REGISTERED_FILE, "w") as f:
        f.write("registered")

@app.route("/video_feed")
def video_feed():
    return Response(
        generate_recognition_frames(on_success_url="/challenge"),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/recognize")
def recognize():
    return render_template("recognize.html")

@app.route("/start_recognition")
def start_recognition():
    for file in ["recognition_done.txt","challenge_result.txt"]:
        if os.path.exists(file):
            os.remove(file)
    start_scan()
    return render_template(
        "recognize.html",
        message="Face scanning started. Please wait...",
        status="waiting"
    )

@app.route("/check_recognition")
def check_recognition():
    done = os.path.exists("recognition_done.txt")
    if done:
        next_step()
        return jsonify({"done": True,"result":"FACE_OK"})
    if os.path.exists("recognition_failed.txt"):
        os.remove('recognition_failed.txt')
        access_denied()
        return jsonify({"done":True,"result":"ACCESS_DENIED"})
    return jsonify({"done":False})


@app.route("/challenge")
def challenge():
    return render_template("challenge.html")

@app.route("/challenge_video_feed")
def challenge_video_feed():
    return Response(
        generate_challenge_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/check_challenge")
def check_challenge():
    if os.path.exists("challenge_result.txt"):
        with open("challenge_result.txt", "r") as f:
            result = f.read().strip()
        os.remove("challenge_result.txt")
        if result=="granted":
            access_granted()
        elif result=="denied":
            access_denied()
            if os.path.exists("challenge_failed.jpg"):
                send_intruder_email("challenge_failed.jpg")

        return jsonify({"done": True, "result": result})

    return jsonify({"done": False})

@app.route("/home_ready")
def home_ready():
    system_ready()
    return redirect("/")

@app.route("/register")
def register():
    if owner_already_registered():
        return render_template("register.html",message="Owner already registered. Please use Update Owner to register again.",status="already registered")
    return render_template("register.html")

count = 1
max_images = 35

@app.route("/register_video_feed")
def register_video_feed():
    return Response(generate_register_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


def generate_register_frames():
    global count,registration_done_sent
    registration_done_sent=False

    cap = cv2.VideoCapture(0)
    start_registration()
    while True:
        success, frame = cap.read()
        if not success:
            continue

        cv2.putText(frame, f"Captured: {count-1}/{max_images}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2)

        # AUTO SAVE every frame until 35 images
        if count <= max_images:
            cv2.imwrite(f"owner_{count}.jpg", frame)
            print("Saved:", count)
            count += 1
            time.sleep(0.3)

        
        if count > max_images and not registration_done_sent:
            face_saved()
            registration_done_sent=True
            mark_owner_registered()
        if count>max_images:
            cv2.putText(frame, "REGISTRATION DONE", (100, 300),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 3)

        ret, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


@app.route("/update_owner", methods=["GET", "POST"])
def update_owner():
    if request.method == "GET":
        verifying()
        return render_template("owner_quiz.html")
    
    q1 = request.form.get("q1", "").lower().strip()
    q2 = request.form.get("q2", "").lower().strip()
    q3 = request.form.get("q3", "").lower().strip()

    if q1 == "smart safe" and q2 == "blue" and q3 == "owner":
        return redirect("/change_email_choice")

    access_denied()
    return render_template("owner_quiz.html", error="Wrong answers. Access denied.")       

@app.route("/start_update_owner")
def start_update_owner():
    global count
    count=1
    import os, shutil

    paths_to_delete = [
        "known_faces",
        "owner_images",
        "encodings.pickle",
        "face_encodings.pkl",
        "owner.jpg"
    ]

    for path in paths_to_delete:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
    start_registration()
    return render_template("update_owner.html")

@app.route("/update_owner_video_feed")
def update_owner_video_feed():
    return Response(
        generate_register_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/email_setup", methods=["GET", "POST"])
def email_setup():

    if request.method == "POST":

        email = request.form["email"]

        with open("owner_email.txt", "w") as f:
            f.write(email)

        return redirect("/register")

    return render_template("email.html")

@app.route("/update_email", methods=["GET", "POST"])
def update_email():

    if request.method == "POST":

        email = request.form["email"]

        with open("owner_email.txt", "w") as f:
            f.write(email)

        return redirect("/start_update_owner")

    return render_template("update_email.html")

@app.route("/change_email_choice")
def change_email_choice():
    return render_template("change_email_choice.html")

@app.route("/project_details")
def project_details():
    print("PROJECT DETAILS ROUTE OPENED")
    print("Current folder:", os.getcwd())
    print("Template exists:", os.path.exists("templates/project_details.html"))
    return render_template("project_details.html")

if __name__ == "__main__":
    app.run(debug=True)