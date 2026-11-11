# ARCH styling backend · screens 12 to 38

This is the complete backend for the styling journey on pages 6 to 13 of the ARCH Visual Screen Map (30 October 2026). It covers guest browsing, brow profile setup, home, scan consent, the face scan, the face shape recommendation, the style selector, Refine mine / Reshape mine, the three intensities, the two-look comparison, and saving a look.

It is a new build. The old `/scan`, `/apply-style` and `/enhance/*` endpoints are not part of it. Every route is under `/v1`.

| Area | Screens | Build plan module |
|---|---|---|
| Platform: health, config, errors, stub login | all | M0 |
| Guest gates | 12, 12a, 13, 13a | M0 (stub) |
| Brow profile setup | 14 to 18 | M3 |
| Home | 19, 20, 21 | M3 + M8 |
| Face scan consent | 23 | M2 (scan consent only) |
| Face scan, face shape, brow reading | 25 to 28 | M4 |
| Style catalogue (8 styles, 8 colours, 3 intensities, 24 titles) | 29, 31 | M5 |
| Recommendation (Measurement JSON v1.3.1) | 27, 29 | M6 |
| Realistic try-on, Refine mine / Reshape mine | 29 to 36 | M7 |
| Save a look | 37, 38 | M8 |

Login (M1) is built: `/v1/auth/*` and `/v1/me` (see `docs/SCREEN_API_MAP.md`). Every call sends `Authorization: Bearer <access_token>`; with no token you are a guest. Tokens use the same format and `JWT_SECRET` as the existing auth service in `../app`, so its tokens are accepted too. Emails (2FA codes, reset links, account emails) are sent over SMTP with the `SMTP_*` settings; settings come from the environment or `.env` (template: `.env.example`). Texts go through Twilio (`TWILIO_*`). Push has no provider yet and is only logged. Membership (M10) is real: free accounts can scan and try on; saving, tracing and guides need membership (`MEMBERSHIP_REQUIRED` → 64). In dev, `POST /v1/dev/grant-membership` makes the signed-in account a member without a store.

Images are private: every `/media` URL the API returns is signed and expires after 15 minutes. Dev routes (`/v1/dev/*`, `/live`) only exist with `ARCH_ENV=dev` or `staging`; on production they answer 404. `API-STATUS.md` tracks every screen and open item.

Settings: `ARCH_ENV` is `dev`, `staging` or `production`, and **defaults to `production`** (`run.bat`, `run.sh` and the tests set `dev`). `ARCH_JWT_SECRET` (or `JWT_SECRET`) is required outside dev. Server settings for each environment are in `deploy/production.env.example` and `deploy/staging.env.example`. `ARCH_DEV_AUTO_LOGIN=true` (dev only, off by default) brings back the old shortcut where no token means the test user.

---

## 1. Run it

You need Python 3.10 to 3.13 and an internet connection the first time.

### Windows

```bat
cd arch-styling-backend
run.bat
```

### macOS or Linux

```bash
cd arch-styling-backend
./run.sh
```

The script creates `.venv`, installs `requirements.txt`, downloads the face model if it is missing (`models/face_landmarker.task` is already in the folder), and starts the server on http://127.0.0.1:8000.

To run it by hand:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
python tools/download_model.py  # only if models/face_landmarker.task is missing
set ARCH_ENV=dev                 # Windows (export ARCH_ENV=dev on macOS / Linux)
uvicorn app.main:app --reload --port 8000
```

To check it is running, open http://127.0.0.1:8000/health. You should see `"status": "ok"` and `"model_found": true`.

To run the automated tests:

```bash
pytest -q                                   # no photo needed (photo tests are skipped)
ARCH_TEST_PHOTO=my_face.jpg pytest -q       # macOS / Linux: adds the full journey test
set ARCH_TEST_PHOTO=my_face.jpg && pytest -q    (Windows)
```

All 100 tests passed on the build machine (with a face photo), 9 November 2026.

---

## 2. Test the API in Swagger

Open http://127.0.0.1:8000/docs. First call `POST /v1/auth/register` with `{"name": "Mary", "email": "mary@example.com", "password": "a-good-password", "confirm_password": "a-good-password"}`, copy `access_token`, click **Authorize** and paste it. Do the steps in this order, because each step uses the `scan_id` from step 2.

**Step 0. Optional: start fresh.** Register a new email, or call `POST /v1/dev/reset-test-user`, which wipes the signed-in account (register again afterwards).

**Step 1. Profile setup (screens 14 to 18).**
1. `PUT /v1/onboarding/skin-tone-goal` with the body
   `{"skin_tone": "medium", "undertone": "warm", "brow_goal": "both"}`.
   The response holds `screen_15`, which is her tone and the Best and two Close brow shades.
2. `POST /v1/onboarding/confirm-tone` with `{}`.
3. `PUT /v1/onboarding/direction` with `{"direction": "refined_natural"}`. The response holds `screen_17`. Send `{"direction": null}` to test "I'll add this later".
4. `POST /v1/onboarding/complete` with `{}`. The response holds `screen_18` and `next_screen: "19"`.
5. `GET /v1/home`. This returns `screen: "19"` until a look is saved, then `"21"`.

**Step 2. Consent and scan (screens 23 and 25 to 28).**
1. `POST /v1/consents/face-scan` with `{"granted": true}`.
2. `POST /v1/scans`. Click **Choose File**, pick a front-facing photo of your face, and click Execute.
3. Copy `scan_id` from the response. Check:
   * `screen_27.face_shape`, `screen_27.brow_shape` and `screen_27.recommended_for_you`
   * `screen_28.lines` and `screen_28.chips`
   * `recommendation`, which has the recommended style, the alternate, the styles to avoid, the peak position after the face shape adjustment, the colour and the default intensity and mode
   * `face_shape.rules`, which shows why the face shape was chosen
   * `before_images.face`. Open `http://127.0.0.1:8000` followed by that path to see the crop.

**Step 3. Style selector (screen 29).**
* `GET /v1/styles?scan_id=<id>`. Two styles have `recommended_for_you: true`.
* `GET /v1/colours?scan_id=<id>`. One colour has `best_for_you: true`.

**Step 4. Try a style (screens 30 and 32 to 34, and 36).**
`POST /v1/tryon/render` with

```json
{"scan_id": "<id>", "style": "structured", "colour": "dark_brown", "intensity": "defined", "mode": "reshape"}
```

Open `http://127.0.0.1:8000` followed by `images.face` from the response. Change `mode` to `"refine"`, then try `intensity` `"understated"` and `"deliberate"`. `copy` holds every string the screen shows. The first render takes about 1 second. A repeat of the same look comes from the cache.

**Step 5. Intensity selector and compare (screens 31 and 35b).**
* `POST /v1/tryon/intensities` with `{"scan_id": "<id>", "style": "structured"}` returns three eye-strip images.
* `POST /v1/tryon/compare` with `{"scan_id": "<id>", "style": "structured", "intensities": ["defined", "deliberate"]}` returns two looks with `I CHOOSE DEFINED` and `I CHOOSE DELIBERATE`.

**Step 6. Save (screens 37 and 38).**
`POST /v1/looks` with `{"scan_id": "<id>", "style": "structured", "intensity": "defined", "colour": "dark_brown", "tag": "everyday"}`. The response holds `screen_38`, which says "Saved." with "The One She Keeps Returning To". `GET /v1/looks` lists the saved looks.

**Step 7. Check the gates and errors.**
* Put `true` in the `x-guest` header and call `POST /v1/scans`. The response is `ACCOUNT_REQUIRED` with `route_to: "13"`.
* Upload a photo with no face to `POST /v1/scans`. The response is `NO_FACE` with `route_to: "26"`.

`docs/SCREEN_API_MAP.md` lists every screen next to the call it uses.

---

## 3. Live test on your own face

### Option A. Browser page with your webcam (recommended)

1. Start the server.
2. Open **http://127.0.0.1:8000/live** in Chrome. Use 127.0.0.1 or localhost, because browsers allow the camera only there or on https.
3. Click **START CAMERA**, allow the camera, look straight at it in even light with your hair off your brows, then click **TAKE PHOTO & SCAN**. You can also click **UPLOAD PHOTO**.
4. The left panel shows what the scan read: face shape, brow shape, recommended and alternate styles with their peak positions, styles to avoid, the colour for you and the skin tone it saw. Open "Why this face shape" to see each classifier rule and whether it fired.
5. The recommended style is applied straight away. Tap any style, colour, REFINE MINE / RESHAPE MINE and intensity. The before and after images sit side by side.
6. Try **SHOW ALL 3 INTENSITIES**, **COMPARE**, and **SAVE THIS LOOK**.
7. **Open debug overlay** shows your traced natural brow in white and the recommended style outline in gold. Use it to see that the brow sits where it should.

### Option B. One command, everything saved to a folder

```bash
python tools/live_test.py path/to/my_face.jpg
```

This runs the whole journey (23 → 25 → 29 → 30 → 31 → 35b → 37/38) and writes `out/live_test_<time>/` with:

* `summary.md`: face shape, brow shape, the recommendation and the full classifier trace
* `recommended_<style>_<mode>_<intensity>.jpg`: the recommended style at all three intensities in both modes
* `all_styles.jpg`: all eight styles on your face, with `*` on the two recommended ones
* `debug_overlay.jpg`

To see what a different face shape would recommend on your face, add `--face-shape heart` (or round, square, diamond, oblong, triangle, oval).

### How to check the recommendation is right

The recommendation comes only from the client's Measurement JSON v1.3.1 (`app/catalogue/data/`). For the face shape your scan reports, the result must match this table:

| Face shape | Recommended | Alternate | Peak adjustment | Avoid |
|---|---|---|---|---|
| Oval | Arch (67%) | Structured (57%) | 0 | none |
| Round | Sharp (71%) | Arch (73%) | +6 | Bold |
| Square | Rounded (45%) | Structured (50%) | −7 | none |
| Heart | Structured (51%) | Rounded (46%) | −6 | Bold |
| Diamond | Rounded (50%) | Arch (65%) | −2 | none |
| Oblong | Straight (level) | Bold (50%) | −7, not applied to Straight | none |
| Triangle | Arch (69%) | Sharp (67%) | +2 | none |

If the face shape itself looks wrong for your face, open the classifier trace (in `/live` or `summary.md`). It lists the client's rules in order (Oblong, Round, Diamond, Heart, Triangle, Square, then Oval as the default) with your measured ratio next to each threshold. The thresholds sit in one place, `RULES` and `CALIBRATION` in `app/vision/face_analysis.py`.

---

## 4. How it works

**Scan.** MediaPipe Face Landmarker finds 478 points. The photo is checked for one face, centred, close enough, facing forward, with enough light and visible brows. Each failure has its own error code and screen. The photo, the landmarks and her traced natural brow are stored once under a `scan_id`, so a try-on tap never uploads the photo again.

**Face shape.** The client's classifier rules are applied in the client's order. MediaPipe has no hairline point and its mesh varies less than real faces, so the mesh ratios are mapped onto the client's scale first (`CALIBRATION`). Then the client's thresholds are used as written.

**Brow reading (screen 27 "BROW SHAPE").** Her brow is traced on the real hair in the photo and measured with the client's own measures, in eye-width units in the eye-line frame: length, peak position, peak height, thickness at head, body and tail, and tail against head. It is labelled High arch, Defined arch, Soft arch, Low arch, Rounded or Straight.

**Style geometry.** Each style is built from its JSON row. The build re-measures every generated shape against the JSON, and the tests require it to match within 0.02 eye width and 2 points of peak position. The face shape's peak adjustment moves the peak, and the plateau moves with it.

**Reshape mine** ("The style's shape, placed on your brow"). The style's exact shape is placed on her brow and scaled by her eye width. Her own brow is softly concealed by rebuilding the skin with the photo's own grain. The brow is then painted as a powder body plus several hundred tapered, curved hairs. Hair growth follows the client's stroke-direction zones, the pigment is lit by the photo's light, and the result matches the photo's sharpness. The brow is never allowed to sit on the eyelid.

**Refine mine** ("Your own shape, filled and groomed toward the style"). Her brow stays. The target is her own outline moved halfway toward the style. Sparse areas are filled, strays outside the target are softened away, new hairs go mostly where she has none, and her own hairs take on the chosen colour.

**Intensity.** Understated, Defined and Deliberate change only fill weight and colour density (35 / 65 / 95%). The shape never changes, and the hairs of a lighter intensity are an exact subset of the heavier one.

**Colour.** The recommended colour is, in order: the shade she confirmed on screen 15, or else her own brow colour moved one shade toward the best shade for her skin tone.

---

## 5. Folder

```
arch-styling-backend/
  app/
    main.py                     FastAPI app, routers, /media and /static
    config.py                   settings (env vars ARCH_*)
    core/        auth.py (stub login + can()), db.py (SQLite), errors.py
    catalogue/   measurements.py (loads the JSON), content.py (all copy, colours, titles)
                 data/arch_brow_measurements_v1.3.1.json
    vision/      landmarks.py, face_analysis.py (face shape, quality, skin tone), brow_measure.py
    rendering/   geometry.py (JSON → brow shape), brow_renderer.py (Reshape + Refine)
    services/    scan_service.py, render_service.py, profile_service.py
    routers/     profile_routes.py (12-23), styling_routes.py (25-38), dev_routes.py
    static/      live_test.html
  models/        face_landmarker.task
  tools/         live_test.py, contact_sheet.py, download_model.py
  tests/         test_api.py
  docs/          SCREEN_API_MAP.md
  data/          created at run time: arch.db and media/ (photos, renders, looks)
```

---

## 6. Assumptions and items for the client

These are working decisions. Each one can be changed in a single file.

1. **Refine mine = fill and groom her own brow, Reshape mine = place the style's shape** (assumed from the 30a copy). `app/rendering/brow_renderer.py`, with `REFINE_PULL = 0.5`.
2. **"Head" is the lower inner end of the brow.** That is the only reading under which Straight's level top edge at 0.25 agrees with its 0.27 head thickness. `app/rendering/geometry.py`.
3. **The face shape peak adjustment applies to every style tried on that face**, not only the recommended and alternate styles, so a style keeps the same peak however she reaches it. `measurements.py → peak_pct`.
4. **Colour names and hex values** for the eight swatches were sampled from screen 29. Only Dark Brown is named in the client files. They are marked `provisional`. `content.py → COLOURS`.
5. **Skin tone → Best and Close shades** (screen 15) is our table. `content.py → BROW_SHADES_FOR_TONE`.
6. **Copy the screen map does not show** is drafted and marked `provisional`: screen 30 headlines for the seven styles other than Structured, screen 17 for the other two directions, and screen 28 line 3 for the six face shapes other than Oval.
7. **Scan Complete shows two recommended chips** (Recommended and Alternate), following the JSON and the drawn screen. The handoff text lists three.
8. **Face shape calibration** (`CALIBRATION` and `RULES`) was set on a small set of test photos. The client should check it on real ARCH users.

## 7. Known limits

* Renders are still photos. The live camera AR overlay is built in the app. The app can use the same measured shapes from `GET /v1/styles` (each style's measurements) to draw it.
* Very heavy, dark natural brows can leave a faint lighter band where they are concealed in Reshape mine. Refine mine has no such band.
* The detected skin tone shifts with photo exposure. It is only a suggestion. The tone she picks on screen 14 always wins.
* Storage is SQLite plus local files (`data/`), with one server process. Move it to Postgres and S3 in M0 production work. The seam is `app/core/db.py`.
* Swagger loads its page script from a CDN, so `/docs` needs internet. The API itself does not.

## 8. Done for today

When you can do all of the following on your machine, this step is complete and we can move to the next part of the app:

- [ ] `/health` shows `model_found: true`
- [ ] `pytest -q` passes
- [ ] Swagger steps 1 to 7 above work
- [ ] `/live` scans your face, shows a face shape and a recommendation that matches the table in section 3, and renders all eight styles in both modes and all three intensities
- [ ] `python tools/live_test.py my_face.jpg` writes the result folder
