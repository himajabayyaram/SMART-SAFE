import cv2
import os
import numpy as np

faces = []
labels = []

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

for file in os.listdir():
    if file.startswith("owner") and file.endswith(".jpg"):

        img = cv2.imread(file, cv2.IMREAD_GRAYSCALE)
        detected_faces = face_cascade.detectMultiScale(img, 1.3, 5)

        for (x, y, w, h) in detected_faces:
            face = img[y:y+h, x:x+w]
            faces.append(face)
            labels.append(0)   # only one person

if len(faces) == 0:
    print("No training data found!")
    exit()

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces, np.array(labels))

recognizer.save("trainer.yml")

print("Training completed!")