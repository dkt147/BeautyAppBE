"""Render every style (or a chosen list) on one photo into a single sheet.

    python tools/contact_sheet.py my_face.jpg out.jpg
    python tools/contact_sheet.py my_face.jpg out.jpg --mode refine --intensity deliberate --colour soft_black
"""
import argparse
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.catalogue import content as C                       # noqa: E402
from app.catalogue.measurements import load_measurements     # noqa: E402
from app.rendering.brow_renderer import BrowRenderer         # noqa: E402
from app.vision import landmarks as LM                       # noqa: E402
from app.vision.face_analysis import classify_face_shape, face_metrics  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo"); ap.add_argument("out")
    ap.add_argument("--styles", default=",".join(C.STYLE_ORDER))
    ap.add_argument("--mode", default="reshape", choices=["reshape", "refine"])
    ap.add_argument("--intensity", default="defined", choices=C.INTENSITY_ORDER)
    ap.add_argument("--colour", default="dark_brown", choices=list(C.COLOUR_BY_ID))
    ap.add_argument("--face-shape", default=None)
    a = ap.parse_args()
    img = cv2.imread(a.photo)
    lm = LM.detect(img)[0]
    M = load_measurements()
    fs = a.face_shape or classify_face_shape(face_metrics(lm))[0]
    xs, ys = lm[:, 0], lm[:, 1]
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(max(0, ys.min() - 0.08 * (x1 - x0))), int(lm[1, 1])
    R = BrowRenderer()
    tiles = [("Before", img)]
    for sid in a.styles.split(","):
        out, _ = R.render(img, lm, M.style(sid), M.peak_pct(sid, fs), M.plateau(sid, fs),
                          C.COLOUR_BY_ID[a.colour]["hex"], a.intensity, a.mode)
        tiles.append((M.style(sid).name, out))
    h = 300
    cells = []
    for name, t in tiles:
        c = t[y0:y1, x0:x1]
        c = cv2.resize(c, (int(c.shape[1] * h / c.shape[0]), h))
        cv2.rectangle(c, (0, 0), (c.shape[1], 26), (10, 10, 10), -1)
        cv2.putText(c, name, (8, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (76, 168, 201), 1, cv2.LINE_AA)
        cells.append(c)
    cols = 3
    while len(cells) % cols:
        cells.append(np.zeros_like(cells[0]))
    rows = [np.hstack(cells[i:i + cols]) for i in range(0, len(cells), cols)]
    sheet = np.vstack(rows)
    cv2.imwrite(a.out, sheet)
    print(f"face shape {fs}; wrote {a.out}")


if __name__ == "__main__":
    main()
