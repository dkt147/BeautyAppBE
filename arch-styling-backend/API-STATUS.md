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
| 46 | `POST /v1/consent`, `GET /v1/consent/status` | 02, 23 | [profile_routes.py](app/routers/profile_routes.py) |
| 47 | `GET` / `PATCH /v1/me/brow-profile` | 39, 55, 55a, 55f | [privacy_routes.py](app/routers/privacy_routes.py) |
| 48 | `DELETE /v1/me/face-scan` | 55c → 55d / 55e | privacy_routes.py |
| 49 | `POST /v1/me/delete` | 79 → 80 | privacy_routes.py |
| 50 | `POST /v1/dev/run-jobs` (dev only) | none | privacy_routes.py |
| 51 | `GET /v1/catalogue` | all | [library_routes.py](app/routers/library_routes.py) |
| 52 | `GET /v1/library`, `GET /v1/library/editorial` | 89 to 94, 29 no-scan | library_routes.py |
| 53 | `POST /v1/tryon/before-after` | 44 | styling_routes.py |
| 54 | `GET /v1/looks?tab=` (now with `kind`) | 50, 51 | styling_routes.py |
| 55 | `POST /v1/tracing/sessions`, `GET` / `PATCH /v1/tracing/sessions/{id}` | 36a, 73, 75-xx, 76-xx | [tracing_routes.py](app/routers/tracing_routes.py) |
| 56 | `POST /v1/tracing/sessions/{id}/complete`, `/save`, `/leave` | 77, 75d | tracing_routes.py |
| 57 | `POST /v1/guides`, `GET /v1/guides`, `GET` / `DELETE /v1/guides/{id}` | 49a, 49b | tracing_routes.py |
| 58 | `GET /v1/recommendations`, `GET /v1/recommendations/{style}` | 41, 42, 43 | [account_routes.py](app/routers/account_routes.py) |
| 59 | `GET` / `PATCH /v1/me/preferences` | 56, 57 | account_routes.py |
| 60 | `PATCH /v1/looks/{id}`, `POST /v1/looks/{id}/share-image` | 50, 52 | account_routes.py |
| 61 | `POST` / `GET /v1/devices`, `DELETE /v1/devices/{id}` | 82, 83 | account_routes.py |
| 62 | `GET /v1/me/entitlements` | 13, 51, 53, 54, 63, 64, 67, 68, 71, 72 | account_routes.py |
| 63 | `POST /v1/billing/apple/verify`, `/google/verify`, `/restore`, `/web/checkout` (503) | 64 → 65, 66 | account_routes.py |
| 64 | `POST /v1/webhooks/apple`, `/google`, `/web` | 68, 71, 72 | account_routes.py |
| 65 | `POST /v1/support/messages` | 59 | account_routes.py |
| 66 | `POST /v1/dev/grant-membership` (dev only) | none | account_routes.py |
| 67 | `GET /media/{path}?exp=&sig=` (signed, private) | every image | [media.py](app/core/media.py) |

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
| - [x] F2 | ✅ Done | **Face photos were public.** | [media.py](app/core/media.py) | Block 3: the public `/media` mount is gone. Every `/media` URL in a response is signed (HMAC) and expires after 15 min (`ARCH_MEDIA_URL_MINUTES`); stored documents keep plain paths, so nothing goes stale. Unsigned, tampered, expired or out-of-folder links answer 403 / 404. |
| - [x] F3 | ✅ Done (see F17) | **Two separate logins.** | [auth.py](app/core/auth.py) | Block 1: `current_user` validates the bearer JWT (HS256, `sub`, same `JWT_SECRET` as `../app`, so its tokens work). Sessions can be revoked. No token = guest. `ARCH_DEV_AUTO_LOGIN` defaults to `false` and only works with `ARCH_ENV=dev`. |
| - [x] F4 | ✅ Done | **Entitlement stub.** | [billing_service.py](app/services/billing_service.py) | Block 3: guest / free / member. Free accounts get `MEMBERSHIP_REQUIRED` → 64 on save (37), tracing (36a), guides (49a); `GET /v1/looks` answers 51 with the membership line. |
| - [x] F5 | ✅ Done | **Silent defaults.** | [styling_routes.py](app/routers/styling_routes.py) `_resolve`, [profile_service.py](app/services/profile_service.py) | Block 1: colour, intensity and mode are optional and filled only from request → brow profile → scan. Each response says where each value came from (`resolved_from`). No intensity anywhere → 422 `INTENSITY_REQUIRED`. Mode is remembered per account and starts as Refine mine (or the style direction's mode). `DEFAULT_COLOUR` / `DEFAULT_MODE` removed. ⏸ The map draws RESHAPE MINE selected; the plan says Refine. Confirm with the client (one line: `STARTING_MODE` in content.py). |
| - [x] F6 | ✅ Done (styling) | **One error shape.** | [errors.py](app/core/errors.py) | Block 1: `{"detail", "code", "route_to"}` plus optional `details` / `retry_after`. `../app` still returns FastAPI's `{"detail"}` and is now superseded by `/v1/auth` (see F17). |
| - [x] F7 | ✅ Done | **Unknown errors gave `route_to: null`.** | [errors.py](app/core/errors.py), [content.py](app/catalogue/content.py) | Block 1: any 5xx → "88". Added `EMAIL_REGISTERED` → 07, `AUTH_REQUIRED` → 08, `INVALID_CODE` / `CODE_EXPIRED` → 11, `MEMBERSHIP_REQUIRED` → 64. Field errors stay on the screen (null). |
| - [x] F8 | ✅ Done | **Consent was a single true/false.** | [consent_service.py](app/services/consent_service.py) | Block 2: M2 built. Records for 02 and 23 kept apart, with policy version and time; none / granted / withdrawn; 02 held by install id and linked at sign-up / sign-in; `ARCH_SCREEN_23_ENABLED` flag. |
| - [x] F9 | ✅ Done | **Dev endpoints open.** | [devtools.py](app/core/devtools.py) | Block 3: `/v1/dev/*`, `/live` and `face_shape_override` answer 404 / are ignored and are hidden from Swagger unless `ARCH_ENV=dev`. Production also refuses to start without `ARCH_JWT_SECRET`. |
| - [x] F10 | ✅ Done | **No upload limits.** | [styling_routes.py](app/routers/styling_routes.py) `_read_upload` | Block 2: JPEG / PNG only (type and file signature), 8 MB cap (`ARCH_MAX_UPLOAD_MB`). 415 `UNSUPPORTED_IMAGE_TYPE`, 413 `IMAGE_TOO_LARGE`. |
| - [x] F11 | ✅ Done | **Two meanings of "tag".** | [looks_service.py](app/services/looks_service.py) | Block 2: `tag` stays for 37. `kind` (traced / previewed) is derived from completed tracing sessions and guides, and `GET /v1/looks?tab=` filters on it. |
| - [x] F12 | ✅ Done | **No `finish`.** | render_service, renderer, looks | Block 2: `finish` (full / ombre) on render, intensities, compare, before-after, looks and tracing. Ombre is refused for Straight and Micro (`FINISH_NOT_AVAILABLE`). See F21. |
| - [x] F13 | ✅ Done (styling) | **Immediate account delete.** | [privacy_service.py](app/services/privacy_service.py) | Block 2: `POST /v1/me/delete` marks the account pending, purges after 14 days, purges every table and media folder, writes `deletion_audit`. `../app`'s `DELETE /auth/account` still deletes at once: switch it off when `../app` is retired (F17). |
| - [ ] F14 | 🟢 Later | Storage is SQLite plus local files in one process. The plan wants Postgres, Redis and S3. | [db.py](app/core/db.py) | M0 production work. `db.py` is the swap point. |
| - [ ] F15 | 🟢 Later | Content marked `provisional`: colour names and hex values, skin tone → shade table, screen 17 copy for two directions, screen 28 line 3 for six face shapes, screen 30 headlines for seven styles. | [content.py](app/catalogue/content.py) | Replace each when the client confirms it. |
| - [ ] F16 | ⏸ Decide | **Legacy routes.** The plan keeps `/scan`, `/apply-style`, `/styles`, `/render`, `/enhance/*` unchanged for the current Flutter app. The README says they are not part of this build, and their source is not in this workspace. | none | Confirm whether the Flutter app still calls them. If it does, find the source (plan: `/mnt/project-files/enhance-mode`). |
| - [ ] F17 | 🟠 High | **Users live in two stores.** `/v1/auth` keeps accounts in the styling database (MongoDB was not running and there is no `.env`). Accounts already in `../app`'s MongoDB can still call the API with their old token, but cannot sign in with `/v1/auth/login`, because their password hash is in MongoDB. | `app/core/db.py`, `../app` | Decide: migrate the MongoDB users (bcrypt hashes are compatible; one script), or point the styling backend at MongoDB. Then retire `../app`. |
| - [ ] F18 | 🟡 Medium | **No email / SMS provider yet.** 2FA codes, phone codes and reset links are written to the `outbox` table (with the code in it) and never delivered. | [notify.py](app/services/notify.py) | M11: pick a provider and replace `_deliver`. Stop storing codes in the outbox at the same time. |
| - [x] F19 | ✅ Done (one process) | **No rate limits.** | [ratelimit.py](app/core/ratelimit.py) | Block 3: per-address limits on register (10/h), login (10/5 min), 2FA (10/5 min), forgot password (5/15 min), Apple / Google (20/5 min), contact (5/h) → 429 `RATE_LIMITED` + `retry_after`. Moves to Redis with F14. Social sign-in still untested against Apple / Google (F23). |
| - [ ] F20 | 🟡 Medium | **Brow library images are not uploaded and the manifest is ours.** `library_manifest.csv` is built from the naming convention (`tools/build_library_manifest.py`, every row `source=convention`), and `ARCH_LIBRARY_CDN_BASE` is not set, so `url_*` is null and only `path_*` is returned. Per-tone colour hex values (Dev Notes 7, deeper for Deep / Rich) were not in the files received (`colour_by_tone: null`). | [library_service.py](app/services/library_service.py) | Replace the CSV with the client's manifest, upload the WebP set, set the CDN base. Get the per-tone hex table. |
| - [ ] F21 | 🟡 Medium | **Ombre look and base finish are our reading.** Ombre fades the powder and hairs from 28% at the head to full colour by 60% of the length. A request with no finish renders Full (`resolved_from.finish = "base_finish"`), because every style has Full and only six have Ombre. | [brow_renderer.py](app/rendering/brow_renderer.py) `_ombre_ramp`, content.py `BASE_FINISH` | Check the Ombre renders against the client's Ombre library images. Confirm Full as the base finish. |
| - [ ] F22 | 🟡 Medium | **Privacy jobs need a scheduler.** `tools/run_jobs.py` (purge due accounts, retention sweep) must run hourly from cron / Task Scheduler. The retention sweep is off (`ARCH_RETENTION_SWEEP_ENABLED`) until question 17 is answered. The plan's restore rule (replay `deletion_audit` after a backup restore) is not built. | tools/run_jobs.py | Add the worker / scheduler in M0. |
| - [ ] F23 | 🟠 High | **Store and push credentials.** Billing code is built and tested with our own test certificate chain and stubbed Google responses, never against the real stores. Needed: Apple Root CA - G3 file (`ARCH_APPLE_ROOT_CA_PATH`), bundle id and product ids, Google service account (`ARCH_GOOGLE_SERVICE_ACCOUNT_JSON`), Pub/Sub audience, FCM / APNs keys (push goes to the outbox until then), Apple / Google sign-in client ids. | config.py | Set them in staging and run a sandbox purchase, renewal, grace and refund on each store. |
| - [ ] F24 | ⏸ Decide | **Web payments (66, 69).** No provider is chosen (backend question). `POST /v1/billing/web/checkout` answers 503. A provider-neutral signed webhook (`POST /v1/webhooks/web`, HMAC in `X-Signature`) is built and tested. | billing_service.py | Choose the provider, then build checkout and payment update on its API. |
| - [ ] F25 | 🟡 Medium | **Our readings to confirm.** 19 vs 20 (19 is the first Home after onboarding, then 20); 56 switches start as drawn (Notifications on, Auto-save on, Camera auto-detect off); 42 / 43 copy is drafted except Arch and Oval (question 14); Android refund wording not received (`null`); subscription records are kept after an account purge (financial records), devices are deleted. | content.py, recommend_copy.py | Confirm with the client. |

---

## 3. Screen-by-screen status (all 134 screens)

### Area 1 · Accounts and onboarding (20 screens)

| Screen | Name | Status | API today | What is missing or needs a fix | Module |
|---|---|---|---|---|---|
| 01 | Splash | ➖ | none | none | — |
| 02 | Before We Begin · Biometric Notice | ✅ | `POST /v1/consent` type `biometric_notice` (four boxes) with `X-Install-Id`; `GET /v1/consent/status` | Linked to the account at sign-up / sign-in. ⏸ Re-consent on a new policy version (question 2) is behind `ARCH_RECONSENT_ON_POLICY_CHANGE`, off. | M2 |
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
| 20 | Home (Returning User) | ✅ ⏸ | `GET /v1/home` → `screen: "20"` (returning, no saved look) | 19 → 20 rule is ours (F25). | M3, M8 |
| 21 | Personalised Returning Welcome | ✅ | `GET /v1/home` → `screen: "21"` with the last look | RE-APPLY → 36 is still [to confirm]. | M8 |

### Area 3 · Brow experience: try-on (19 screens)

| Screen | Name | Status | API today | What is missing or needs a fix | Module |
|---|---|---|---|---|---|
| 22 | Face Scan Intro | ✅ | `GET /v1/styles` for "Browse styles directly" | none | — |
| 23 | Camera Permission + Face Scan Consent | ✅ | `POST /v1/consent` type `face_scan` (alias `POST /v1/consents/face-scan`), `GET /v1/consent/status` → `show_screen_23` | Server flag `ARCH_SCREEN_23_ENABLED`. | M2 |
| 24 | Camera Access Settings | ➖ | none | iOS Settings | — |
| 25 | Scanning Active | ✅ | `POST /v1/scans` (JPEG / PNG, 8 MB cap) | none | M4 |
| 26 | Face Not In Frame | ✅ | Error codes → 26 | none | M4 |
| 27 | Scan Complete | ✅ | Scan response `screen_27`, `GET /v1/scans/{id}` | none | M4, M6 |
| 28 | Post-Scan Discovery | ✅ | Scan response `screen_28` | Line 3 copy is provisional for six face shapes. | M4 |
| 29 | Style Selector | ✅ | `GET /v1/styles?scan_id=`, `GET /v1/colours`, `POST /v1/tryon/render`; no-scan preview `GET /v1/library?style=&tone=` | Library images not uploaded yet (F20). | M5, M7 |
| 30 | Style Applied | ✅ | `POST /v1/tryon/render` (mode remembered per account) | none | M7, M3 |
| 30a | Mode Introduction (first use) | ✅ | `show_mode_intro_30a`, `GET /v1/modes`, `POST /v1/me/flags` | none | M3 |
| 31 | Intensity Selector | ✅ | `POST /v1/tryon/intensities`, `GET /v1/intensities` | "Compare two intensities → 35a" is still [to confirm]. | M7 |
| 32 | Intensity · Understated | ✅ | `POST /v1/tryon/render` with `intensity` | none | M7 |
| 33 | Intensity · Defined | ✅ | same | none | M7 |
| 34 | Intensity · Deliberate | ✅ | same | none | M7 |
| 35a | Two Looks · Selection | ✅ | thumbnails from `POST /v1/tryon/intensities` | none | M7 |
| 35b | Two Looks · Comparison | ✅ | `POST /v1/tryon/compare` | none | M7 |
| 36 | This Is Your Look | ✅ ⏸ | `POST /v1/tryon/render`, `GET /v1/looks/{id}`; TRACE THIS LOOK → `POST /v1/tracing/sessions` | ⏸ What 36 shows from each entry (question 9). | M7, M8 |
| 37 | Save Look | ✅ | `POST /v1/looks` (members; free → 64) | none | M8, M10 |
| 38 | Saved Confirmation | ✅ | `POST /v1/looks` response `screen_38` | none | M8 |

### Area 4 · Brow experience: recommendation (6 screens + 2 added states)

| Screen | Name | Status | API today | What is missing or needs a fix | Module |
|---|---|---|---|---|---|
| 39 | Recommendation Intro (first time / already scanned) | ✅ ⏸ | `GET /v1/me/brow-profile` → `has_scan` | ⏸ How old a scan may be (question 13). | M4, M6 |
| 40 | Reading Face | ➖ ⏸ | reuses the latest scan | AR / animation. Stays until the AR partner confirms (question 3). | M6 |
| 41 | Your Result | ✅ ⏸ | `GET /v1/recommendations` (face shape, the two Table 2 styles, avoid, her own pick) | TRY TOP RECOMMENDATION → 42 is [to confirm]. | M6 |
| 42 | Why This Shape (View 1) | ✅ ⏸ | `GET /v1/recommendations/{style}` → `screen_42` | Copy drafted except Arch (question 14). | M6 |
| 43 | Why This Shape (View 2) | ✅ ⏸ | `GET /v1/recommendations/{style}` → `screen_43` (face-oval outline and ellipse fitted to her landmarks, drawn on her photo) | Copy drafted except Oval (question 14). | M6 |
| 44 | The Difference | ✅ | `POST /v1/tryon/before-after` (both panels, same photo) | ENTRY GAP from 41 still open (screen map). | M7 |

### Area 5 · Brow experience: tracing (41 screens)

Live tracing runs on the device. The backend stores sessions, guides and results, and checks membership.

| Screen | Name | Status | API today | What is missing or needs a fix | Module |
|---|---|---|---|---|---|
| 36a | Before You Trace | ✅ | `POST /v1/tracing/sessions` (the gate fires here; returns "You will need") | Non-members get 64 once M10 lands (F4). | M9, M10 |
| 73 | Setup Check | ➖ | none | AR on the device | M9 |
| 73a | Setup light too low | ➖ | none | AR on the device | — |
| 74 / 74a | Position & Adjust (portrait / landscape) | ➖ | none | AR on the device. Uses `GET /v1/styles` measurements. | — |
| 75-01 … 75-10 | SCULPT stages (10) | ✅ | `PATCH /v1/tracing/sessions/{id}` `{stage}` (forward only, type fixed) | none | M9 |
| 76-01 … 76-10 | REFINE stages (10) | ✅ | same | none | M9 |
| 75g | Landscape tracing | ➖ | none | none | — |
| 75a | Interrupted | ➖ | none | none | — |
| 75d | Exit Confirmation | ✅ ⏸ | `POST /v1/tracing/sessions/{id}/leave` → 36 | Nothing saved is removed. ⏸ Question 6. | M9 |
| 75b / 75c / 75e / 75f | Light low, tracking lost, hand occlusion (partner ⏸), recovery | ➖ | none | AR on the device | — |
| 77 | Tracing · Completion | ✅ | `POST /v1/tracing/sessions/{id}/complete` (state 2 if saved on 37), `/save` (state 1 → 2, new TRACED look) | ⏸ Question 5 (photo, recipe or both): a look keeps both. | M9, M8 |
| 49c | Tracing Unavailable | ➖ | none | none | — |
| 45 | Tracing Guide Intro | ➖ | none | none | — |
| 46 / 47 / 48 | Draw, Erase, Reset | ➖ | none | Drawing on the device | — |
| 49 | Guide Complete | ✅ ⏸ | SAVE MY GUIDE → 49a; SHARE → `POST /v1/looks/{id}/share-image` once saved | SHARE → 52 before saving is [to confirm]. | M9 |
| 49a | Save Guide | ✅ | `POST /v1/guides` (multipart: strokes JSON, name, image) | none | M9 |
| 49b | Guide Saved | ✅ | `POST /v1/guides` response `screen_49b`; `GET /v1/looks?tab=traced` | none | M9 |

### Area 6 · My Looks and profile (25 screens)

| Screen | Name | Status | API today | What is missing or needs a fix | Module |
|---|---|---|---|---|---|
| 50 | My Looks (Populated) | ✅ ⏸ | `GET /v1/looks?tab=`, `PATCH /v1/looks/{id}` (rename, tag), `DELETE /v1/looks/{id}` | Look card → 36 is [to confirm]. | M8 |
| 51 | My Looks (Empty State) | ✅ | `GET /v1/looks` → `screen: "51"`, `is_member`, `membership_line` → 64, `create_new_to` 29 / 22 | none | M8, M10 |
| 52 | Share This Look | ✅ | `POST /v1/looks/{id}/share-image` (her look with its name, as one image) | Save as image / Share via message are native. | M8 |
| 89 to 94 | Looks · The Library (1 to 6 of 6) | ✅ | `GET /v1/library?tone=&finish=&page=1..6` (page → screen 89..94), `GET /v1/library/editorial`, `GET /v1/catalogue` | Images and CDN (F20). ENTRY GAP into 89. Look card → 36 is [to confirm]. | M5 |
| 53 | Profile Home | ✅ | `GET /v1/me` (name, "With us since …", `membership.badge`) | Avatar: use `GET /v1/me/brow-profile` `brow_image` or the app's own. | M1, M10 |
| 54 | My Account (Edit) | ✅ | `GET` / `PATCH /v1/me` (+ `membership`: plan, renewal, payment method), phone via 65 | Changing the payment method is native (stores) or web (F24). | M1, M10 |
| 55 | Brow Profile | ✅ | `GET /v1/me/brow-profile` (face shape, preferred style and colour, last scan date, brow image) | none | M4 |
| 55a | Brow Profile · Editable | ✅ ⏸ | `PATCH /v1/me/brow-profile` | SAVE / CANCEL → 55 are [to confirm]. | M4 |
| 55b | Delete my face scan · Step 1 | ➖ | none | No call. Nothing is deleted yet. | — |
| 55c | Delete my face scan · Step 2 | ✅ | `DELETE /v1/me/face-scan {"remove_photographs": true\|false}` | Removes measurements, brow profile, scan photos; optionally look photographs (recipes kept); withdraws consent; audited. | M4, M2 |
| 55d / 55e | Done · photographs removed / kept | ✅ ⏸ | Response of the call above (`screen` 55d / 55e) | SCAN AGAIN → 23 is [to confirm]. | M4 |
| 55f | Brow Profile · no scan | ✅ | `GET /v1/me/brow-profile` → `screen: "55f"`, `has_scan: false` | none | M4 |
| 56 | Preferences | ✅ ⏸ | `GET` / `PATCH /v1/me/preferences` | Starting switch states are as drawn (F25). | M3 |
| 57 | Language & Region | ✅ | `PATCH /v1/me/preferences {language}` (six languages) | none | M3 |
| 58 | Help & Support | ➖ | none | Static menu | — |
| 59 | Contact Us | ✅ ⏸ | `POST /v1/support/messages` → office@cbygroyals.com | Email waits in the outbox until M11 provider (F18). SEND → 53 is [to confirm]. | M13 |
| 60 | About ARCH | ➖ | none | none | — |
| 61, 62 | How ARCH Works, Terms | ➖ | none | (listed in Area 1) | — |

### Area 7 · Membership, deletion, notifications, errors (20 screens)

| Screen | Name | Status | API today | What is missing or needs a fix | Module |
|---|---|---|---|---|---|
| 64 | Membership Gate (Unlock) | ✅ | `GET /v1/me/entitlements` → `offer` (prices, plans, saving, products), `GET /v1/config` | ENTRY GAP: no gate trigger is locked; every gated call returns 64. | M10, M13 |
| 66 | Payment Details (web) | ❌ ⏸ | `POST /v1/billing/web/checkout` → 503 | Provider not chosen (F24). Restore purchase: `POST /v1/billing/restore`. | M10 |
| 65 | Phone Number (Trial Start) | ✅ | `POST /v1/me/phone`, `POST /v1/me/phone/verify` → 67 | SMS goes to the outbox until M11 (F18). | M1 |
| 67 | Free Trial Begun | ✅ | `POST /v1/billing/apple/verify` / `google/verify` → `screen_67` (FREE UNTIL, FIRST CHARGE) | Live stores need F23. | M10 |
| 63 | Membership Standing | ✅ | `GET /v1/me/entitlements` → `screen_63` | none | M10 |
| 70 | Cancellation Retention | ➖ | none | Native `showManageSubscriptions(in:)`; CONTACT US → 59 | — |
| 71 | Cancel Membership | ✅ | `screen_71` (access-until date, refund wording by billing path); store cancel is native | Web cancel (F24); Android refund text not received (F25). | M10, M13 |
| 72 | Membership Cancelled | ✅ | `screen_72` once the store reports the cancellation; email sent | none | M10, M11 |
| 68 | Payment Failed | ✅ | Store webhook → `grace`; `screen_68` (days left); email + push | none | M10, M11 |
| 69 | Update Payment | ❌ ⏸ | none (store users update in the store) | Web provider (F24). | M10 |
| 78 | Delete My Account | ✅ | Static; MANAGE IN APPLE SETTINGS is native; DELETE MY ACCOUNT → 79 | `../app` `DELETE /auth/account` still immediate (F13, F17). | M12 |
| 79 | Deletion Confirmation Modal | ✅ | `POST /v1/me/delete {"confirm": true}` → 80 | none | M12 |
| 80 | Deletion Underway | ✅ | Response of `POST /v1/me/delete`: purge date, `email_sent` (hide the line when false) | Email goes to the outbox until M11 (F18). | M12, M11 |
| 81 | Sign Out Modal | ✅ ⏸ | `POST /v1/auth/logout` → 08 (session revoked; access and refresh stop working) | SIGN OUT → 08 is [to confirm]. | M1 |
| 82 | Notification Priming | ✅ | `POST /v1/devices` (token, platform, permission), `GET` / `DELETE /v1/devices`; flag `notification_prompt_seen` | ENTRY GAP: entry point not locked. FCM / APNs keys (F23). | M11 |
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
- [x] Rate limits (F19)
- [ ] One user store (F17)

### M2 · Consent and legal
- [x] `POST /v1/consent` (biometric_notice for 02, face_scan for 23, policy version, install id)
- [x] `GET /v1/consent/status` → none / granted / withdrawn
- [x] Withdraw on Delete my face scan
- [x] Server flag to hide screen 23

### M3 · Profile and preferences
- [x] Onboarding 14 to 18
- [x] `POST /v1/me/flags` (30a)
- [x] Remembered mode per account (F5)
- [x] `GET` / `PATCH /v1/me/preferences` (56, 57)
- [x] Home: return 20 on its own (Area 2)

### M4 · Face scan and brow profile
- [x] `POST /v1/scans`, `GET /v1/scans/latest`, `GET /v1/scans/{id}`
- [x] Upload limits (F10)
- [x] `GET /v1/me/brow-profile` with `has_scan` (55, 55f, 39)
- [x] `PATCH /v1/me/brow-profile` (55a)
- [x] `DELETE /v1/me/face-scan` (55c to 55e)

### M5 · Catalogue and library
- [x] `GET /v1/styles`, `/v1/styles/{id}`, `/v1/colours`, `/v1/intensities`, `/v1/modes`, `/v1/face-shapes`
- [x] `supports_ombre`, `finish`, `GET /v1/catalogue`
- [ ] Per-tone colour hex (Deep, Rich) ⏸ values not received (F20)
- [ ] Client manifest, WebP upload, CDN base (F20)
- [x] `GET /v1/library?tone=&finish=` (89 to 94, 29 no-scan preview)
- [x] `GET /v1/library/editorial`

### M6 · Recommendations
- [x] Recommendation inside the scan response
- [x] `GET /v1/recommendations` (41)
- [x] Copy for 42 per style, copy and outline for 43 per face shape

### M7 · Try-on
- [x] `POST /v1/tryon/render`, `/tryon/intensities`, `/tryon/compare`, `GET /v1/tryon/before`
- [x] `POST /v1/tryon/before-after` (44)
- [x] `finish` (Full / Ombre) on every render (F12)
- [x] Remove silent defaults (F5)

### M8 · Looks
- [x] `POST /v1/looks`, `GET /v1/looks`, `GET /v1/looks/{id}`, `DELETE /v1/looks/{id}`
- [x] `GET /v1/looks?tab=all|traced|previewed`
- [x] `PATCH /v1/looks/{id}` (rename)
- [x] `POST /v1/looks/{id}/share-image` (52)
- [x] Membership gate on save (F4)

### M9 · Tracing and guides
- [x] `POST /v1/tracing/sessions` (member only)
- [x] `PATCH /v1/tracing/sessions/{id}`
- [x] `POST /v1/tracing/sessions/{id}/complete`
- [x] `POST /v1/tracing/sessions/{id}/leave`
- [x] `POST /v1/guides`, `GET` / `DELETE /v1/guides/{id}`, `POST .../save` (77 state 1 → 2)

### M10 · Membership and billing
- [x] Entitlement service (guest, free, member) replacing `can()`
- [x] `GET /v1/me/entitlements`
- [x] `POST /v1/billing/apple/verify`, `/google/verify`, `/restore`
- [x] `POST /v1/webhooks/apple`, `/google`, `/web` (tested with our own chain / stubs; live stores need F23)
- [x] Billing jobs: lapsed access, trial-ending (2 days), annual (30 days) and monthly reminders
- [ ] Web checkout and payment update (66, 69) ⏸ provider (F24)

### M11 · Notifications and email
- [x] `POST /v1/devices`, `DELETE /v1/devices/{id}`
- [x] Every email event is sent (reset, 2FA, trial started / ending, payment failed, cancelled, renewal reminders, deletion, contact) and push goes to devices when 56 is on
- [ ] Real delivery: email / SMS provider and FCM / APNs keys (F18, F23)

### M12 · Privacy and data lifecycle
- [x] `POST /v1/me/delete` (14-day pending, cancel on sign-in)
- [x] Purge job (styling store and media) and `deletion_audit` (`tools/run_jobs.py`; needs a scheduler, F22)
- [x] 24-month retention sweep (built, switched off)

### M13 · Support and remote config
- [x] `GET /v1/config` (enums only)
- [x] Add prices, plan names, trial length, refund wording key, privacy URL, feature flags
- [x] `POST /v1/support/messages`

### M14 · Admin and operations
- [ ] Internal admin, dashboards (not built: not in Block 3). Feature flags are in `GET /v1/config`.

### M0 · Platform (production)
- [x] Commit `app/main.py` (F1)
- [x] Private media and signed URLs (F2)
- [x] One error shape (F6) and route_to 88 by default (F7)
- [x] Turn off dev routes outside dev (F9)
- [ ] Postgres, Redis, S3, Docker, CI (F14)

---

## 5. Summary

| Area | Screens | ✅ Built | 🟡 Incomplete | ❌ Missing | ➖ No backend |
|---|---|---|---|---|---|
| 1 Accounts and onboarding | 20 | 17 | 0 | 0 | 3 |
| 2 Home | 3 | 3 | 0 | 0 | 0 |
| 3 Try-on | 19 | 18 | 0 | 0 | 1 |
| 4 Recommendation | 6 | 5 | 0 | 0 | 1 |
| 5 Tracing | 41 | 26 | 0 | 0 | 15 |
| 6 Looks and profile (incl. 61, 62) | 25 | 20 | 0 | 0 | 5 |
| 7 Membership, deletion, notifications, errors | 20 | 14 | 0 | 2 (66, 69 ⏸ web provider) | 4 |
| **Total** | **134** | **103** | **0** | **2** | **29** |

So 105 screens need backend work (134 minus 29 with no backend). Of those, 103 are built. The 2 left (66, 69) wait for the web payment provider. Screens flagged ⏸ are counted under their main status.

**Where things stand:** every screen that needs the backend has its API, except web payments (66, 69), which wait for a provider. What stands between this and production is outside the code's reach or not yet built: store, email, SMS and push credentials (F23, F18), Postgres / Redis / S3 / a scheduler (F14, F22), one user store (F17), the library files (F20), the admin tool (M14), and the client's answers on the ⏸ items.

**Suggested next steps:**
1. Staging with real credentials (F23): sandbox purchase, renewal, grace and refund on both stores; Apple / Google sign-in on a device.
2. Production infrastructure (F14, F22): Postgres, Redis (rate limits, caches), S3 for media, a worker for `tools/run_jobs.py`.
3. Decide F17 (one user store) and F24 (web provider); pick the email / SMS / push providers (F18).
4. Client answers: questions 2, 5, 6, 9, 13, 14, 16, 17, the library files and per-tone colours (F20), Ombre look (F21), F25.
5. M14 admin tool.

---

## 6. Change log

| Date | Change |
|---|---|
| 2026-11-06 | **Block 3.** F2 private signed media, F4 membership gate, F9 dev routes off outside dev, F19 rate limits. M10 entitlements + Apple (JWS chain) / Google / web billing + webhooks + billing jobs, M8 rename + share image, M11 devices + push, M13 contact + config, M6 recommendations 41-43, M3 preferences 56-57, Home 20. 69 tests pass with the photo. New items F23 to F25.
| 2026-11-06 | **Block 2.** M2 consent, M4 brow profile + Delete my face scan + F10, M12 account deletion + purge + retention sweep (off), M5 catalogue + library (manifest from the naming convention), M7 before-after + `finish` (Ombre rendering), M9 tracing sessions + guides, F11 looks tabs. F8, F10 to F13 fixed. 51 tests pass with the photo. New items F20 to F22.
| 2026-11-06 | **Block 1.** F1, F3, F5, F6, F7 fixed. M1 built (13 endpoints under `/v1/auth` and `/v1/me`). 35 tests pass, including the full photo journey. New items F17 to F19.
| 2026-11-06 | File created. Baseline scan of `arch-styling-backend` (34 routes) and `../app` auth (8 routes) against the 30 October screen map and the 3 November build plan. |
