# ARCH Backend · API Status Tracker

Last updated: **6 November 2026**.
Baseline: ARCH Visual Screen Map (30 October 2026, 134 screens), ARCH Backend Build Plan (3 November 2026, modules M0 to M14), and a scan of the code as it is today.

Update this file every time an API is built or fixed. Change the status icon, tick the checkbox, and add a line to the change log at the bottom.

## Legend

| Icon | Meaning |
|---|---|
| ✅ | **Built.** The API exists and serves the screen as drawn. |
| 🟡 | **Incomplete.** The API exists but is missing something or needs a fix. |
| ❌ | **Missing.** Nothing is built yet. |
| ➖ | **No backend.** The screen is static, app-only, native OS or AR on the device. |
| ⏸ | **Blocked.** It waits on an open client or AR partner question. Do not guess. |

---

## 1. What exists in the code today

The workspace has two backends:

| Codebase | Path | Stack | What it covers |
|---|---|---|---|
| **ARCH styling backend** | `arch-styling-backend/` | FastAPI, SQLite, local files, MediaPipe and OpenCV | Screens 12 to 38: guest gates, onboarding, home, consent 23, scan, catalogue, try-on, save look. Real login since Block 1 (`/v1/auth/*`, bearer JWT). Accepts tokens from `../app` too. |
| **Auth service** (existing login) | `../app/` | FastAPI, MongoDB, JWT (24 h) | Register, login, me, profile, change email, change password, delete account, onboarding flag |
| `../beauty-face/` | none | none | Only a `.venv`, renders and demo images. **No source code.** The legacy `/scan`, `/apply-style` and `/enhance/*` from the build plan are not here. |

### 1a. Styling backend routes (`arch-styling-backend/app/routers/`)

| # | Method · Path | Screens | File |
|---|---|---|---|
| 1 | `GET /health` | none | [dev_routes.py](app/routers/dev_routes.py) |
| 2 | `GET /v1/config` | all | dev_routes.py |
| 3 | `GET /v1/styles/{style_id}/diagram.png` | QA | dev_routes.py |
| 4 | `GET /v1/dev/scan-debug/{scan_id}` | dev only | dev_routes.py |
| 5 | `GET /live` | dev only (webcam test page) | dev_routes.py |
| 6 | ~~`GET /v1/me` (stub)~~ moved to row 44 | 53 | [profile_routes.py](app/routers/profile_routes.py) |
| 7 | `POST /v1/me/flags` | 30a | profile_routes.py |
| 8 | `POST /v1/dev/reset-test-user` | dev only | profile_routes.py |
| 9 | `GET /v1/onboarding/options` | 14, 16 | profile_routes.py |
| 10 | `PUT /v1/onboarding/skin-tone-goal` | 14 → 15 | profile_routes.py |
| 11 | `POST /v1/onboarding/confirm-tone` | 15 | profile_routes.py |
| 12 | `PUT /v1/onboarding/direction` | 16 → 17 / 18 | profile_routes.py |
| 13 | `POST /v1/onboarding/complete` | 18 | profile_routes.py |
| 14 | `GET /v1/profile` | 55 (read only) | profile_routes.py |
| 15 | `GET /v1/home` | 12, 19, 20, 21 | profile_routes.py |
| 16 | `POST /v1/consents/face-scan` | 23 | profile_routes.py |
| 17 | `GET /v1/consents` | 23 | profile_routes.py |
| 18 | `POST /v1/scans` | 25 → 26 / 84 / 27 | [styling_routes.py](app/routers/styling_routes.py) |
| 19 | `GET /v1/scans/latest` | 39, 27 | styling_routes.py |
| 20 | `GET /v1/scans/{scan_id}` | 27, 28 | styling_routes.py |
| 21 | `GET /v1/styles` | 12a, 22, 29 | styling_routes.py |
| 22 | `GET /v1/styles/{style_id}` | 29, 30 | styling_routes.py |
| 23 | `GET /v1/colours` | 29 | styling_routes.py |
| 24 | `GET /v1/intensities` | 31 | styling_routes.py |
| 25 | `GET /v1/modes` | 30, 30a | styling_routes.py |
| 26 | `GET /v1/face-shapes` | 27, 41 | styling_routes.py |
| 27 | `POST /v1/tryon/render` | 29, 30, 32 to 34, 36 | styling_routes.py |
| 28 | `POST /v1/tryon/intensities` | 31, 35a | styling_routes.py |
| 29 | `POST /v1/tryon/compare` | 35b | styling_routes.py |
| 30 | `GET /v1/tryon/before` | 44 (half) | styling_routes.py |
| 31 | `POST /v1/looks` | 37 → 38 | styling_routes.py |
| 32 | `GET /v1/looks` | 50, 21 | styling_routes.py |
| 33 | `GET /v1/looks/{look_id}` | 36 (opened), 21 RE-APPLY | styling_routes.py |
| 34 | `DELETE /v1/looks/{look_id}` | 50 | styling_routes.py |
| 35 | `POST /v1/auth/register` | 05 → 14 / 06 / 07 | [auth_routes.py](app/routers/auth_routes.py) |
| 36 | `POST /v1/auth/login` | 08 → 11 / 14 / 20 / 21 | auth_routes.py |
| 37 | `POST /v1/auth/apple`, `POST /v1/auth/google` | 05, 08 | auth_routes.py |
| 38 | `POST /v1/auth/2fa/verify`, `POST /v1/auth/2fa/resend` | 11 | auth_routes.py |
| 39 | `POST /v1/auth/password/forgot` | 09, 10 | auth_routes.py |
| 40 | `POST /v1/auth/password/reset` | set new password → 08 | auth_routes.py |
| 41 | `POST /v1/me/password` | Change Password | auth_routes.py |
| 42 | `POST /v1/auth/refresh` | all (token rotation) | auth_routes.py |
| 43 | `POST /v1/auth/logout` | 81 → 08 | auth_routes.py |
| 44 | `GET /v1/me` (replaces the stub), `PATCH /v1/me` | 53, 54 | auth_routes.py |
| 45 | `POST /v1/me/phone`, `POST /v1/me/phone/verify` | 65 → 67 | auth_routes.py |

Error codes mapped to screens today (`ERROR_ROUTES` in [content.py](app/catalogue/content.py)): `ACCOUNT_REQUIRED` → 13 / 13a, `CONSENT_REQUIRED` → 23, `NO_FACE` / `MULTIPLE_FACES` / `FACE_NOT_CENTRED` / `FACE_TOO_SMALL` / `FACE_TURNED` / `BROWS_NOT_VISIBLE` / `BAD_IMAGE` → 26, `LOW_LIGHT` → 84, `SCAN_NOT_FOUND` → 22.

### 1b. Auth service routes (`../app/`)

| Method · Path | Screens | Notes |
|---|---|---|
| `POST /auth/register` | 05 | Duplicate email returns **400**, not the 409 that screen 07 needs |
| `POST /auth/login` | 08 | No 2FA step, no refresh token |
| `GET /auth/me` | 53, 54 | |
| `PUT /auth/profile` | 54 | full_name, profile_image, catalog_image |
| `PUT /auth/change-email` | 54 | |
| `PUT /auth/change-password` | Change Password (kept, has no screen number) | |
| `DELETE /auth/account` | 78 to 80 | **Hard deletes at once.** The client needs a 14-day recovery period. |
| `POST /onboarding/complete` | old onboarding | Old flags (`has_used_before`, `permissions_granted`). Replaced by the `/v1/onboarding/*` routes. |

The styling backend does not read the JWT from `../app`. The two are not connected yet.

---

## 2. Cross-cutting fixes (do these before new modules)

| # | Priority | Issue | Where | Fix |
|---|---|---|---|---|
| - [x] F1 | ✅ Done | **`app/main.py` was not in git.** Parent `.gitignore` ignored `main.py` and `README.md` everywhere. | `../.gitignore` | Block 1: rules anchored to the repo root (`/main.py`, `/README.md`, ...). `app/main.py` and `README.md` committed. |
| - [ ] F2 | 🔴 Critical | **Face photos are public.** `/media` is a plain `StaticFiles` mount, so anyone with the URL can open scan photos, renders and look photos with no login. Face data is biometric. | [main.py](app/main.py), [config.py](app/config.py) | Serve media through an authorised route or signed URLs that expire (plan: 15 min). |
| - [x] F3 | ✅ Done (see F17) | **Two separate logins.** | [auth.py](app/core/auth.py) | Block 1: `current_user` validates the bearer JWT (HS256, `sub`, same `JWT_SECRET` as `../app`, so its tokens work). Sessions can be revoked. No token = guest. `ARCH_DEV_AUTO_LOGIN` defaults to `false` and only works with `ARCH_ENV=dev`. |
| - [ ] F4 | 🟠 High | **Entitlement stub.** `can()` lets every account do everything, so `MEMBERSHIP_REQUIRED` → 64 is never returned. Saving (37), tracing (36a) and guides need membership. | [auth.py](app/core/auth.py) `can()` | Add free and member tiers (M10). Free accounts get an empty `GET /v1/looks` (screen 51) instead of an error. |
| - [x] F5 | ✅ Done | **Silent defaults.** | [styling_routes.py](app/routers/styling_routes.py) `_resolve`, [profile_service.py](app/services/profile_service.py) | Block 1: colour, intensity and mode are optional and filled only from request → brow profile → scan. Each response says where each value came from (`resolved_from`). No intensity anywhere → 422 `INTENSITY_REQUIRED`. Mode is remembered per account and starts as Refine mine (or the style direction's mode). `DEFAULT_COLOUR` / `DEFAULT_MODE` removed. ⏸ The map draws RESHAPE MINE selected; the plan says Refine. Confirm with the client (one line: `STARTING_MODE` in content.py). |
| - [x] F6 | ✅ Done (styling) | **One error shape.** | [errors.py](app/core/errors.py) | Block 1: `{"detail", "code", "route_to"}` plus optional `details` / `retry_after`. `../app` still returns FastAPI's `{"detail"}` and is now superseded by `/v1/auth` (see F17). |
| - [x] F7 | ✅ Done | **Unknown errors gave `route_to: null`.** | [errors.py](app/core/errors.py), [content.py](app/catalogue/content.py) | Block 1: any 5xx → "88". Added `EMAIL_REGISTERED` → 07, `AUTH_REQUIRED` → 08, `INVALID_CODE` / `CODE_EXPIRED` → 11, `MEMBERSHIP_REQUIRED` → 64. Field errors stay on the screen (null). |
| - [ ] F8 | 🟠 High | **Consent is a single true/false.** It has no `withdrawn` state, no screen 02 record, no install id, no re-consent on a new policy version, and no server flag to hide 23. | [profile_routes.py](app/routers/profile_routes.py) consent section | Build M2 (`POST /v1/consent`, `GET /v1/consent/status`). |
| - [ ] F9 | 🟡 Medium | **Dev endpoints and test fields are open.** `/v1/dev/reset-test-user`, `/v1/dev/scan-debug`, `/live`, and the `face_shape_override` form field on `POST /v1/scans`. | dev_routes.py, styling_routes.py | Turn them off outside dev with one setting. |
| - [ ] F10 | 🟡 Medium | **No upload limits on `POST /v1/scans`.** There is no size cap (plan: 8 MB) and no content-type check. EXIF is already dropped, because the photo is re-saved with `cv2.imwrite`. | [scan_service.py](app/services/scan_service.py) | Add a size cap and a JPEG / PNG check. |
| - [ ] F11 | 🟡 Medium | **Two meanings of "tag" on a look.** Screen 37 has EVERYDAY / OCCASION. Screen 50 has TRACED / PREVIEWED. The model only stores the first. | `POST /v1/looks` | Keep `tag` for 37. Add a derived `kind` (traced / previewed) from tracing sessions and guides. |
| - [ ] F12 | 🟡 Medium | **No `finish` (Full / Ombre)** on render or looks. The library and the plan both use it. | render_service, `LookIn` | Add `finish` once M5 lands. |
| - [ ] F13 | 🟡 Medium | **Account delete in `../app` is immediate.** It also leaves scans, looks and photos behind in the styling database. | `../app/auth/router.py` `DELETE /auth/account` | Replace with M12: 14-day pending deletion that purges both stores. |
| - [ ] F14 | 🟢 Later | Storage is SQLite plus local files in one process. The plan wants Postgres, Redis and S3. | [db.py](app/core/db.py) | M0 production work. `db.py` is the swap point. |
| - [ ] F15 | 🟢 Later | Content marked `provisional`: colour names and hex values, skin tone → shade table, screen 17 copy for two directions, screen 28 line 3 for six face shapes, screen 30 headlines for seven styles. | [content.py](app/catalogue/content.py) | Replace each when the client confirms it. |
| - [ ] F16 | ⏸ Decide | **Legacy routes.** The plan keeps `/scan`, `/apply-style`, `/styles`, `/render`, `/enhance/*` unchanged for the current Flutter app. The README says they are not part of this build, and their source is not in this workspace. | none | Confirm whether the Flutter app still calls them. If it does, find the source (plan: `/mnt/project-files/enhance-mode`). |
| - [ ] F17 | 🟠 High | **Users live in two stores.** `/v1/auth` keeps accounts in the styling database (MongoDB was not running and there is no `.env`). Accounts already in `../app`'s MongoDB can still call the API with their old token, but cannot sign in with `/v1/auth/login`, because their password hash is in MongoDB. | `app/core/db.py`, `../app` | Decide: migrate the MongoDB users (bcrypt hashes are compatible; one script), or point the styling backend at MongoDB. Then retire `../app`. |
| - [ ] F18 | 🟡 Medium | **No email / SMS provider yet.** 2FA codes, phone codes and reset links are written to the `outbox` table (with the code in it) and never delivered. | [notify.py](app/services/notify.py) | M11: pick a provider and replace `_deliver`. Stop storing codes in the outbox at the same time. |
| - [ ] F19 | 🟡 Medium | **No rate limits** on login, register, forgot password. Codes already lock after 5 tries and resend waits 30 s. Apple / Google sign-in is built but needs `ARCH_APPLE_CLIENT_ID` / `ARCH_GOOGLE_CLIENT_IDS` and has only been tested with a stubbed token check. | auth_routes.py | Add per-IP / per-email rate limits (M0, Redis). Test social sign-in on a device. |

---

## 3. Screen-by-screen status (all 134 screens)

### Area 1 · Accounts and onboarding (20 screens)

| Screen | Name | Status | API today | What is missing or needs a fix | Module |
|---|---|---|---|---|---|
| 01 | Splash | ➖ | none | none | — |
| 02 | Before We Begin · Biometric Notice | ❌ | none | `POST /v1/consent` with type `biometric_notice`, the four boxes, policy version and install id. Link it to the account after sign-up. | M2 |
| 03 | Brand Manifesto | ➖ | none | none | — |
| 62 | Terms of Use | ➖ | none | Static text. Optional: terms version and URL in `GET /v1/config`. | M13 |
| 04 | New or Returning | ➖ | none | none | — |
| 05 | Create Account | ✅ | `POST /v1/auth/register`; `POST /v1/auth/apple`, `/v1/auth/google` | Apple / Google need client IDs set (F19). ⏸ Sign-up email verification step: none exists in `../app`. Confirm what Dev Notes 8.13 means. | M1 |
| 06 | Create Account · Error State | ✅ | 422 `VALIDATION_ERROR` with `details[{field, issue}]` (e.g. "Passwords do not match") | none | M1 |
| 07 | Account Already Exists | ✅ | 409 `EMAIL_REGISTERED` → 07 | none | M1 |
| 08 | Sign In | ✅ | `POST /v1/auth/login` → `next_screen` 14 / 20 / 21, or 11 | Sign-in cancels a pending deletion already (for M12). | M1 |
| 09 | Forgot Password | ✅ | `POST /v1/auth/password/forgot` | Email goes to the outbox until M11 (F18). | M1, M11 |
| 10 | Reset Link Sent | ✅ | Send again = same call; `POST /v1/auth/password/reset` → 08 | none | M1 |
| 11 | Two-Factor Auth | ✅ | `POST /v1/auth/2fa/verify`, `/2fa/resend` (30 s wait, lock after 5 tries) | 2FA is on when the account turns it on (`PATCH /v1/me {two_factor}`). ⏸ The client has not said when 2FA is required. | M1 |
| 12 | Guest Home | ✅ | `GET /v1/home` with `X-Guest: true` | none | M0 |
| 12a | Guest Try-On Preview | ✅ | `GET /v1/styles` | none | M5 |
| 13 | Scan Gate | ✅ | `ACCOUNT_REQUIRED` → 13; `POST /v1/onboarding/complete {carry_style}` → 29 | none | M0 |
| 13a | Account Gate (Looks and Profile) | ✅ | `ACCOUNT_REQUIRED` → 13a | none | M0 |
| 61 | How ARCH Works | ➖ ⏸ | none | Static. The privacy wording waits on the SDK partner. | — |
| 14 | Skin Tone + Goal Selection | ✅ | `GET /v1/onboarding/options`, `PUT /v1/onboarding/skin-tone-goal` | Screen 14 was updated 1 Nov. Check its copy against the new artwork. | M3 |
| 15 | Skin Tone Confirmation | ✅ | PUT response `screen_15`, `POST /v1/onboarding/confirm-tone` | The shade table is provisional (F15). | M3 |
| 16 | Style Direction Selection | ✅ | `PUT /v1/onboarding/direction` (null = skip → 18) | none | M3 |
| 17 | Style Direction Confirmation | ✅ | PUT response `screen_17` | Copy for two directions is provisional. | M3 |
| 18 | Onboarding Complete | ✅ | `POST /v1/onboarding/complete` | none | M3 |
| — | Sign-up OTP, Change Password, set new password (no screen numbers) | 🟡 ⏸ | `POST /v1/me/password`, `POST /v1/auth/password/reset` | Change and set-new-password done. Sign-up OTP: none exists to keep. Confirm with Daniyal before building one. | M1 |

### Area 2 · Home and navigation (3 screens)

| Screen | Name | Status | API today | What is missing or needs a fix | Module |
|---|---|---|---|---|---|
| 19 | Home (New User) | ✅ | `GET /v1/home` → `screen: "19"` | "Read my brows → 22" is still [to confirm]. | M3 |
| 20 | Home (Returning User) | 🟡 | Only returned **nested inside 21** (`home_returning`) | It is never returned as `screen: "20"`. Agree when 20 shows and when 21 shows (after sign-in 08 / 11, and the Home tab). | M3, M8 |
| 21 | Personalised Returning Welcome | ✅ | `GET /v1/home` → `screen: "21"` with the last look | RE-APPLY → 36 is still [to confirm]. | M8 |

### Area 3 · Brow experience: try-on (19 screens)

| Screen | Name | Status | API today | What is missing or needs a fix | Module |
|---|---|---|---|---|---|
| 22 | Face Scan Intro | ✅ | `GET /v1/styles` for "Browse styles directly" | none | — |
| 23 | Camera Permission + Face Scan Consent | 🟡 | `POST /v1/consents/face-scan`, `GET /v1/consents` | No `withdrawn` state, no status endpoint, no server flag to hide 23 (F8). | M2 |
| 24 | Camera Access Settings | ➖ | none | iOS Settings | — |
| 25 | Scanning Active | ✅ | `POST /v1/scans` | Upload size and type limits (F10). | M4 |
| 26 | Face Not In Frame | ✅ | Error codes → 26 | none | M4 |
| 27 | Scan Complete | ✅ | Scan response `screen_27`, `GET /v1/scans/{id}` | none | M4, M6 |
| 28 | Post-Scan Discovery | ✅ | Scan response `screen_28` | Line 3 copy is provisional for six face shapes. | M4 |
| 29 | Style Selector | 🟡 | `GET /v1/styles?scan_id=`, `GET /v1/colours`, `POST /v1/tryon/render` | With a scan it works. **No-scan states** (added on map page 15) need the library image of the style, and the library is missing (M5). | M5, M7 |
| 30 | Style Applied | ✅ | `POST /v1/tryon/render` (mode remembered per account) | none | M7, M3 |
| 30a | Mode Introduction (first use) | ✅ | `show_mode_intro_30a`, `GET /v1/modes`, `POST /v1/me/flags` | none | M3 |
| 31 | Intensity Selector | ✅ | `POST /v1/tryon/intensities`, `GET /v1/intensities` | "Compare two intensities → 35a" is still [to confirm]. | M7 |
| 32 | Intensity · Understated | ✅ | `POST /v1/tryon/render` with `intensity` | none | M7 |
| 33 | Intensity · Defined | ✅ | same | none | M7 |
| 34 | Intensity · Deliberate | ✅ | same | none | M7 |
| 35a | Two Looks · Selection | ✅ | thumbnails from `POST /v1/tryon/intensities` | none | M7 |
| 35b | Two Looks · Comparison | ✅ | `POST /v1/tryon/compare` | none | M7 |
| 36 | This Is Your Look | 🟡 | `POST /v1/tryon/render`, `GET /v1/looks/{id}` | TRACE THIS LOOK → 36a needs tracing (M9). ⏸ What 36 shows from each entry (question 9). | M7, M8 |
| 37 | Save Look | 🟡 | `POST /v1/looks` | Needs the membership gate → 64 (F4). Defaults (F5). | M8, M10 |
| 38 | Saved Confirmation | ✅ | `POST /v1/looks` response `screen_38` | none | M8 |

### Area 4 · Brow experience: recommendation (6 screens + 2 added states)

| Screen | Name | Status | API today | What is missing or needs a fix | Module |
|---|---|---|---|---|---|
| 39 | Recommendation Intro (first time / already scanned) | 🟡 | `GET /v1/scans/latest` (404 = first time) | Works, but a 404 for a normal state is awkward. Add `has_scan` to `GET /v1/home` or `GET /v1/profile`. ⏸ How old a scan may be (question 13). | M4, M6 |
| 40 | Reading Face | ➖ ⏸ | reuses the latest scan | AR / animation. Stays until the AR partner confirms (question 3). | M6 |
| 41 | Your Result | 🟡 | `recommendation` inside the scan response | Add `GET /v1/recommendations` (latest scan): face shape, recommended, alternate, avoid. "TRY TOP RECOMMENDATION → 42" is still [to confirm]. | M6 |
| 42 | Why This Shape (View 1) | ❌ | none | The "about this shape" bullets per style | M6 |
| 43 | Why This Shape (View 2) | ❌ ⏸ | `FACE_SHAPE_TAGLINES` exists only in part | Face shape explanation copy, and the proportion outline fitted to her landmarks. Copy is a draft (question 14). | M6 |
| 44 | The Difference | 🟡 | `GET /v1/tryon/before` (before half only) | `POST /v1/tryon/before-after` returning both panels. ENTRY GAP from 41 still open. | M7 |

### Area 5 · Brow experience: tracing (41 screens)

Live tracing runs on the device. The backend stores sessions, guides and results, and checks membership.

| Screen | Name | Status | API today | What is missing or needs a fix | Module |
|---|---|---|---|---|---|
| 36a | Before You Trace | ❌ | none | Membership gate at BEGIN → 64. `POST /v1/tracing/sessions` (type from mode: reshape = SCULPT, refine = REFINE). | M9, M10 |
| 73 | Setup Check | ➖ | none | AR on the device | M9 |
| 73a | Setup light too low | ➖ | none | AR on the device | — |
| 74 / 74a | Position & Adjust (portrait / landscape) | ➖ | none | AR on the device. Uses `GET /v1/styles` measurements. | — |
| 75-01 … 75-10 | SCULPT stages (10) | ❌ | none | `PATCH /v1/tracing/sessions/{id}` (stage reached) | M9 |
| 76-01 … 76-10 | REFINE stages (10) | ❌ | none | same | M9 |
| 75g | Landscape tracing | ➖ | none | none | — |
| 75a | Interrupted | ➖ | none | none | — |
| 75d | Exit Confirmation | ❌ ⏸ | none | `POST /v1/tracing/sessions/{id}/leave`. Does leaving discard anything (question 6)? | M9 |
| 75b / 75c / 75e / 75f | Light low, tracking lost, hand occlusion (partner ⏸), recovery | ➖ | none | AR on the device | — |
| 77 | Tracing · Completion | ❌ | none | `POST /v1/tracing/sessions/{id}/complete`. Attaches to the saved look, or creates a new TRACED look. | M9, M8 |
| 49c | Tracing Unavailable | ➖ | none | none | — |
| 45 | Tracing Guide Intro | ➖ | none | none | — |
| 46 / 47 / 48 | Draw, Erase, Reset | ➖ | none | Drawing on the device | — |
| 49 | Guide Complete | 🟡 ⏸ | none | SHARE → 52 is [to confirm]. | M9 |
| 49a | Save Guide | ❌ | none | `POST /v1/guides` (name, strokes, image). Saved as a TRACED look. Member only. | M9 |
| 49b | Guide Saved | ❌ | none | Response of `POST /v1/guides`; then `GET /v1/looks?tab=traced` | M9 |

### Area 6 · My Looks and profile (25 screens)

| Screen | Name | Status | API today | What is missing or needs a fix | Module |
|---|---|---|---|---|---|
| 50 | My Looks (Populated) | 🟡 | `GET /v1/looks`, `DELETE /v1/looks/{id}` | `?tab=all\|traced\|previewed` filter, a derived traced / previewed kind (F11), `PATCH /v1/looks/{id}` (rename). Look card → 36 is [to confirm]. | M8 |
| 51 | My Looks (Empty State) | 🟡 | `GET /v1/looks` (empty list) | Free accounts must get an empty list, not an error, plus `is_member` for the "See what membership includes → 64" line. | M8, M10 |
| 52 | Share This Look | 🟡 | `images.full` on the look | `POST /v1/looks/{id}/share-image` (formatted share image with caption) | M8 |
| 89 to 94 | Looks · The Library (1 to 6 of 6) | ❌ | none | `GET /v1/library?tone=&finish=`, `GET /v1/library/editorial`, CDN manifest of 252 WebP images. ENTRY GAP into 89. Look card → 36 is [to confirm]. | M5 |
| 53 | Profile Home | 🟡 | `GET /v1/me` (real account, "With us since …") | MEMBER badge needs entitlements (M10). Avatar not stored. | M1, M10 |
| 54 | My Account (Edit) | 🟡 | `GET` / `PATCH /v1/me` (name, email with password), phone via 65 | Payment method, current plan and renewal date (M10). | M1, M10 |
| 55 | Brow Profile | 🟡 | `GET /v1/profile` | Return face shape, preferred style, preferred colour and last scan date as labels. Return `has_scan` so the app shows 55f. | M4 |
| 55a | Brow Profile · Editable | ❌ ⏸ | none | `PATCH /v1/me/brow-profile` (preferred style and colour). Routes are [to confirm]. | M4 |
| 55b | Delete my face scan · Step 1 | ➖ | none | No call. Nothing is deleted yet. | — |
| 55c | Delete my face scan · Step 2 | ❌ | none | `DELETE /v1/me/face-scan {"remove_photographs": true\|false}`. Removes measurements, brow profile and scan photos. Optionally removes look photographs but keeps the recipes. Sets consent to withdrawn. | M4, M2 |
| 55d / 55e | Done · photographs removed / kept | ❌ | none | Response of the call above. SCAN AGAIN → 23 is [to confirm]. | M4 |
| 55f | Brow Profile · no scan | ❌ | none | `GET /v1/profile` with `has_scan: false` | M4 |
| 56 | Preferences | ❌ | none | `GET` / `PATCH /v1/me/preferences` (notifications, auto-save looks, camera auto-detect, language) | M3 |
| 57 | Language & Region | ❌ | none | Same endpoint, six languages | M3 |
| 58 | Help & Support | ➖ | none | Static menu | — |
| 59 | Contact Us | ❌ | none | `POST /v1/support/messages` (sends to office@cbygroyals.com) | M13 |
| 60 | About ARCH | ➖ | none | none | — |
| 61, 62 | How ARCH Works, Terms | ➖ | none | (listed in Area 1) | — |

### Area 7 · Membership, deletion, notifications, errors (20 screens)

| Screen | Name | Status | API today | What is missing or needs a fix | Module |
|---|---|---|---|---|---|
| 64 | Membership Gate (Unlock) | ❌ | none | `GET /v1/me/entitlements`; prices from `GET /v1/config` ($19.99 / $179.99). ENTRY GAP: no gate trigger is locked. | M10, M13 |
| 66 | Payment Details (web) | ❌ ⏸ | none | Web checkout. Which provider? | M10 |
| 65 | Phone Number (Trial Start) | ✅ | `POST /v1/me/phone`, `POST /v1/me/phone/verify` → 67 | SMS goes to the outbox until M11 (F18). | M1 |
| 67 | Free Trial Begun | ❌ | none | `POST /v1/billing/apple/verify` / `google/verify`; trial dates (FREE UNTIL, FIRST CHARGE) | M10 |
| 63 | Membership Standing | ❌ | none | `GET /v1/me/entitlements` (plan, status) | M10 |
| 70 | Cancellation Retention | ➖ | none | Native `showManageSubscriptions(in:)`; CONTACT US → 59 | — |
| 71 | Cancel Membership | ❌ | none | Web cancel; access-until date; refund wording key from `GET /v1/config` | M10, M13 |
| 72 | Membership Cancelled | ❌ | none | Last look, access until, "sent to email" | M10, M11 |
| 68 | Payment Failed | ❌ | none | Store webhooks set the grace state; grace length (16 days) from config | M10, M11 |
| 69 | Update Payment | ❌ | none | Web payment update | M10 |
| 78 | Delete My Account | 🟡 | `DELETE /auth/account` (`../app`) | Immediate hard delete is wrong (F13). Needs `POST /v1/me/delete` with a 14-day `purge_at`. | M12 |
| 79 | Deletion Confirmation Modal | 🟡 | same | same | M12 |
| 80 | Deletion Underway | ❌ | none | Deletion email; API reports whether it was sent, so the app can hide the line | M12, M11 |
| 81 | Sign Out Modal | ✅ ⏸ | `POST /v1/auth/logout` → 08 (session revoked; access and refresh stop working) | SIGN OUT → 08 is [to confirm]. | M1 |
| 82 | Notification Priming | ❌ | none | `POST /v1/devices` (push token, platform), `DELETE /v1/devices/{id}`. ENTRY GAP: entry point not locked. | M11 |
| 83 | Native OS Permission Dialog | ➖ | none | Native | — |
| 84 | Scan Lighting Error | ✅ | `LOW_LIGHT` → 84 | none | M4 |
| 85 | Scan Slow | ➖ | none | App timeout | — |
| 87 | Between Connections | ➖ ⏸ | none | App offline state. Partner question. | — |
| 88 | Generic Error | ✅ | any 5xx → `route_to: "88"` | none | M0 |

---

## 4. Missing APIs by module (build checklist)

Tick each box when the endpoint is built, tested and in Swagger.

### M1 · Identity and accounts (Block 1)
- [x] Connect the styling backend to the existing JWT login (F3)
- [x] `POST /v1/auth/register` → 409 `EMAIL_REGISTERED` (07)
- [x] `POST /v1/auth/login` with 2FA branch
- [x] `POST /v1/auth/apple`, `POST /v1/auth/google` (needs client IDs, F19)
- [x] `POST /v1/auth/2fa/verify`, `POST /v1/auth/2fa/resend`
- [x] `POST /v1/auth/password/forgot`, `POST /v1/auth/password/reset`, `POST /v1/me/password`
- [x] `POST /v1/auth/refresh` (rotating), `POST /v1/auth/logout`
- [x] `GET` / `PATCH /v1/me` (replace stub)
- [x] `POST /v1/me/phone`, `POST /v1/me/phone/verify`
- [ ] Sign-up email verification / OTP ⏸ (none found to keep)
- [ ] One user store (F17), rate limits (F19)

### M2 · Consent and legal
- [ ] `POST /v1/consent` (biometric_notice for 02, face_scan for 23, policy version, install id)
- [ ] `GET /v1/consent/status` → none / granted / withdrawn
- [ ] Withdraw on Delete my face scan
- [ ] Server flag to hide screen 23

### M3 · Profile and preferences
- [x] Onboarding 14 to 18
- [x] `POST /v1/me/flags` (30a)
- [x] Remembered mode per account (F5)
- [ ] `GET` / `PATCH /v1/me/preferences` (56, 57)
- [ ] Home: return 20 on its own (Area 2)

### M4 · Face scan and brow profile
- [x] `POST /v1/scans`, `GET /v1/scans/latest`, `GET /v1/scans/{id}`
- [ ] Upload limits (F10)
- [ ] `GET /v1/me/brow-profile` with `has_scan` (55, 55f, 39)
- [ ] `PATCH /v1/me/brow-profile` (55a)
- [ ] `DELETE /v1/me/face-scan` (55c to 55e)

### M5 · Catalogue and library
- [x] `GET /v1/styles`, `/v1/styles/{id}`, `/v1/colours`, `/v1/intensities`, `/v1/modes`, `/v1/face-shapes`
- [ ] Per-tone colour hex (Deep, Rich), `supports_ombre`, `finish`
- [ ] `GET /v1/library?tone=&finish=` (89 to 94, 29 no-scan preview)
- [ ] `GET /v1/library/editorial`

### M6 · Recommendations
- [x] Recommendation inside the scan response
- [ ] `GET /v1/recommendations` (41)
- [ ] Copy for 42 per style, copy and outline for 43 per face shape

### M7 · Try-on
- [x] `POST /v1/tryon/render`, `/tryon/intensities`, `/tryon/compare`, `GET /v1/tryon/before`
- [ ] `POST /v1/tryon/before-after` (44)
- [x] Remove silent defaults (F5)

### M8 · Looks
- [x] `POST /v1/looks`, `GET /v1/looks`, `GET /v1/looks/{id}`, `DELETE /v1/looks/{id}`
- [ ] `GET /v1/looks?tab=all|traced|previewed`
- [ ] `PATCH /v1/looks/{id}` (rename)
- [ ] `POST /v1/looks/{id}/share-image` (52)
- [ ] Membership gate on save (F4)

### M9 · Tracing and guides
- [ ] `POST /v1/tracing/sessions` (member only)
- [ ] `PATCH /v1/tracing/sessions/{id}`
- [ ] `POST /v1/tracing/sessions/{id}/complete`
- [ ] `POST /v1/tracing/sessions/{id}/leave`
- [ ] `POST /v1/guides`

### M10 · Membership and billing
- [ ] Entitlement service (guest, free, member) replacing `can()`
- [ ] `GET /v1/me/entitlements`
- [ ] `POST /v1/billing/apple/verify`, `/google/verify`, `/restore`
- [ ] `POST /v1/webhooks/apple`, `/google`, `/web`
- [ ] Web checkout and payment update (66, 69)

### M11 · Notifications and email
- [ ] `POST /v1/devices`, `DELETE /v1/devices/{id}`
- [ ] Email templates: reset, 2FA, trial started, trial ending, payment failed, cancelled, renewal reminder, deletion

### M12 · Privacy and data lifecycle
- [ ] `POST /v1/me/delete` (14-day pending, cancel on sign-in)
- [ ] Purge job (both stores, media too) and `deletion_audit`
- [ ] 24-month retention sweep (built, switched off)

### M13 · Support and remote config
- [x] `GET /v1/config` (enums only)
- [ ] Add prices, plan names, trial length, refund wording key, privacy URL, feature flags
- [ ] `POST /v1/support/messages`

### M14 · Admin and operations
- [ ] Internal admin, dashboards, feature flags

### M0 · Platform (production)
- [x] Commit `app/main.py` (F1)
- [ ] Private media and signed URLs (F2)
- [x] One error shape (F6) and route_to 88 by default (F7)
- [ ] Turn off dev routes outside dev (F9)
- [ ] Postgres, Redis, S3, Docker, CI (F14)

---

## 5. Summary

| Area | Screens | ✅ Built | 🟡 Incomplete | ❌ Missing | ➖ No backend |
|---|---|---|---|---|---|
| 1 Accounts and onboarding | 20 | 16 | 0 | 1 | 3 |
| 2 Home | 3 | 2 | 1 | 0 | 0 |
| 3 Try-on | 19 | 14 | 4 | 0 | 1 |
| 4 Recommendation | 6 | 0 | 3 | 2 | 1 |
| 5 Tracing | 41 | 0 | 1 | 25 (36a, 20 stages, 75d, 77, 49a, 49b) | 15 |
| 6 Looks and profile (incl. 61, 62) | 25 | 0 | 6 | 14 (incl. 89 to 94) | 5 |
| 7 Membership, deletion, notifications, errors | 20 | 4 | 2 | 10 | 4 |
| **Total** | **134** | **36** | **17** | **52** | **29** |

So 105 screens need backend work (134 minus 29 with no backend). Of those, 36 are done, 17 need fixing and 52 are still to build. Screens flagged ⏸ are counted under their main status.

**Where things stand:** the styling journey 12 to 38 is built, and real login (M1) is in. Everything after saving a look is still to build: tracing, the library, recommendation detail, profile editing, face scan deletion, membership, notifications and account deletion. Membership still needs connecting.

**Suggested next steps:**
1. F2 (private media, signed URLs). Small and urgent.
2. Decide F17 (one user store) and the open sign-up OTP question.
3. Do M2 consent and M4 brow profile / Delete my face scan (55 to 55f). These are new in the 30 October round.
4. Build M10 entitlements, so 37, 36a and 49a can be gated.
5. Then build M8 looks tabs, M9 tracing and M5 library.

---

## 6. Change log

| Date | Change |
|---|---|
| 2026-11-06 | **Block 1.** F1, F3, F5, F6, F7 fixed. M1 built (13 endpoints under `/v1/auth` and `/v1/me`). 35 tests pass, including the full photo journey. New items F17 to F19.
| 2026-11-06 | File created. Baseline scan of `arch-styling-backend` (34 routes) and `../app` auth (8 routes) against the 30 October screen map and the 3 November build plan. |
