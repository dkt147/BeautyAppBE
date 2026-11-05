# Screen → API map (screens 12 to 38)

Source: ARCH Visual Screen Map, 30 October 2026, pages 6 to 13. Every call
below is in Swagger at http://127.0.0.1:8000/docs under the tag shown.
Errors always come back as `{"error": {"code", "message", "route_to"}}`, and
`route_to` is the screen the app should open.

| Screen | What the app does | Call |
|---|---|---|
| 12 Guest Home | Tiles for a guest | `GET /v1/home` with `X-Guest: true` → `screen: "12"` |
| 12a Guest Try-On Preview | Static. Style list is browsable | `GET /v1/styles` (works for guests) |
| 13 Scan Gate | Shown when a guest taps scan / try-on | any scan or try-on call returns `ACCOUNT_REQUIRED`, `route_to: "13"` |
| 13a Account Gate | Shown when a guest opens Looks / Profile | looks and profile calls return `route_to: "13a"` |
| 14 Skin Tone + Goal | Lists tones, undertones, goals; NEXT saves | `GET /v1/onboarding/options`, `PUT /v1/onboarding/skin-tone-goal` |
| 15 Skin Tone Confirmation | Tone label + Best / Close / Close shades | returned by the PUT above as `screen_15`; CONFIRM → `POST /v1/onboarding/confirm-tone` |
| 16 Style Direction | Three directions; BEGIN or "I'll add this later" | `PUT /v1/onboarding/direction` (`direction: null` = skip → 18) |
| 17 Direction Confirmation | Three bullet points | returned by the PUT above as `screen_17` |
| 18 Onboarding Complete | Summary; ENTER ARCH | `POST /v1/onboarding/complete` (`carry_style` → next 29 with that style) |
| 19 / 20 / 21 Home | New, returning, personalised (last look + RE-APPLY) | `GET /v1/home` → `screen` is 19, 20 data, or 21 |
| 22 Face Scan Intro | Static. "Browse styles directly" → 29 without a scan | `GET /v1/styles` |
| 23 Camera + Face Scan Consent | ALLOW CAMERA with the box ticked | `POST /v1/consents/face-scan {granted: true}` |
| 24 Camera Settings | iOS only | none |
| 25 Scanning Active | Capture one front-facing frame and upload it | `POST /v1/scans` (multipart `photo`) |
| 26 Face Not In Frame | Shown on `NO_FACE`, `MULTIPLE_FACES`, `FACE_NOT_CENTRED`, `FACE_TOO_SMALL`, `FACE_TURNED`, `BROWS_NOT_VISIBLE`, `BAD_IMAGE` | error `route_to: "26"` |
| 84 Low light (Area 7) | Shown on `LOW_LIGHT` | error `route_to: "84"` |
| 27 Scan Complete | Photo, BROW SHAPE, FACE SHAPE, two recommended chips | scan response `screen_27`, `before_images.face`, `recommendation` |
| 28 Post-Scan Discovery | Three lines + three chips | scan response `screen_28` (also `GET /v1/scans/{id}`) |
| 29 Style Selector | 8 style tiles with "Recommended for you" dots, 8 colours, brow preview, caption | `GET /v1/styles?scan_id=`, `GET /v1/colours?scan_id=`, preview = `POST /v1/tryon/render` → `images.brow`, caption = `copy.caption_upper` |
| 30 Style Applied | Her face with the style; REFINE / RESHAPE toggle; headline + body | `POST /v1/tryon/render` → `images.face`, `copy.style_applied`; toggle = same call with `mode` |
| 30a Mode Introduction | Once per account, 2 s after arrival | `show_mode_intro_30a` in the render response; copy `GET /v1/modes`; GOT IT → `POST /v1/me/flags {mode_intro_seen: true}` |
| 31 Intensity Selector | Three cards with eye-strip previews | `POST /v1/tryon/intensities` → `items[].images.eyes` (copy: `GET /v1/intensities`) |
| 32 / 33 / 34 Intensity | Her face at one intensity; copy changes with mode | `POST /v1/tryon/render` with `intensity` → `copy.intensity_screen` |
| 35a Two Looks Selection | Pick two of three | thumbnails from `POST /v1/tryon/intensities` |
| 35b Two Looks Comparison | Two faces side by side, I CHOOSE … | `POST /v1/tryon/compare {intensities: [a, b]}` |
| 36 This Is Your Look | Face, caption, editorial title | `POST /v1/tryon/render` → `copy.caption`, `copy.editorial_title` |
| 37 Save Look | Name (default caption), tag EVERYDAY / OCCASION | `POST /v1/looks` |
| 38 Saved Confirmation | "Saved.", editorial title, mode | `POST /v1/looks` response `screen_38` |
| (50 / 21 feed) | Saved looks | `GET /v1/looks`, `GET /v1/looks/{id}` |

## Values the app sends

* `style`: arch, structured, feathered, bold, straight, micro, sharp, rounded
* `intensity`: understated, defined, deliberate
* `mode`: refine (REFINE MINE), reshape (RESHAPE MINE)
* `colour`: blonde, light_taupe, taupe, light_brown, medium_brown, chestnut, dark_brown, soft_black

## Image views in a render response

| View | Used on | What it is |
|---|---|---|
| `face` | 30, 32-34, 35b, 36, 37 | 4:5 portrait crop, forehead to chin |
| `brow` | 29 preview | close-up of her right brow (image left) |
| `eyes` | 31, 35a | both brows and eyes strip |
| `full` | save / share | the whole photo |
