# ARCH API · fixes found by the mobile app's integration testing

**For:** the backend developer, to work through with Claude Code in the
`arch-styling-backend` repository.
**Tested against:** `http://2.25.159.7:8010` (API 2.0.0, measurement 1.3.1),
9 November 2026, from the Flutter app on branch `feature/api-integration`.
**How it was tested:** every endpoint the app uses was called with curl, and
the app's end-to-end test drove every screen against the live server with a
new account each run.

Each item has what happens, how to reproduce it, and what to change. Work
top to bottom: the first three block release or testing.

---

## 1. Intermittent 500 on ordinary reads under concurrent requests (critical)

**What happens.** When several requests arrive at once from one user, about
1 in 40 returns `500 SERVER_ERROR` (`route_to: "88"`). The app's home screen
loads about eight things at the same time, so users would see the error
screen (88) on an ordinary launch. Seen on `GET /v1/me`; it can hit any
route that touches the database.

**Reproduce.**

```bash
B=http://2.25.159.7:8010
T=<access_token of any account>
for round in 1 2 3 4; do
  for p in "/v1/looks?tab=all" /v1/me /v1/me/brow-profile /v1/me/entitlements \
           "/v1/looks?tab=all" /v1/me /v1/me/entitlements /v1/me/preferences \
           /v1/consent/status /v1/styles; do
    (curl -s -o /dev/null -w '%{http_code} '"$p"'\n' "$B$p" -H "Authorization: Bearer $T") &
  done; wait
done | sort | uniq -c        # expect only 200s; today some 500s appear
```

**Likely cause.** SQLite under concurrent access (`database is locked`), made
worse by reads that also write (for example, flags set as a side effect of
`GET /v1/me` or `GET /v1/home`). Check the server log for the 500's traceback
to confirm.

**Fix.**
- In `app/core/db.py`: enable WAL (`PRAGMA journal_mode=WAL`), set
  `PRAGMA busy_timeout=5000`, and use one connection per request with short
  transactions.
- Move writes out of GET handlers, or make them conditional, so reads stay
  read-only.
- Longer term this is the F14 Postgres move.
- **Done when:** the loop above returns only 200s over 10 rounds.

The app now retries a failed GET once, which hides most of this, but the
server must not return 500 for a plain read.

## 2. Dev-only endpoints are live on this server (critical, security)

**What happens.** The server runs with `ARCH_ENV=dev`. Any signed-in account
can call:
- `POST /v1/dev/grant-membership`, which gives itself a membership without
  paying.
- `POST /v1/dev/reset-test-user`, which deletes its own account (see 3).
- `POST /v1/dev/run-jobs`, `GET /v1/dev/scan-debug/{id}` and `GET /live`.

**Reproduce.** Sign in as a free account, then
`POST /v1/dev/grant-membership {"plan":"annual","status":"trial"}`. The
response is 200, and `GET /v1/me/entitlements` then says `is_member: true`.

**Fix.**
- Run any server real users can reach with `ARCH_ENV=production` (F9 already
  hides these routes outside dev).
- Keep a separate staging server with `ARCH_ENV=dev` for QA. The app's debug
  build uses `grant-membership` to test 65 to 72 while store billing is not
  installed, so staging must keep it.
- Tell the mobile team the two base URLs.

## 3. `POST /v1/dev/reset-test-user` deletes the account

**What happens.** Swagger calls it "Wipe the test user (fresh onboarding)".
It actually removes the account: afterwards the same email and password get
`INVALID_CREDENTIALS`, and the old tokens get `AUTH_REQUIRED`.

**Fix.** Choose one and make the code and the summary agree:
- (a) keep the user, the password and the sessions, and reset only onboarding,
  profile, scans, looks and flags, so QA can rerun 14 to 18; or
- (b) rename it to "delete test user".

(a) is what QA needs: see 4.

## 4. Sign-up rate limit blocks testing and shared networks

**What happens.** `POST /v1/auth/register` allows 10 attempts per hour per IP
address. Attempts that fail (409 `EMAIL_REGISTERED`, 422 validation) count
too. One test run uses two, so QA is blocked for up to an hour after a few
runs. In production, many users share one IP (offices, campus Wi-Fi, mobile
carriers' shared addresses), so legitimate sign-ups would be refused with
`RATE_LIMITED` and `retry_after` up to about 2000 seconds.

`POST /v1/auth/login` has the same shape of problem: about 10 attempts per 5
minutes, and successful sign-ins count. During testing a correct password
got `429 RATE_LIMITED` straight after a successful sign-in to the same
account. A household where two people sign in on a few devices could hit it.

**Fix (in `app/core/ratelimit.py`).**
- Count only successful registrations against the per-IP limit, and limit
  failed attempts per email instead.
- For login, count failed attempts only (per email and per IP). A correct
  password should never be refused for rate.
- Raise the per-IP limit, for example to 30 an hour.
- Make the limits configurable by environment variable, and turn them off on
  staging.

## 5. HTTPS and a domain name (required for the App Store)

The API is plain HTTP on a bare IP address. iOS App Transport Security
expects HTTPS, and exceptions cannot name an IP address, so the only way to
call this server from iOS is a blanket allow-all exception, which App Review
questions. Plain HTTP also sends tokens and face photos unencrypted.

**Fix.**
- Put the API behind a domain with TLS, for example `https://api.cbygroyals.com`,
  using nginx or Caddy in front of uvicorn.
- Make every media URL use the same domain.
- Send the URL to the mobile team. The app takes it at build time
  (`--dart-define=API_BASE=…`).

## 6. Emails and texts are not delivered (F18)

2FA codes, password-reset links and phone-verification codes go to the
`outbox` table and never leave the server. So:
- **11 (two-factor):** no one can sign in once two-factor is on.
- **09 → 10 (reset):** the email never arrives.
- **65 (phone):** the code never arrives.

**Fix.** Pick an email provider and an SMS provider, implement `_deliver` in
`app/services/notify.py`, and stop storing codes in the outbox.

## 7. The reset link must open the app

The app needs to know the reset email's link so it can open "set new
password" with the token. Please:
- Send a link of the form `https://<api-or-web-domain>/reset-password?token=<token>`.
- Host `apple-app-site-association` (iOS) and `assetlinks.json` (Android) on
  that domain for the app's bundle ids, so the link opens the app.
- On a desktop browser, the same URL should show a small web form that calls
  `POST /v1/auth/password/reset`.
- Tell the mobile team the exact path.

## 8. Response consistency

These don't break the app (it handles both forms), but they disagree with
the handover document:

| Where | Today | Expected (handover section 3) |
|---|---|---|
| Every media URL (`images.*`, `before_images.*`, `look.images.*`, `screen_22a.photo`, `screen_43.photo`) | Absolute: `http://2.25.159.7:8010/media/...` | Relative `/media/...`, or update the document to say absolute. Absolute is fine once 5 is done. |
| `styles[].diagram_url` | Relative `/v1/styles/arch/diagram.png` | Make it the same form as the media URLs |
| `GET /v1/scans/{id}` | Has no `before_images` | Return `before_images` as `POST /v1/scans` does. The app shows the 4:5 portrait on 27 and 43 after a restart. |
| Error `detail` strings, for example "That code isn't right.", "That email and password don't match." | Straight apostrophe `'` | The designs use the typographic apostrophe `’`. Use it in every user-facing string. |

## 9. Smaller items found while testing

- **Library images:** `GET /v1/library` returns `url_512` / `url_1254` as
  `null` (F20). The app shows the bundled style photo until they are set.
- **Session sign-out on password change:** `POST /v1/me/password` says it
  signs out other devices. The token used for the change keeps working,
  which is right. Please confirm that the other sessions' refresh tokens stop
  working.
---

## What the app does today (so the server can rely on it)

- Sends `Authorization: Bearer <access>` when signed in, nothing for
  guests, and `X-Install-Id` on every call (including 02, register and login).
- On a `401`, calls `POST /v1/auth/refresh` once, stores both new tokens and
  retries. If the refresh fails, the app signs out to 08.
- Branches on `code` and opens `route_to` (64, 13, 13a, 88). It shows
  `detail` on the screen and `details[].issue` next to each field.
- Sends `finish` on every render, intensities, compare, before-after, save
  and tracing call (`full`, or her `remembered_finish`).
- Reports tracing stages in order and waits for the last one before
  `…/complete`.
- Records 30a and 82 with `POST /v1/me/flags`.
- Not yet calling, because the mobile side is missing a piece:
  - `/v1/auth/apple`, `/v1/auth/google` and `/v1/billing/*/verify`: store and
    sign-in SDKs.
  - `/v1/devices`: push provider.
  - `/v1/me/phone/verify`: no design for the code entry.

## Checklist

- [ ] 1 No 500s under concurrent reads
- [ ] 2 Production server on `ARCH_ENV=production`; staging kept for QA
- [ ] 3 `reset-test-user` resets onboarding without deleting the account
- [ ] 4 Register and login rate limits count failures sensibly, configurable, off on staging
- [ ] 5 HTTPS domain for the API and media
- [ ] 6 Email and SMS delivery
- [ ] 7 Reset link format and app links
- [ ] 8 Consistent media URLs, `before_images` on `GET /v1/scans/{id}`, typographic apostrophes
- [ ] 9 Library images, session revocation confirmed
