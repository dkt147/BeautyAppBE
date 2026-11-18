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

## Round 5 · 19 November 2026 · billing (backend notes)

Round 5 was sent as a message, not added to this file. Items 19 and 23 were
not in that message, so they are not covered here.

- [x] 20 Apple and Google verify accept Production and Sandbox; Sandbox is logged (`ARCH_STORE_ENVIRONMENTS`)
- [x] 21 Verify is idempotent (same `transactionId` / `purchase_token` returns the same subscription); another account's purchase is 409 `ACCOUNT_MISMATCH`
- [x] 22 Google purchases are acknowledged by the server; "already acknowledged" counts as success
- [x] 24 Billing errors return `route_to: "88"` (field errors stay `null`)

---

## Round 4 · 17 November 2026 · iOS bundle id is back to `com.cbyg.arch`

**What changed in the app.** The App Store Connect app for ARCH was set up
under the original bundle id `com.cbyg.arch` (team `FTQ9GSY7QA`, CbyG Royals
LLC), and builds have already been uploaded to it. Apple fixes an app's
bundle id after the first upload, so the iOS app goes back to
`com.cbyg.arch`. TestFlight build 1.0.0 (3) uses it.
**This replaces item 11 for iOS only.** Android keeps
`com.cbygroyals.arch`. Nothing changes in the API itself.

| Platform | Bundle / application id | App id used by Apple |
|---|---|---|
| iOS | `com.cbyg.arch` | `FTQ9GSY7QA.com.cbyg.arch` |
| Android | `com.cbygroyals.arch` (unchanged) | — |

### New items to fix

**17. Add the iOS app id to the app-link file (high: reset links open
Safari until it's done).**
`https://api.cbygroyals.com/.well-known/apple-app-site-association` lists
only `FTQ9GSY7QA.com.cbygroyals.arch`, so iOS won't open
`/reset-password?token=…` links in the app. Add the old id next to it, and
keep both so either build works:

```json
{"applinks":{"apps":[],"details":[{
  "appIDs":["FTQ9GSY7QA.com.cbyg.arch","FTQ9GSY7QA.com.cbygroyals.arch"],
  "components":[{"/":"/reset-password","?":{"token":"?*"},"comment":"Password reset link"}],
  "paths":["/reset-password"]
}]}}
```

If the legacy `appID` key (singular) is still in the file, set it to
`FTQ9GSY7QA.com.cbyg.arch`. Older iOS versions read only `paths` plus
`appID`. Keep serving the file as `application/json` over HTTPS with no
redirect.

**Done when** this lists `FTQ9GSY7QA.com.cbyg.arch`:

```bash
curl -s https://api.cbygroyals.com/.well-known/apple-app-site-association
```

Apple's CDN caches the file. To see what devices get, check
`https://app-site-association.cdn-apple.com/a/v1/api.cbygroyals.com`,
which can lag by up to a day.

**18. Any Apple bundle-id setting on the server must be `com.cbyg.arch`.**
Search the backend's configuration and environment for `cbygroyals.arch`,
and change the iOS values, for example `APPLE_BUNDLE_ID`, or `APP_BUNDLE_ID`
for App Store Server API or receipt checks. The App Store Server API
rejects a token whose `bid` doesn't match the app, and signed transactions
and App Store Server Notifications carry `bundleId: com.cbyg.arch`. Leave
Android/Google Play values on `com.cbygroyals.arch`.

In-app purchase product ids don't have to start with the bundle id, so the
existing `com.cbygroyals…` product ids can stay. They must be created in
App Store Connect under the `com.cbyg.arch` app. Tell the mobile team
the exact ids so the app requests the same ones.

### Round 4 checklist

- [x] 17 App-link file lists `FTQ9GSY7QA.com.cbyg.arch` (keep the other id too)
- [x] 18 iOS bundle-id settings on the server are `com.cbyg.arch`; Android unchanged
- [x] Reply with the iOS in-app purchase product ids

---

## Round 3 · 17 November 2026

Checked against production (`:8010`) and staging (`:8011`), backend commit
`c89f5df` (Spec Draft 3.2), from the app's end-to-end test on iPhone and
Android and with curl. Every curl below used a throwaway
`qa.<time>@example.com` account, deleted afterwards.

### Confirmed fixed or working

| # | Item | How it was checked |
|---|---|---|
| 10 | Email no longer holds up the reply | `POST /v1/auth/password/forgot` answers in 0.8 to 1.0 s for a registered email and 0.4 s for an unknown one, on both ports (was 25 s). |
| 13 | Staging server | `:8011` runs the dev tools. The full app test passes on it on Android, with every flow and nothing skipped. |
| — | Face-scan deletion (55c) | `DELETE /v1/me/face-scan` with `remove_photographs: true` keeps the looks, sets their `images` to `null`, and the old signed photo links answer 404. This is right; **no server change.** The app was keeping the old list and showing a black box; it now clears its image cache and reloads `GET /v1/looks` after the delete, and shows a placeholder for a look with no photo. |

### New items to fix

**14. Two-factor sign-in fails on both servers: 503 `EMAIL_NOT_SENT` (high).**
Signing in to the standing two-factor QA account returns 503 within about a
second, on production and staging alike. No one with two-factor on can sign
in, and the app shows the error screen (88), as the handover says it should.
It worked in round 2 (codes were sent).

```bash
for B in http://2.25.159.7:8010 http://2.25.159.7:8011; do
  curl -s -w ' HTTP %{http_code}\n' $B/v1/auth/login -H 'Content-Type: application/json' \
    -d '{"email":"claude.qa2.1794174340@example.com","password":"Passw0rd!99"}'
done
# {"detail":"We couldn’t send your code. Please try again in a minute.",
#  "code":"EMAIL_NOT_SENT","route_to":"88"} HTTP 503
```

The quick failure means the mail server refuses the send rather than timing
out. Check the server log for the SMTP error. Likely causes: expired or
changed SMTP credentials, or the provider rejecting the `@example.com`
recipient. If it is the recipient, the app is fine, but QA needs a two-factor
test account on a mailbox the provider accepts (tell the mobile team its
address). **Done when** the curl above returns `two_factor_required: true`
on both ports.

**15. `POST /v1/looks` requires `intensity`, but the handover says it is
optional (low, documentation).** Saving without `intensity` returns 422
`INTENSITY_REQUIRED` ("Choose an intensity: understated, defined or
deliberate."). Handover section 6 says `intensity` is optional on try-on
calls and is filled from her profile or scan, and `INTENSITY_REQUIRED` is
not in the error table (4.3). The app always sends `intensity` when saving,
so nothing breaks. Either fill it as documented, or add the code to section
4.3 and say in section 6 that saving needs it.

**16. Validation errors on a missing body name no field (low).**
`POST /v1/dev/grant-membership` with no body returns 422 with
`details: [{"field": "", "issue": "Field required"}]`. An empty `field`
can't be shown next to anything. Name the missing fields (`plan`, `status`)
or say "body". The handover's staging section also doesn't mention that this
call needs `{"plan": "monthly" | "annual", "status": "trial" | ...}`.

### Round 3 checklist

- [x] 10 Emails sent without holding up the reply
- [x] 13 Staging server (full Android test passes on it)
- [ ] 14 Two-factor codes sent again on both ports (code fixed 17 Nov: `@example.com` is skipped, not a 503. Still needs a new Gmail app password on the server: the current one is rejected by Google)
- [x] 15 `intensity` on `POST /v1/looks`: fill it, or document `INTENSITY_REQUIRED`
- [x] 16 Missing-body validation errors name the field; document the grant-membership body

---

## Round 2 · recheck on 10 November 2026

The fixes in API-STATUS section 8 were rechecked against the live server
from the app and with curl. Items 1 to 9 further down are the original
report, kept for reference.

### Confirmed fixed on the live server

| # | Item | How it was checked |
|---|---|---|
| 1 | 500s under concurrent reads | The reproduction loop in item 1, run for 10 rounds: 100 of 100 returned 200 (before: about 1 in 40 failed). |
| 2 | Dev endpoints | `POST /v1/dev/grant-membership` answers 404, so this server now runs as production. |
| 4 | Rate limits | A correct password is no longer refused after earlier sign-ins. Repeated full test runs were not blocked. |
| 7 | Reset link | `GET /reset-password` serves the web form. `/.well-known/apple-app-site-association` is served. The app now opens `https://api.cbygroyals.com/reset-password?token=…` (iOS Associated Domains, Android app link) and sends the token to `POST /v1/auth/password/reset`. |
| 8 | Typographic apostrophes | Error `detail` strings now use ’ (for example "That email and password don’t match."). |
| 6 | Email | Two-factor codes and reset emails are sent (`sent_to`, `channel: email` on sign-in). |

### New items to fix

**10. Sending email holds up the reply (high).**
`POST /v1/auth/password/forgot` takes **25 seconds** to answer for a
registered email, and 0.4 seconds for an unknown one. Two-factor sign-in
(`POST /v1/auth/login` on a two-factor account) takes about 2.6 seconds.
`POST /v1/support/messages` (59) and `POST /v1/me/delete` (79) were also
slow in the app's test runs, for the same reason.
The email is being sent over SMTP before the response is returned.
- She waits on a spinner for 25 seconds, and the app gives up at 30
  seconds, so a slightly slower mail server shows her the offline screen.
- The time difference tells anyone which emails have an account. The
  endpoint's equal reply for known and unknown emails is meant to hide that.

Reproduce:

```bash
B=http://2.25.159.7:8010
curl -s -o /dev/null -w '%{time_total}s\n' -X POST $B/v1/auth/password/forgot \
  -H 'Content-Type: application/json' -d '{"email":"<registered email>"}'
curl -s -o /dev/null -w '%{time_total}s\n' -X POST $B/v1/auth/password/forgot \
  -H 'Content-Type: application/json' -d '{"email":"nobody.123@example.com"}'
```

Fix: in `app/services/notify.py`, queue the email and return at once
(FastAPI `BackgroundTasks`, or a worker reading the outbox), and set an SMTP
timeout of about 10 seconds. Do the same for every email (two-factor,
deletion, contact, membership). **Done when** both calls above answer in
under a second. For two-factor, keep the 503 `EMAIL_NOT_SENT` for a send
that fails outright. Return it only when the send fails before the reply,
and otherwise let the resend button cover a lost email.

**11. Bundle id (iOS superseded by Round 4, item 17: iOS is `com.cbyg.arch`).** Daniyal chose
`com.cbygroyals.arch`, which matches the app-link file
(`FTQ9GSY7QA.com.cbygroyals.arch`) and the store product ids. The app now
uses it on iOS and Android. Use the same id for the Android fingerprint in
item 12.

**12. Android app-link file.** `/.well-known/assetlinks.json` answers 404
because `ARCH_ANDROID_CERT_SHA256` is not set. The mobile team will send
the SHA-256 fingerprint of the Play App Signing key once the app is in the
Play Console. Until then the Android link opens the browser form, which
still works.

**13. A staging server for QA.** Production now refuses the dev endpoints,
as it should. The app's debug build starts a membership through
`POST /v1/dev/grant-membership` because store billing is not installed yet.
Without a staging server, membership (65 to 72), saving looks (37, 38),
tracing (36a to 77), guides (49a) and My Looks with saved looks (50 to 52)
cannot be tested. Please run a staging copy (`ARCH_ENV=staging`) and send
its URL. The app points at it with `--dart-define=API_BASE=<url>`.

### Still open from round 1

- 5: HTTPS and the `api.cbygroyals.com` domain (infrastructure). Universal
  links and App Review need it.
- 6: SMS for phone codes (screen 65): no provider yet.
- 9: Library images (F20).

### Round 2 checklist

- [x] 10 Emails sent in the background; forgot-password answers in under a second for any email (confirmed 17 November)
- [x] 11 Bundle id `com.cbygroyals.arch` (app changed to match; nothing to do)
- [ ] 12 `ARCH_ANDROID_CERT_SHA256` set once the mobile team sends it
- [x] 13 Staging server running at `http://2.25.159.7:8011` (11 November 2026; full app test passes on it)
- [ ] 5 HTTPS on `api.cbygroyals.com`

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
