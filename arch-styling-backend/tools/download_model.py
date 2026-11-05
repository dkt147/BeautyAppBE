"""Download MediaPipe's face_landmarker.task into models/ (about 3.7 MB)."""
import pathlib
import urllib.request

URL = ("https://storage.googleapis.com/mediapipe-models/face_landmarker/"
       "face_landmarker/float16/1/face_landmarker.task")
dest = pathlib.Path(__file__).resolve().parent.parent / "models" / "face_landmarker.task"
dest.parent.mkdir(exist_ok=True)
if dest.exists() and dest.stat().st_size > 1_000_000:
    print(f"Already there: {dest}")
else:
    print(f"Downloading {URL}")
    urllib.request.urlretrieve(URL, dest)
    print(f"Saved {dest} ({dest.stat().st_size // 1024} KB)")
