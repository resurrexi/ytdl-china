import os
import time

upload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'uploads')

# scan upload folder for existing videos
videos = [
    f for f in os.listdir(upload_path)
    if os.path.isfile(os.path.join(upload_path, f)) and len(f) <= 15
]

# check video creation timestamp
now = time.time()

for v in videos:
    if now - os.stat(os.path.join(upload_path, v)).st_mtime > 86400:
        os.remove(os.path.join(upload_path, v))
