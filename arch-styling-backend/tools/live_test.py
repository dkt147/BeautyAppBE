"""Live test on YOUR face photo, end to end, without Swagger.

    python tools/live_test.py path/to/my_face.jpg
    python tools/live_test.py my_face.jpg --face-shape heart      (force a face shape)

It runs the same API calls the app makes (consent 23 -> scan 25 -> styles 29
-> render 30 -> intensities 31 -> compare 35b -> save 37/38) inside this
process, as a fresh test user, and writes everything to out/live_test_<time>/:

    summary.md            what the scan found and what it recommends, and why
    recommended_*.jpg     the recommended style, every intensity, both modes
    all_styles.jpg        all eight styles on your face
    debug_overlay.jpg     your traced brow + the recommended outline
"""
import argparse
import json
import os
import sys
import time
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from fastapi.testclient import TestClient   # noqa: E402

from app import config                       # noqa: E402
from app.main import app                     # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--face-shape", default=None, help="force oval/round/square/heart/diamond/oblong/triangle")
    a = ap.parse_args()

    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = os.path.join(ROOT, "out", f"live_test_{stamp}")
    os.makedirs(out, exist_ok=True)
    c = TestClient(app)
    tag = uuid.uuid4().hex[:6]
    reg = c.post("/v1/auth/register", json={"name": "Live Test", "email": f"live-{tag}@example.com",
                                            "password": f"live-test-{tag}", "confirm_password": f"live-test-{tag}"})
    if reg.status_code != 201:
        print(f"FAILED sign-up: {reg.status_code} {reg.text}")
        sys.exit(1)
    H = {"Authorization": "Bearer " + reg.json()["access_token"]}
    c.post("/v1/dev/grant-membership", json={}, headers=H)     # saving needs membership (M10)

    def ok(r, code=200):
        if r.status_code != code:
            print(f"\nFAILED {r.request.method} {r.request.url.path}: {r.status_code}\n{r.text}")
            sys.exit(1)
        return r.json()

    def save(url, name):
        p = os.path.join(out, name)
        with open(p, "wb") as f:
            f.write(c.get(url).content)
        return p

    print("1/7 consent (23)")
    ok(c.post("/v1/consents/face-scan", json={"granted": True}, headers=H))
    print("2/7 scan (25)")
    with open(a.photo, "rb") as f:
        data = {"face_shape_override": a.face_shape} if a.face_shape else {}
        sc = ok(c.post("/v1/scans", files={"photo": ("face.jpg", f, "image/jpeg")}, data=data, headers=H), 201)
    sid = sc["scan_id"]
    rec = sc["recommendation"]
    print(f"     face shape: {sc['face_shape']['name']}   brow shape: {sc['brow']['shape_label']}")
    print(f"     recommended: {rec['recommended']['name']}  alternate: {rec['alternate']['name']}  "
          f"avoid: {', '.join(rec['avoid']) or 'none'}  colour: {rec['colour']['name']}")

    print("3/7 styles (29)")
    styles = ok(c.get("/v1/styles", params={"scan_id": sid}, headers=H))["styles"]
    best = rec["recommended"]["style"]
    colour = rec["colour"]["id"]

    print("4/7 recommended style, all intensities, both modes (30, 32-34)")
    for mode in ("reshape", "refine"):
        for it in ("understated", "defined", "deliberate"):
            r = ok(c.post("/v1/tryon/render", json={"scan_id": sid, "style": best, "colour": colour,
                                                     "intensity": it, "mode": mode}, headers=H))
            save(r["images"]["face"], f"recommended_{best}_{mode}_{it}.jpg")
    save(sc["before_images"]["face"], "before.jpg")

    print("5/7 intensity selector (31) and compare (35b)")
    ok(c.post("/v1/tryon/intensities", json={"scan_id": sid, "style": best, "colour": colour}, headers=H))
    cmp_ = ok(c.post("/v1/tryon/compare", json={"scan_id": sid, "style": best, "colour": colour,
                                                "intensities": ["defined", "deliberate"]}, headers=H))

    print("6/7 all eight styles")
    import cv2
    import numpy as np
    tiles = [cv2.imread(os.path.join(out, "before.jpg"))]
    names = ["Before"]
    for s in styles:
        r = ok(c.post("/v1/tryon/render", json={"scan_id": sid, "style": s["id"], "colour": colour,
                                                 "intensity": "defined", "mode": "reshape"}, headers=H))
        tiles.append(cv2.imread(save(r["images"]["face"], f"style_{s['id']}.jpg")))
        names.append(s["name"] + (" *" if s["recommended_for_you"] else ""))
    h = 420
    cells = []
    for t, n in zip(tiles, names):
        t = cv2.resize(t, (int(t.shape[1] * h / t.shape[0]), h))
        cv2.rectangle(t, (0, 0), (t.shape[1], 30), (10, 10, 10), -1)
        cv2.putText(t, n, (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (76, 168, 201), 1, cv2.LINE_AA)
        cells.append(t)
    rows = [np.hstack(cells[i:i + 3]) for i in range(0, 9, 3)]
    cv2.imwrite(os.path.join(out, "all_styles.jpg"), np.vstack(rows))
    with open(os.path.join(out, "debug_overlay.jpg"), "wb") as f:
        f.write(c.get(f"/v1/dev/scan-debug/{sid}", headers=H).content)

    print("7/7 save look (37 / 38)")
    look = ok(c.post("/v1/looks", json={"scan_id": sid, "style": best, "colour": colour,
                                         # null when she has no style direction; the tool then picks Defined
                                         "intensity": rec["intensity"] or "defined", "mode": rec["mode"],
                                         "tag": "everyday"},
                     headers=H), 201)

    fsd = sc["face_shape"]
    lines = [
        f"# Live test · {stamp}", "",
        f"Photo: `{a.photo}`", "",
        "## What the scan found (screens 27 and 28)", "",
        f"* Face shape: **{fsd['name']}** ({fsd['source']}) · {fsd['tagline']}",
        f"* Brow shape: **{sc['brow']['shape_label']}** (closest of the eight: {sc['brow']['closest_style']})",
        f"* Features: {' '.join(sc['features']['lines'])}",
        f"* Chips: {' · '.join(sc['features']['chips'])}",
        f"* Skin tone seen: {sc['skin_tone_detected']['tone']} {sc['skin_tone_detected']['undertone']}",
        "", "## Recommendation (Measurement JSON v1.3.1, face shape table)", "",
        f"* Recommended: **{rec['recommended']['name']}**, peak at {rec['recommended']['peak_position_pct']}% of length",
        f"* Alternate: **{rec['alternate']['name']}**, peak at {rec['alternate']['peak_position_pct']}%",
        f"* Avoid: {', '.join(rec['avoid']) or 'none'}",
        f"* Peak adjustment for {fsd['name']}: {rec['peak_adjustment_pts']:+g} points",
        f"* Colour: {rec['colour']['name']} ({rec['colour']['source']})",
        "", "## Why this face shape (client classifier, in order)", "",
        "| Shape | Fired | Test |", "|---|---|---|",
        *[f"| {t['shape']} | {'yes' if t['fired'] else 'no'} | {t['test']} |" for t in fsd["rules"]],
        "", "Measured: `" + json.dumps({k: v for k, v in fsd["metrics"].items() if k != "raw"}) + "`",
        "", "## Your natural brow, in the client's measures (eye-width units)", "",
        "`" + json.dumps(sc["brow"]["measurements"]["average"]) + "`",
        "", "## Saved look (38)", "",
        f"* {look['screen_38']['title']} {look['screen_38']['editorial_title']} · {look['look']['caption']} · {look['look']['mode_label']}",
        "", "Images in this folder: before.jpg, recommended_*.jpg, style_*.jpg, all_styles.jpg, debug_overlay.jpg",
    ]
    with open(os.path.join(out, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nDone. Open {out}")


if __name__ == "__main__":
    main()
