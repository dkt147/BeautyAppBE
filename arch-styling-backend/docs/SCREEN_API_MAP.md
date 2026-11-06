# Screen → API map (screens 12 to 38)

Source: ARCH Visual Screen Map, 30 October 2026, pages 6 to 13. Every call
below is in Swagger at http://127.0.0.1:8000/docs under the tag shown.
Errors always come back as `{"detail", "code", "route_to"}`, and
`route_to` is the screen the app should open (null = stay on this screen;
any 5xx = 88). Every call sends `Authorization: Bearer <access_token>`;
with no token the caller is a guest.

| Screen | What the app does | Call |
|---|---|---|
| 05 Create Account | CREATE ACCOUNT | `POST /v1/auth/register` → tokens, `next_screen: "14"`; mismatch → field errors (06); email taken → `EMAIL_REGISTERED` (07) |
| 05 / 08 Apple, Google | Continue with Apple / Google | `POST /v1/auth/apple`, `POST /v1/auth/google` `{id_token}` |
| 08 Sign In | SIGN IN | `POST /v1/auth/login` → tokens and `next_screen` 14 / 20 / 21, or `two_factor_required` + `pending_token` → 11 |
| 09 / 10 Forgot, Reset link sent | SEND RESET LINK, Send again | `POST /v1/auth/password/forgot` |
| set new password (kept step) | from the reset link | `POST /v1/auth/password/reset {token, new_password}` → 08 |
| Change Password (kept step) | | `POST /v1/me/password` |
| 11 Two-Factor Auth | VERIFY CODE, Resend code | `POST /v1/auth/2fa/verify`, `POST /v1/auth/2fa/resend` (429 `RESEND_TOO_SOON`, `retry_after`) |
| any | access token expired | `POST /v1/auth/refresh {refresh_token}` (rotates); 401 `AUTH_REQUIRED` → 08 |
| 53 / 54 Profile, My Account | read, SAVE CHANGES | `GET /v1/me`, `PATCH /v1/me` (name; email needs `current_password`; `two_factor`) |
| 65 Phone Number | CONTINUE, then the code | `POST /v1/me/phone`, `POST /v1/me/phone/verify` → 67 |
| 81 Sign Out | SIGN OUT | `POST /v1/auth/logout` → 08 |

Styling screens:

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

## Block 2 screens

| Screen | What the app does | Call |
|---|---|---|
| 02 Before We Begin | CONTINUE (four boxes), before sign-up | `POST /v1/consent {type: "biometric_notice", boxes}` with `X-Install-Id`; send the same header on register / login to link it |
| 23 Camera + Face Scan Consent | show only when `show_screen_23` | `GET /v1/consent/status`; ALLOW CAMERA → `POST /v1/consent {type: "face_scan"}` |
| 25 Scanning | upload | `POST /v1/scans` (JPEG / PNG, max 8 MB: 415 / 413 otherwise) |
| 29 no scan | preview of a tapped style | `GET /v1/library?style=&tone=` (`image.url_*`) |
| 39 Recommendation Intro | first time vs already scanned | `GET /v1/me/brow-profile` → `has_scan` |
| 44 The Difference | BEFORE / AFTER | `POST /v1/tryon/before-after` |
| any try-on | Full / Ombre | `finish` on render, intensities, compare, before-after, looks (Ombre not for Straight / Micro) |
| 36a Before You Trace | BEGIN (gate) | `POST /v1/tracing/sessions {look_id}` or `{scan_id, style, ...}` → 73 |
| 75-xx / 76-xx | stage reached, events | `PATCH /v1/tracing/sessions/{id} {stage}` or `{event}` (`tracking_failed` → 49c) |
| 75d | LEAVE SESSION | `POST /v1/tracing/sessions/{id}/leave` → 36 |
| 77 | FINISH, SAVE LOOK | `POST .../complete` (state 2 if saved on 37, else 1), `POST .../save` (state 1 → 2) |
| 49a / 49b | SAVE THIS GUIDE | `POST /v1/guides` (multipart `strokes` JSON, `name`, `image`) |
| 50 / 51 My Looks | tabs ALL / TRACED / PREVIEWED | `GET /v1/looks?tab=` (`screen` 50 or 51, each look has `kind`) |
| 55 / 55f Brow Profile | read | `GET /v1/me/brow-profile` (`screen` 55 or 55f) |
| 55a | SAVE CHANGES | `PATCH /v1/me/brow-profile {preferred_style, preferred_colour}` |
| 55c → 55d / 55e | REMOVE / KEEP MY PHOTOGRAPHS | `DELETE /v1/me/face-scan {remove_photographs}` |
| 89 to 94 The Library | pages 1 to 6 | `GET /v1/library?tone=&finish=&page=` |
| 79 → 80 | YES, DELETE MY ACCOUNT | `POST /v1/me/delete {confirm: true}` (14 days; signing in stops it) |

## Block 3 screens

Every image URL in a response is signed and expires after 15 minutes
(`/media/...?exp=&sig=`). Load the screen again for fresh links. Free
accounts get `MEMBERSHIP_REQUIRED` (`route_to: "64"`) on save, tracing and
guides.

| Screen | What the app does | Call |
|---|---|---|
| 20 Home (Returning) | returning, no saved look | `GET /v1/home` → `screen: "20"` |
| 41 Your Result | face shape + two styles | `GET /v1/recommendations` |
| 42 / 43 Why This Shape | about the style; why it suits her face (outline on her photo) | `GET /v1/recommendations/{style}` → `screen_42`, `screen_43` |
| 50 My Looks | rename | `PATCH /v1/looks/{id} {name, tag}` |
| 52 Share This Look | the share image | `POST /v1/looks/{id}/share-image` |
| 53 / 54 Profile, My Account | MEMBER badge, plan, renewal, payment method | `GET /v1/me` → `membership` |
| 56 / 57 Preferences, Language | switches, six languages | `GET` / `PATCH /v1/me/preferences` |
| 59 Contact Us | SEND MESSAGE | `POST /v1/support/messages` |
| 63 / 64 / 67 / 68 / 71 / 72 Membership | all screen data | `GET /v1/me/entitlements` (`offer`, `screen_63`, `screen_67`, `screen_68`, `screen_71`, `screen_72`) |
| 64 → native sheet → 65 | after the purchase | `POST /v1/billing/apple/verify {signed_transaction}` or `/google/verify {purchase_token}` (pass `app_account_token` to the store) |
| 66 Restore purchase | | `POST /v1/billing/restore` |
| 66 / 69 web | | not set up (503) until the provider is chosen |
| 82 / 83 Notifications | YES, KEEP ME INFORMED → native dialog | `POST /v1/devices {platform, push_token, permission}` |
| any | prices, refund wording, flags | `GET /v1/config` |

