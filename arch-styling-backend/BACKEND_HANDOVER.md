# ARCH Backend · Frontend Handover

**For:** the frontend (mobile) team.
**Backend version:** commit `c89f5df`, "Final client changes applied", 6 November 2026. It includes the Live Brow Experience Specification, Draft 3.2.
**Sources:** ARCH Visual Screen Map (30 October 2026), `docs/SCREEN_API_MAP.md`, `API-STATUS.md` and the client's Draft 3.2 change list.

---

## 1. Where the API lives

| Item | Value |
|---|---|
| Base URL, production | http://2.25.159.7:8010 |
| Base URL, staging (QA) | http://2.25.159.7:8011 |
| Swagger (interactive docs) | http://2.25.159.7:8010/docs (production), http://2.25.159.7:8011/docs (staging) |
| API prefix | Every app endpoint starts with `/v1/` |
| Request and response format | JSON, except two calls that use multipart form data: the scan upload (`POST /v1/scans`) and saving a guide (`POST /v1/guides`) |
| Health check | `GET /health` |

**Environments.** The same server runs two copies of the API:

| Port | Environment | Dev tools | Rate limits | Use it for |
|---|---|---|---|---|
| **8010** | Production (`ARCH_ENV=production`) | **Off.** `/v1/dev/*` and `/live` answer 404. | On | The real app and release builds |
| **8011** | Staging (`ARCH_ENV=staging`) | **On** | Off | QA, including membership flows without store billing |

On staging (8011):
- `POST /v1/dev/grant-membership` makes the signed-in account a member without a store, so screens 65 to 72 can be tested.
- `POST /v1/dev/reset-test-user` keeps the account, its password and its tokens. It resets onboarding, scans, looks, guides and flags, so screens 14 to 18 can run again.

The two have separate data. An account, its tokens and its images on one port do not work on the other, so sign up again on staging. Media URLs and reset links from staging start with `http://2.25.159.7:8011`.

Production will move to HTTPS on a domain later (planned: `https://api.cbygroyals.com`). Until then, both stay on the IP address.

Swagger lists every endpoint with its request fields, response fields and error codes. If this document and Swagger disagree, Swagger is correct, because it is generated from the running code.

---

## 2. Auth flow

### 2.1 Getting a token

Any of the following calls returns a token pair:

| How she signs in | Call | Screen |
|---|---|---|
| Create an account | `POST /v1/auth/register` with name, email, password and confirm_password | 05 |
| Email and password | `POST /v1/auth/login` | 08 |
| Apple | `POST /v1/auth/apple` with the Apple `id_token` | 05, 08 |
| Google | `POST /v1/auth/google` with the Google `id_token` | 05, 08 |
| Two-factor code | `POST /v1/auth/2fa/verify` with the `pending_token` and the code | 11 |

A successful response contains these fields:

| Field | Meaning |
|---|---|
| `access_token` | A JWT that you send on every request. It lasts **15 minutes**. |
| `refresh_token` | Used to get a new access token. It lasts **30 days**. |
| `token_type` | Always `bearer` |
| `expires_in` | How long the access token lasts, in seconds (900) |
| `user` | Her public profile |
| `next_screen` | The screen to open next: `14` for a new account, `20` for a returning account with no saved look, `21` for one with a saved look |
| `is_new_account`, `deletion_cancelled` | Information flags. `deletion_cancelled` is true when signing in stopped a pending account deletion. |

**Two-factor accounts:** if her account has two-factor turned on, login does not return tokens. It returns `two_factor_required: true`, `next_screen: "11"` and a `pending_token`, which lasts 10 minutes. Open screen 11 and send the code with that pending token to `POST /v1/auth/2fa/verify`. That call returns the normal token pair. To resend the code, use `POST /v1/auth/2fa/resend`. A resend sent too soon returns 429 `RESEND_TOO_SOON` with `retry_after` in seconds.

### 2.2 Sending the token

Send this header on every request:

**`Authorization: Bearer <access_token>`**

- **No header means a guest.** Guests can browse home (12), styles (12a, 22) and the library. Calls that need an account return `ACCOUNT_REQUIRED`, which routes to 13 or 13a.
- **Guest home:** to get the guest home (12), also send `X-Guest: true` on `GET /v1/home`.
- **Install ID:** send `X-Install-Id: <a stable id per install>` on the screen 02 consent call (`POST /v1/consent`), and send the same header on register and login. This links the consent she gave on screen 02, before she had an account, to her new account.

### 2.3 Keeping her signed in

1. When the access token expires, calls return 401 `AUTH_REQUIRED`.
2. Call `POST /v1/auth/refresh` with the `refresh_token`. It returns a **new** access token and a **new** refresh token.
3. Store both new tokens. Refresh tokens rotate, so an old refresh token stops working once you use it.
4. If the refresh call also fails, open screen 08 (Sign In). The error's `route_to` is `"08"`.

Sign out (81) is `POST /v1/auth/logout`. It revokes the session on the server, so both tokens stop working. Then open screen 08.

### 2.4 Membership tiers

| Tier | What happens |
|---|---|
| Guest (no token) | Gated calls return `ACCOUNT_REQUIRED` → 13 (scan or try-on) or 13a (looks or profile) |
| Free account | Saving a look (37), tracing (36a) and saving a guide (49a) return `MEMBERSHIP_REQUIRED` → 64 |
| Member (trial or paid) | Full access |

`GET /v1/me/entitlements` tells you which tier she is in.

---

## 3. Image URLs: read this before building any image view

> ⚠️ **Treat image URLs as possibly RELATIVE. If a URL starts with `/`, prepend the Base URL before you load it.**
>
> The API may return: `/media/scans/scan_ab12/face.jpg?exp=1793920000&sig=3f2a...`
> The app must then load: `http://2.25.159.7:8010/media/scans/scan_ab12/face.jpg?exp=1793920000&sig=3f2a...`
>
> The form depends on the server's `ARCH_PUBLIC_BASE_URL` setting. When it is set, as it is on the current test server, media URLs and `styles[].diagram_url` come back absolute (`http://2.25.159.7:8010/media/...`) and must be used as they are. When it is empty, they are relative. The app should handle both.

The following rules also apply:

1. **Keep the query string.** The `exp` and `sig` parameters are the signature, and without them the server answers 403.
2. **Links expire after 15 minutes.** If you keep a URL longer than that, it returns 403. Don't cache image URLs across sessions. To get fresh links, call the screen's endpoint again, for example `GET /v1/looks` or `GET /v1/scans/{id}`. You can cache the downloaded image bytes for as long as she is signed in.
3. **Face photos are private.** A link works only with its signature. A link that has been edited, has expired or points outside its folder returns 403 or 404.
4. **Render views.** A try-on response carries `images` with up to four views:

| View | Used on | What it is |
|---|---|---|
| `face` | 30, 32 to 34, 35b, 36, 37 | 4:5 portrait crop, forehead to chin |
| `brow` | 29 preview | Close-up of one brow |
| `eyes` | 31, 35a | A strip showing both brows and eyes |
| `full` | Save and share | The whole photo |

5. **Library images (89 to 94 and the no-scan preview on 29) are not hosted yet.** Their `url_*` fields are `null`, and only `path_*` is returned. Show a placeholder until the client's image set is uploaded to the CDN. When that happens, `url_*` will hold full CDN URLs that need nothing prepended.

---

## 4. Error handling

### 4.1 The error shape

Every error from every endpoint has the same JSON body:

| Field | Type | Meaning |
|---|---|---|
| `code` | string | A machine-readable code, for example `NO_FACE` or `MEMBERSHIP_REQUIRED`. Branch on this field, not on the HTTP status. |
| `detail` | string | A readable message for her. **The message field is named `detail`, not `message`.** |
| `route_to` | string or null | The screen number the app **must** open. |

Some errors add extra fields:

| Field | Found on | Meaning |
|---|---|---|
| `details` | 422 `VALIDATION_ERROR` | A list of `{field, issue}`, one per bad field. Show each issue next to its field. |
| `retry_after` | 429 `RATE_LIMITED`, `RESEND_TOO_SOON` | Seconds to wait before trying again |

### 4.2 The routing rule

**The frontend MUST open the screen named in `route_to`.**

- **`route_to` is a screen number** (for example `"26"`): navigate to that screen.
- **`route_to` is `null`:** stay on the current screen and show `detail`. If `details` is present, show each issue next to its field.
- **Any 5xx error** always has `route_to: "88"` (Generic Error).
- **Network failure with no response at all:** this is the app's offline state (87). The server can't send that one.

### 4.3 Error codes and their screens

| Code | HTTP | route_to | When |
|---|---|---|---|
| `ACCOUNT_REQUIRED` | 403 | 13 or 13a | A guest tapped scan or try-on (13), or opened looks or profile (13a) |
| `AUTH_REQUIRED` | 401 | 08 | The token is missing, expired or revoked. Refresh first (see 2.3). |
| `EMAIL_REGISTERED` | 409 | 07 | Create Account with an email that is already registered |
| `INVALID_CODE`, `CODE_EXPIRED` | 400 | 11 | Wrong or expired two-factor code |
| `MEMBERSHIP_REQUIRED` | 403 | 64 | A free account tried to save a look, trace or save a guide |
| `CONSENT_REQUIRED` | 403 | 23 | Scan without face-scan consent |
| `SCAN_REQUIRED`, `SCAN_NOT_FOUND` | 404 / 409 | 22 | The call needs a scan and she has none |
| `NO_FACE`, `MULTIPLE_FACES`, `FACE_NOT_CENTRED`, `FACE_TOO_SMALL`, `FACE_TURNED`, `BROWS_NOT_VISIBLE`, `BAD_IMAGE` | 422 | 26 | The scan photo can't be used |
| `LOW_LIGHT` | 422 | 84 | The scan photo is too dark |
| `VALIDATION_ERROR` | 422 | null | Missing or invalid fields, including **Ombre on Straight or Micro** (see section 5) |
| `UNSUPPORTED_IMAGE_TYPE` / `IMAGE_TOO_LARGE` | 415 / 413 | null | The upload is not a JPEG or PNG, or is over 8 MB |
| `RATE_LIMITED`, `RESEND_TOO_SOON` | 429 | null | Too many tries. Wait `retry_after` seconds. Sign-in counts only failed attempts (per email and per address), and a correct password resets the email's count. Sign-up allows 30 new accounts an hour per address and limits failed attempts per email. |
| `NOT_FOUND` | 404 | null | Unknown ID or path |
| `SERVER_ERROR` (any 5xx) | 500+ | 88 | Something went wrong on the server |

---

## 5. Changes in the final release (Spec Draft 3.2)

If you built against an earlier version, check these points.

1. **`finish` is now REQUIRED** on `POST /v1/tryon/render`, `/v1/tryon/intensities`, `/v1/tryon/compare`, `/v1/tryon/before-after` and `POST /v1/looks`. The values are `full` and `ombre`. If you leave it out, the response is 422 `VALIDATION_ERROR`.
2. **Ombre is not offered for Straight or Micro.** Sending `finish: ombre` with either style returns 422 `VALIDATION_ERROR` with `route_to: null`. Its `details` points at the `finish` field, and its message reads, for example, "Straight has no Ombre. Use the Full finish." Hide or disable the Ombre option for these two styles on screen 29.
3. **Her finish is remembered.** `GET /v1/styles` returns `remembered_finish`. Use it to preselect the Full or Ombre toggle on 29. Tapping Straight or Micro doesn't erase a remembered Ombre choice.
4. **Look names add " · Ombre"** when the finish is Ombre, for example "Arch · Defined · Dark Brown · Ombre". The caption on 29 is in `copy.caption_29`, for example "ARCH · DARK BROWN · OMBRE".
5. **Saved looks have no tag.** The EVERYDAY / OCCASION tag is gone from 37 and from rename.
6. **Rename and delete looks (50):** `PATCH /v1/looks/{id}` takes `name` only, from 1 to 60 characters. `DELETE /v1/looks/{id}` removes the look and its photos.
7. **Renewal date:** `GET /v1/me/entitlements` returns `renewal_date`. It is `null` when the membership is not set to renew, for example after cancellation.
8. **Skin tone or face shape change (55a):** `PATCH /v1/me/brow-profile` with `skin_tone`, `undertone` or `face_shape` re-runs her recommendation and library on the scan she already has. The response contains `refreshed`, which holds `rescan_needed: false`, the new `recommendation` and library page 1. **Don't send her to a new scan.**
9. **Scan Held (22a):** `GET /v1/me/brow-profile` returns `has_scan`, `last_scan_date` and `screen_22a` (the wording). `GET /v1/home` returns `scan_held`, which holds `has_scan`, `last_scan_date` and `try_on_starts_at`. When `has_scan` is true, try-on starts at **22a**, not 22. On 22a, CHOOSE A STYLE goes to 29 and "Scan again" goes to 25.
10. **Screens 40 and 41 are retired** by the spec. The flow is now 39 → 22 / 22a → 25 → 27. The endpoint for 41 stays live, marked `retired: true`, until the client confirms in writing. Don't build new UI on it.
11. **Copy now comes from the API.** The wording for 22a, 30 (Structured), 32 (Refine), 42 and 43 now comes from the API and matches the client's change list. Show the strings exactly as they come back, and don't hardcode them from the drawings.

---

## 6. Values the app sends

| Field | Allowed values |
|---|---|
| `style` | arch, structured, feathered, bold, straight, micro, sharp, rounded |
| `intensity` | understated, defined, deliberate |
| `mode` | refine (REFINE MINE), reshape (RESHAPE MINE) |
| `finish` | full, ombre (ombre is not allowed with straight or micro) |
| `colour` | blonde, light_taupe, taupe, light_brown, medium_brown, chestnut, dark_brown, soft_black |
| `face_shape` | oval, round, square, heart, diamond, oblong, triangle |

`GET /v1/catalogue` returns all of these lists with their display names. `colour`, `intensity` and `mode` are optional on try-on calls. If you leave them out, the server fills them from her brow profile or her scan, and `resolved_from` in the response says where each value came from.

---

## 7. The screen map (01 to 147)

**Key:**
- **No backend:** the screen is static, native, or runs on the device (AR or drawing).
- **Retired:** removed by the client's spec. Don't build it.
- **Waiting:** blocked on an open client decision.

**About the 01 to 147 range:** the client's screen map (30 October 2026) and spec Draft 3.2 number screens only up to **94**. **Screens 95 to 147 do not exist in any document we have received**, so no endpoints exist for them. If the design files have screens in that range, send them to the backend team before building them. Screen 86 is also not in the map.

Unless a screen says otherwise, every call needs `Authorization: Bearer`.

### 01 to 13a · Start, accounts, guests

| Screen | Name | Endpoint(s) | Notes |
|---|---|---|---|
| 01 | Splash | No backend | |
| 02 | Before We Begin · Biometric Notice | `POST /v1/consent` (type `biometric_notice`, four boxes), `GET /v1/consent/status` | Send `X-Install-Id`. Comes before sign-up, so no token is needed. |
| 03 | Brand Manifesto | No backend | |
| 04 | New or Returning | No backend | |
| 05 | Create Account | `POST /v1/auth/register`, `POST /v1/auth/apple`, `POST /v1/auth/google` | Success → `next_screen` (14) |
| 06 | Create Account · Error State | Error from `POST /v1/auth/register`: 422 `VALIDATION_ERROR` with `details` | Stay on the screen and show the field errors |
| 07 | Account Already Exists | Error from `POST /v1/auth/register`: 409 `EMAIL_REGISTERED` → 07 | |
| 08 | Sign In | `POST /v1/auth/login`, `POST /v1/auth/apple`, `POST /v1/auth/google` | → `next_screen` 14, 20 or 21; or 11 for two-factor |
| 09 | Forgot Password | `POST /v1/auth/password/forgot` | |
| 10 | Reset Link Sent | `POST /v1/auth/password/forgot` (Send again), `POST /v1/auth/password/reset` (from the link) → 08 | The email link is `https://api.cbygroyals.com/reset-password?token=<token>`. With app links set up, it opens the app: read `token` and show "set new password". In a desktop browser it opens a small web form. |
| 11 | Two-Factor Auth | `POST /v1/auth/2fa/verify`, `POST /v1/auth/2fa/resend` | Resend has a 30-second wait. The code locks after 5 wrong tries. |
| 12 | Guest Home | `GET /v1/home` with `X-Guest: true` | No token |
| 12a | Guest Try-On Preview | `GET /v1/styles` | No token |
| 13 | Scan Gate | Shown when an error has `route_to: "13"` (`ACCOUNT_REQUIRED`); after sign-up, `POST /v1/onboarding/complete` with `carry_style` → 29 | |
| 13a | Account Gate (Looks and Profile) | Shown when an error has `route_to: "13a"` | |

### 14 to 21 · Onboarding and home

| Screen | Name | Endpoint(s) | Notes |
|---|---|---|---|
| 14 | Skin Tone + Goal | `GET /v1/onboarding/options`, `PUT /v1/onboarding/skin-tone-goal` | |
| 15 | Skin Tone Confirmation | `screen_15` in the response to the PUT above; CONFIRM → `POST /v1/onboarding/confirm-tone` | |
| 16 | Style Direction | `PUT /v1/onboarding/direction` | `direction: null` means skip → 18 |
| 17 | Direction Confirmation | `screen_17` in the response to the PUT above | |
| 18 | Onboarding Complete | `POST /v1/onboarding/complete` | |
| 19 | Home (New User) | `GET /v1/home` → `screen: "19"` | |
| 20 | Home (Returning User) | `GET /v1/home` → `screen: "20"` | |
| 21 | Personalised Returning Welcome | `GET /v1/home` → `screen: "21"` with her last look; RE-APPLY → `GET /v1/looks/{id}` | Home also returns `scan_held`, which decides whether try-on goes to 22 or 22a |

### 22 to 38 · Try-on

| Screen | Name | Endpoint(s) | Notes |
|---|---|---|---|
| 22 | Face Scan Intro | `GET /v1/styles` ("Browse styles directly" → 29) | Shown only when she has **no** scan |
| **22a** | **Scan Held** (new in Draft 3.2) | `GET /v1/me/brow-profile` → `has_scan`, `last_scan_date`, `screen_22a`; or `GET /v1/home` → `scan_held` | Shown instead of 22 whenever `has_scan` is true. CHOOSE A STYLE → 29; Scan again → 25. |
| 23 | Camera + Face Scan Consent | `GET /v1/consent/status` (shown only when `show_screen_23` is true); ALLOW CAMERA → `POST /v1/consent` (type `face_scan`) | |
| 24 | Camera Settings | No backend (iOS Settings) | |
| 25 | Scanning Active | `POST /v1/scans` (multipart `photo`, JPEG or PNG, at most 8 MB) | Errors go to 26 or 84 |
| 26 | Face Not In Frame | Shown when an error has `route_to: "26"` | |
| 27 | Scan Complete | Scan response `screen_27`, `before_images.face`, `recommendation`; also `GET /v1/scans/{id}` | `GET /v1/scans/{id}` and `GET /v1/scans/latest` now return `before_images` too, so 27 and 43 can be rebuilt after a restart |
| 28 | Post-Scan Discovery | Scan response `screen_28`; also `GET /v1/scans/{id}` | Brow-shape wording is waiting (client question 6) |
| 29 | Style Selector | `GET /v1/styles?scan_id=` (includes `remembered_finish`), `GET /v1/colours?scan_id=`, preview = `POST /v1/tryon/render` → `images.brow`, caption = `copy.caption_29`. With no scan: `GET /v1/library?style=&tone=` | **The Full / Ombre toggle is on this screen only.** Ombre is disabled for Straight and Micro. |
| 30 | Style Applied | `POST /v1/tryon/render` → `images.face`, `copy.style_applied`. The REFINE / RESHAPE toggle sends the same call with a different `mode`. | `finish` is required |
| 30a | Mode Introduction | `show_mode_intro_30a` in the render response; copy from `GET /v1/modes`; GOT IT → `POST /v1/me/flags` with `mode_intro_seen: true` | Shown once per account |
| 31 | Intensity Selector | `POST /v1/tryon/intensities` → `items[].images.eyes`; copy from `GET /v1/intensities` | `finish` is required |
| 32 | Intensity · Understated | `POST /v1/tryon/render` with `intensity: understated` → `copy.intensity_screen` | |
| 33 | Intensity · Defined | Same call, with `intensity: defined` | |
| 34 | Intensity · Deliberate | Same call, with `intensity: deliberate` | |
| 35a | Two Looks · Selection | Thumbnails from `POST /v1/tryon/intensities` | |
| 35b | Two Looks · Comparison | `POST /v1/tryon/compare` with `intensities: [a, b]` | `finish` is required |
| 36 | This Is Your Look | `POST /v1/tryon/render` → `copy.caption`, `copy.editorial_title`; when opened from a saved look: `GET /v1/looks/{id}`; TRACE THIS LOOK → 36a | |
| 36a | Before You Trace | `POST /v1/tracing/sessions` with `look_id`, or with `scan_id` and `style` → 73 | Members only (free accounts → 64) |
| 37 | Save Look | `POST /v1/looks` (name defaults to the caption) | `finish` is required. **No tag.** Members only (free accounts → 64). |
| 38 | Saved Confirmation | `screen_38` in the `POST /v1/looks` response | |

### 39 to 49c · Recommendation and the tracing guide

| Screen | Name | Endpoint(s) | Notes |
|---|---|---|---|
| 39 | Recommendation Intro | `GET /v1/me/brow-profile` → `has_scan` | Then → 22 or 22a → 25 → 27 |
| 40 | Reading Face | **Retired** (Draft 3.2) | Don't build |
| 41 | Your Result | **Retired** (Draft 3.2). `GET /v1/recommendations` stays live with `retired: true`. | Kept until the client confirms. Don't build new UI. |
| 42 | Why This Shape (View 1) | `GET /v1/recommendations/{style}` → `screen_42` | Client copy for all seven face shapes. `points` is `null` for styles that have no client copy. |
| 43 | Why This Shape (View 2) | `GET /v1/recommendations/{style}` → `screen_43` (headline, body, tagline, outline image on her photo) | |
| 44 | The Difference | `POST /v1/tryon/before-after` | `finish` is required |
| 45 | Tracing Guide Intro | No backend | |
| 46 | Draw | No backend (drawing on the device) | |
| 47 | Erase | No backend | |
| 48 | Reset | No backend | |
| 49 | Guide Complete | SHARE → `POST /v1/looks/{id}/share-image` once saved | |
| 49a | Save Guide | `POST /v1/guides` (multipart: `strokes` JSON, `name`, `image`) | Members only |
| 49b | Guide Saved | `screen_49b` in the `POST /v1/guides` response; `GET /v1/looks?tab=traced` | |
| 49c | Tracing Unavailable | No backend (shown when the device reports `tracking_failed`) | |

### 50 to 60 · My Looks and profile

| Screen | Name | Endpoint(s) | Notes |
|---|---|---|---|
| 50 | My Looks (Populated) | `GET /v1/looks?tab=all\|traced\|previewed`; rename → `PATCH /v1/looks/{id}` with `name`; delete → `DELETE /v1/looks/{id}` | Rename sends only `name` (1 to 60 characters) |
| 51 | My Looks (Empty) | `GET /v1/looks` → `screen: "51"`, `is_member`, `membership_line` → 64, `create_new_to` (29 or 22) | |
| 52 | Share This Look | `POST /v1/looks/{id}/share-image` | Save and share sheets are native |
| 53 | Profile Home | `GET /v1/me` (name, "With us since", `membership.badge`) | |
| 54 | My Account (Edit) | `GET /v1/me`, `PATCH /v1/me` (changing email needs `current_password`); `membership` holds plan, renewal and payment method | Change Password: `POST /v1/me/password` |
| 55 | Brow Profile | `GET /v1/me/brow-profile` → `screen: "55"` | |
| 55a | Brow Profile · Editable | `PATCH /v1/me/brow-profile` with any of `preferred_style`, `preferred_colour`, `face_shape`, `skin_tone`, `undertone` | A skin tone or face shape change returns `refreshed`. **No new scan.** |
| 55b | Delete my face scan · Step 1 | No backend | |
| 55c | Delete my face scan · Step 2 | `DELETE /v1/me/face-scan` with `remove_photographs` true or false | |
| 55d | Done · photographs removed | Response to the call above, `screen: "55d"` | |
| 55e | Done · photographs kept | Response to the call above, `screen: "55e"` | |
| 55f | Brow Profile · no scan | `GET /v1/me/brow-profile` → `screen: "55f"`, `has_scan: false` | |
| 56 | Preferences | `GET /v1/me/preferences`, `PATCH /v1/me/preferences` | |
| 57 | Language & Region | `PATCH /v1/me/preferences` with `language` (six languages) | **Waiting.** We were asked to make sure no endpoint maps to 57, but the spec retires 40 and 41, not 57. The endpoint stays until the client confirms. Don't remove this screen yet. |
| 58 | Help & Support | No backend (static menu) | |
| 59 | Contact Us | `POST /v1/support/messages` | |
| 60 | About ARCH | No backend | |

### 61 to 72 · Information pages and membership

| Screen | Name | Endpoint(s) | Notes |
|---|---|---|---|
| 61 | How ARCH Works | No backend | |
| 62 | Terms of Use | No backend | |
| 63 | Membership Standing | `GET /v1/me/entitlements` → `screen_63`, `renewal_date` | |
| 64 | Membership Gate (Unlock) | `GET /v1/me/entitlements` → `offer`; `GET /v1/config` (prices) | Every `MEMBERSHIP_REQUIRED` error routes here |
| 65 | Phone Number (Trial Start) | `POST /v1/me/phone`, `POST /v1/me/phone/verify` → 67 | |
| 66 | Payment Details (web) | `POST /v1/billing/web/checkout` returns **503** (no web provider chosen yet); Restore purchase → `POST /v1/billing/restore` | Waiting on the web payment provider |
| 67 | Free Trial Begun | After the native store sheet: `POST /v1/billing/apple/verify` with `signed_transaction`, or `POST /v1/billing/google/verify` with `purchase_token` → `screen_67` | Pass `app_account_token` to the store |
| 68 | Payment Failed | `GET /v1/me/entitlements` → `screen_68` (days of grace left) | |
| 69 | Update Payment | Not built (store users update in the store) | Waiting on the web payment provider |
| 70 | Cancellation Retention | No backend (native manage-subscriptions sheet; CONTACT US → 59) | |
| 71 | Cancel Membership | `GET /v1/me/entitlements` → `screen_71` | The store cancel itself is native |
| 72 | Membership Cancelled | `GET /v1/me/entitlements` → `screen_72` | |

### 73 to 77 · Live tracing (runs on the device)

| Screen | Name | Endpoint(s) | Notes |
|---|---|---|---|
| 73 | Setup Check | No backend (AR) | Session created on 36a |
| 73a | Setup light too low | No backend (AR) | |
| 74 / 74a | Position & Adjust (portrait / landscape) | No backend (AR) | Measurements from `GET /v1/styles` |
| 75-01 to 75-10 | SCULPT stages | `PATCH /v1/tracing/sessions/{id}` with `stage` | Stages only move forward |
| 75a | Interrupted | No backend | |
| 75b / 75c / 75e / 75f | Light low, tracking lost, hand occlusion, recovery | No backend (AR). Report failures with `PATCH /v1/tracing/sessions/{id}` and `event: tracking_failed` → 49c | |
| 75d | Exit Confirmation | LEAVE SESSION → `POST /v1/tracing/sessions/{id}/leave` → 36 | |
| 75g | Landscape tracing | No backend | |
| 76-01 to 76-10 | REFINE stages | `PATCH /v1/tracing/sessions/{id}` with `stage` | |
| 77 | Tracing · Completion | FINISH → `POST /v1/tracing/sessions/{id}/complete`; SAVE LOOK → `POST /v1/tracing/sessions/{id}/save` | |

### 78 to 94 · Deletion, notifications, errors, library

| Screen | Name | Endpoint(s) | Notes |
|---|---|---|---|
| 78 | Delete My Account | No backend (static); DELETE MY ACCOUNT → 79 | |
| 79 | Deletion Confirmation Modal | `POST /v1/me/delete` with `confirm: true` → 80 | |
| 80 | Deletion Underway | Response to the call above: purge date and `email_sent` | Hide the email line when `email_sent` is false. Signing in within 14 days cancels the deletion. |
| 81 | Sign Out Modal | `POST /v1/auth/logout` → 08 | |
| 82 | Notification Priming | YES, KEEP ME INFORMED → native dialog (83), then `POST /v1/devices` with `platform`, `push_token` and `permission` | |
| 83 | Native OS Permission Dialog | No backend (native) | |
| 84 | Scan Lighting Error | Shown when an error has `route_to: "84"` (`LOW_LIGHT`) | |
| 85 | Scan Slow | No backend (app timeout) | |
| 86 | Not in the screen map | None | |
| 87 | Between Connections | No backend (app offline state) | |
| 88 | Generic Error | Shown when an error has `route_to: "88"` (any 5xx) | |
| 89 | The Library · page 1 of 6 | `GET /v1/library?tone=&finish=&page=1`, `GET /v1/library/editorial` | Images are not hosted yet (see section 3). Library page 1 is also refreshed after a skin tone change on 55a. |
| 90 | The Library · page 2 of 6 | `GET /v1/library?page=2` | |
| 91 | The Library · page 3 of 6 | `GET /v1/library?page=3` | |
| 92 | The Library · page 4 of 6 | `GET /v1/library?page=4` | |
| 93 | The Library · page 5 of 6 | `GET /v1/library?page=5` | |
| 94 | The Library · page 6 of 6 | `GET /v1/library?page=6` | |

### 95 to 147

No screens in this range appear in the client's screen map or in spec Draft 3.2, so **no endpoints exist for them**. If the design files contain screens numbered 95 to 147, share them with the backend team before building them.

### Calls used on any screen

| Purpose | Endpoint |
|---|---|
| Refresh an expired access token | `POST /v1/auth/refresh` |
| Prices, refund wording, feature flags | `GET /v1/config` |
| All styles, colours, intensities, modes and face shapes with display names | `GET /v1/catalogue` |
| Her membership tier and renewal date | `GET /v1/me/entitlements` |

---

## 8. Open items that affect the frontend

| Item | Effect on the app |
|---|---|
| Screen 57 removal | Waiting for the client to confirm. Keep the screen. |
| Screen 41 | Retired, but the endpoint stays until the client's written confirmation |
| Screen 30 copy for the seven styles other than Structured | The current wording is provisional and will change on the server. No app change is needed. |
| Screen 28 brow-shape and symmetry wording | Waiting on the client (question 6). Comes from the API. |
| Screen 43 outlines | One face-outline image is drawn for every face shape. The client may ask for seven shape-specific outlines. |
| Library images (89 to 94, 29 with no scan) | Not hosted yet. Show placeholders. |
| Web payments (66, 69) | No provider chosen. Checkout returns 503. |
| Email and SMS | Two-factor codes and reset links are now emailed. If the email can’t be sent, two-factor sign-in answers 503 `EMAIL_NOT_SENT`. Phone codes (SMS, screen 65) are not delivered yet: no SMS provider. |
| HTTPS | The API is still plain HTTP on an IP address. iOS needs HTTPS on a domain. |
| Wording | User-facing strings use the typographic apostrophe (’). Show them as they come back. |
| Apple and Google sign-in, store purchases, push notifications | The code is built, but it has not been tested against the live stores. It needs the client's store credentials. |
