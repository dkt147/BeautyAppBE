"""Copy for screens 22a, 30 (Structured), 42 and 43.

The wording is the client's (Live Brow Experience Specification, Draft 3.2,
6 November 2026) and is held as data in data/copy_v3_2.json, one set per face
shape, as the spec asks ("Do not put any of it in code"). Edit the JSON.
"""
import json
from functools import lru_cache
from pathlib import Path

_PATH = Path(__file__).parent / "data" / "copy_v3_2.json"


@lru_cache(maxsize=1)
def copy() -> dict:
    return json.loads(_PATH.read_text(encoding="utf-8"))


def screen_42(face_shape: str) -> dict:
    return copy()["screen_42"][face_shape]


def screen_43(face_shape: str) -> dict:
    return copy()["screen_43"][face_shape]


def screen_22a() -> dict:
    return copy()["screen_22a"]


def screen_30_structured() -> dict:
    return copy()["screen_30_structured"]


# MediaPipe Face Mesh face-oval landmarks, clockwise from the forehead.
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377,
             152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
