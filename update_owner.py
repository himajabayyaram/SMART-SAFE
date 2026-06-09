import os
import shutil

def delete_old_owner():
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
                print(f"Deleted folder: {path}")
            else:
                os.remove(path)
                print(f"Deleted file: {path}")

    print("Old owner data deleted.")