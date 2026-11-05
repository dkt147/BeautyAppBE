"""MediaPipe Face Landmarker wrapper (478 points, still images).

The model file is models/face_landmarker.task (tools/download_model.py).
A single landmarker is shared; MediaPipe IMAGE mode is not thread safe, so
calls are serialised with a lock.
"""
import atexit
import threading

import cv2
import numpy as np

from app import config
from app.core.errors import ApiError

_landmarker = None
_lock = threading.Lock()

# Index groups used across the backend. "right" = the person's right =
# image LEFT on a non-mirrored photo.
EYE = {
    "right": {"inner": 133, "outer": 33, "iris": 468},
    "left": {"inner": 362, "outer": 263, "iris": 473},
}
BROW = {
    "right": {"upper": [107, 66, 105, 63, 70], "lower": [55, 65, 52, 53, 46]},
    "left": {"upper": [336, 296, 334, 293, 300], "lower": [285, 295, 282, 283, 276]},
}


def _get():
    global _landmarker
    if _landmarker is None:
        if not config.MODEL_PATH.exists():
            raise ApiError("MODEL_MISSING",
                           f"Face model not found at {config.MODEL_PATH}. Run: python tools/download_model.py",
                           500)
        from mediapipe.tasks.python import BaseOptions, vision
        opts = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(config.MODEL_PATH)),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=2,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
        )
        _landmarker = vision.FaceLandmarker.create_from_options(opts)
    return _landmarker


@atexit.register
def close():
    """Release MediaPipe cleanly at exit (avoids a noisy traceback)."""
    global _landmarker
    if _landmarker is not None:
        try:
            _landmarker.close()
        except Exception:
            pass
        _landmarker = None


def decode_image(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ApiError("BAD_IMAGE", "The photo could not be read. Send a JPEG or PNG.", 400)
    h, w = img.shape[:2]
    s = config.MAX_IMAGE_SIDE / max(h, w)
    if s < 1.0:
        img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return img


def detect(image_bgr: np.ndarray):
    """Return a list of (478, 3) landmark arrays in PIXELS (z scaled by width)."""
    import mediapipe as mp
    h, w = image_bgr.shape[:2]
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
    with _lock:
        res = _get().detect(mp_img)
    faces = []
    for lms in res.face_landmarks or []:
        faces.append(np.array([[p.x * w, p.y * h, p.z * w] for p in lms], np.float64))
    return faces


def eye_width(lm, side):
    e = EYE[side]
    return float(np.linalg.norm(lm[e["outer"], :2] - lm[e["inner"], :2]))


def eye_frame(lm, side):
    """Eye-line frame for one side (Measurement JSON 'axes').

    origin = inner eye corner, out = toward the outer corner (x, Head->Tail),
    up = perpendicular, toward the brow (y positive).
    """
    e = EYE[side]
    inner, outer = lm[e["inner"], :2], lm[e["outer"], :2]
    out = (outer - inner) / (np.linalg.norm(outer - inner) + 1e-9)
    up = np.array([out[1], -out[0]])
    if up[1] > 0:      # image y grows downward; "up" must point to the forehead
        up = -up
    return Frame(inner, out, up)


class Frame:
    def __init__(self, origin, out_dir, up_dir):
        self.o = np.asarray(origin, np.float64)
        self.out = np.asarray(out_dir, np.float64)
        self.up = np.asarray(up_dir, np.float64)

    def to_local(self, pts):
        d = np.asarray(pts, np.float64)[..., :2] - self.o
        return np.stack([d @ self.out, d @ self.up], axis=-1)

    def to_image(self, s, n):
        s = np.asarray(s, np.float64)[..., None]
        n = np.asarray(n, np.float64)[..., None]
        return self.o + s * self.out + n * self.up
