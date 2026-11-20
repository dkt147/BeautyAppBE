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

## Round 6 · 20 November 2026 · tracing guide line, Full / Ombre on 29

### Product questions for the client (answer in writing before the next build)

1. **Stroke detection can't be built with the current stack.** Stages 75-02 to 75-06 (and the Ombre shading feedback) need the app to see the pencil line she has actually drawn on her skin and compare it with the guide. That is specification question 5. Neither the server nor the app's current face tracking can see a drawn line. Doing it needs a partner AR / vision engine, or the client decides version one ships without stroke feedback. **Until then, nothing fakes it:** no drift line, no "back on the guide", no shading hints driven by guesses.
2. **The finger-drawn guide (45 to 49c).** On the call the client said nobody should trace brows with a finger. The specification keeps 45 to 49c as the fallback when live tracing can't run. **Backend position:** keep 45 to 49c only as the 49c fallback, opened only after `tracking_failed` (`PATCH /v1/tracing/sessions/{id}` with `event: tracking_failed` → 49c), and never offered as a main route. Ask the client to confirm in writing.

Checked against handover v6 and the client checklist of 19 November. The
app now draws the tracing guide as a thin gold line on her live face, and
screen 29 has the FULL / OMBRE toggle on her rendered brow. Every curl below
used a throwaway staging account, deleted afterwards.

### New items to fix

**25. `GET /v1/tracing/sessions/{id}/strokes` isn't deployed (blocker for
the real guide).** On 20 November it answers **404 `NOT_FOUND`** on 8011 for
a fresh member session (`trc_48a43f4369394487`), and neither port's
`/openapi.json` lists it. Until it's live the app draws the guide on the
device from the session's `style_measurements`, so a session still works,
but the shape is an approximation of the server's.

**Done when** the call returns the shape in handover 7.1 on both ports, and
Swagger lists it.

The app reads these fields. Please confirm each one, or tell me what
differs:
- `brows.right` and `brows.left`. Is `right` her right brow (anatomical),
  or the brow on the right of the scan photo? The app assumes anatomical.
- `outline[]` points have `s_ew`, `n_ew`, `u` (0 at the head, 1 at the
  tail) and `edge`, with values `"top"` / `"bottom"`. If `edge` or `u` is
  missing, the app splits the outline at the tail.
- The eye width behind `s_ew` / `n_ew` is the inner-to-outer eye corner
  distance, from the same landmarks as the corners. The app measures it
  live with ML Kit face contours, so a different definition would scale
  every guide.
- `centre_line[]` points have `u` and `opacity`. In Ombre, opacity rises
  from about 0.28 at the head to 1.0 at 60 % of the length. In Full, is it
  1.0 all along?

**26. REFINE's add zones.** Handover 7.1 says REFINE "shows only the add
zones", but `/strokes` describes the full shape. Today the app works the
zones out itself: it draws the parts of the outline that lie outside her
natural brow, as the camera sees it. If the server knows the add zones
better, from her scan, please mark them, for example `add_zone: true` on
outline points or a `zones` list per brow. The app will draw exactly those.

**27. Still open from round 5.**
- **16:** missing-body validation still returns `"field": ""` on 8011, not
  `"body"`.
- **24:** billing errors carry `route_to: "88"`. This is documented in
  handover v6 and can't be checked until #19 is set up.
- **5 / 23:** `https://api.cbygroyals.com` still doesn't answer.

### What changed in the app (no server change needed)

- **Google Play:** the app no longer acknowledges purchases. The server
  does it, as handover 6.2 says. This replaces round 5 item 22's
  description. Please make sure every verified Play purchase is
  acknowledged within 3 days, or Google refunds it.
- **Screen 29:** sends `POST /v1/tryon/render` with `views: ["brow"]` and
  her finish, and shows `images.brow` and `copy.caption_29`. With no
  intensity remembered and no style direction, it retries with `defined`
  after `INTENSITY_REQUIRED`.
- **Tracing:** sends `stage` 01, 07, 08 and 10, plus 09 and the 02 to 06
  stroke stages only when a stroke engine reports them. Stages stay
  forward-only.

### Round 6 checklist

- [ ] 25 `/strokes` deployed on 8010 and 8011, listed in Swagger, fields confirmed. **Code done and fields confirmed below (commits `e53cf7c`, `69d862f`). Not deployed: the server still runs older code.**
- [x] 26 Add zones marked for REFINE: the server marks them (`add_zone`, `zones[]`), commit `ab44e48`. Live after the deploy.
- [x] 16 Missing-body field is `"body"`: in the code since `d0d36d2`. 8011 still runs older code; live after the deploy.
- [x] 24 Billing errors carry `route_to: "88"`, and 422 stays `null`: in the code since `b7fb1f3`. Live after the deploy.
- [ ] 5 / 23 HTTPS on `api.cbygroyals.com`. **Infra action required** (below). Not done.

### Backend response to Round 6 · 20 November 2026

**Deployment: the real blocker.** Every item below is done in the code and proven on this machine. Ports 8010 and 8011 on `2.25.159.7` still run code from before 19 November, which is why `/strokes` is 404 and items 16 and 24 still show the old behaviour. The backend machine has no login to the server (SSH is refused), and nothing has been pushed to GitHub yet. Whoever holds the server login runs this, after the commits reach the server (push, or copy the repo):

```bash
cd <repo>/arch-styling-backend && git pull
.venv/bin/pip install -r requirements.txt
# restart both services the way they were started (systemd, or the run scripts):
#   production: ARCH_ENV=production on port 8010   staging: ./run_staging.sh on port 8011
curl -s http://2.25.159.7:8010/openapi.json | grep -c '/strokes'   # 1 when live
curl -s http://2.25.159.7:8011/openapi.json | grep -c '/strokes'   # 1 when live
```

**Proof on this machine.** A production server on 8010 and a staging server on 8011, built from this code with the scan test photo:

| Check | 8010 (production) | 8011 (staging) |
|---|---|---|
| `/openapi.json` lists `/v1/tracing/sessions/{session_id}/strokes` | yes | yes |
| `GET …/strokes`, member with a scan (Bold, REFINE, Ombre) | 200, `strokes[128]`, `brows.right` / `left` with `outline`, `centre_line`, `zones` | same |
| Free account | 403 `MEMBERSHIP_REQUIRED`, route 64 | same |
| Unknown session | 404 `NOT_FOUND` | same |
| Scan deleted | 409 `SCAN_REQUIRED`, route 22 | same |
| 16: `POST /v1/dev/grant-membership` with no body | 404 (dev tools are off on production) | 422, `details: [{"field": "body", "issue": "Field required"}]` |
| 24: `POST /v1/billing/apple/verify` | 503 `BILLING_NOT_CONFIGURED`, `route_to: "88"` | same |
| 24: the same call with `{}` | 422 `VALIDATION_ERROR`, `route_to: null` | same |

The curls (`B=http://2.25.159.7:8010` or `:8011` once deployed):

```bash
curl -s $B/v1/tracing/sessions/$TRC/strokes -H "Authorization: Bearer $TOK"
curl -s -X POST $B/v1/dev/grant-membership -H "Authorization: Bearer $TOK"            # 8011 only
curl -s $B/v1/billing/apple/verify -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' -d '{"signed_transaction":"x.y.z"}'
```

**25: the four field questions.**
- (a) Confirmed: `right` is her anatomical right brow. That's MediaPipe landmarks 133 (inner) and 33 (outer), the eye on the image left of a non-mirrored photo. If the app uploads a mirrored selfie, `right` is on the image right.
- (b) Confirmed: every `outline` point always has `x`, `y`, `u` (0 head, 1 tail), `edge` (`"top"` or `"bottom"`), `s_ew`, `n_ew` and `add_zone`. The outline is the top edge from head to tail, then the bottom edge from tail to head, 32 points each.
- (c) Confirmed: the eye width is the inner-to-outer eye corner distance, from the same scan landmarks that set the frame origin (133–33 right, 362–263 left). Commit `e53cf7c` removed a fallback that used a different definition. Measure it live the same way, corner to corner on ML Kit's eye contour.
- (d) Confirmed: in Full, `centre_line[].opacity` is 1.0 all along. In Ombre it rises from 0.28 at the head to 1.0 at 60 % of the length, and stays 1.0 to the tail.

**26: REFINE add zones. Decision (a): the server marks them.** Each `outline` point has `add_zone`. It is true where the guide lies more than 0.03 eye widths outside her natural brow, as read from her scan. Each brow has `zones[]`, the runs of those points: `{edge, u_from, u_to, kind}`, where `kind` is `fill` or `extension` (past her own head or tail). REFINE draws exactly those points. The device no longer works them out from the camera.

**16 and 24.** No new code was needed; both are in the code already (see the checklist above). They show the old behaviour on the live ports only because the server isn't updated.

### Infra action required: HTTPS on `api.cbygroyals.com` (items 5 and 23)

**Not done.** It needs DNS on Cloudflare and root on the server.

**Cloudflare DNS** (zone `cbygroyals.com`):

| Type | Name | Content | Proxy status | TTL |
|---|---|---|---|---|
| A | `api` | `2.25.159.7` | DNS only (grey cloud) | Auto |
| A | `staging-api` | `2.25.159.7` | DNS only (grey cloud) | Auto |

Keep "DNS only", so Let's Encrypt can reach nginx directly and the stores call the server itself. If the orange-cloud proxy is wanted later, set SSL/TLS mode to **Full (strict)** first.

**nginx**:

```nginx
# /etc/nginx/sites-available/arch-api   (nginx 1.24, already on the server)
# Step 1: only this port-80 block, until the certificates exist.
server {
    listen 80;
    listen [::]:80;
    server_name api.cbygroyals.com staging-api.cbygroyals.com;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://$host$request_uri; }
}

# Step 3: add these once certbot has issued both certificates.
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.cbygroyals.com;                       # production -> 8010
    ssl_certificate     /etc/letsencrypt/live/api.cbygroyals.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.cbygroyals.com/privkey.pem;
    client_max_body_size 10m;                             # scan uploads are up to 8 MB
    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;    # SET, not appended: rate limits read the first value
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 60s;                           # first render of a look can take a few seconds
    }
}
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name staging-api.cbygroyals.com;               # staging -> 8011
    ssl_certificate     /etc/letsencrypt/live/staging-api.cbygroyals.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging-api.cbygroyals.com/privkey.pem;
    client_max_body_size 10m;
    location / {
        proxy_pass http://127.0.0.1:8011;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 60s;
    }
}
```

**Steps on the server:**

```bash
sudo mkdir -p /var/www/certbot
sudo ln -s /etc/nginx/sites-available/arch-api /etc/nginx/sites-enabled/arch-api   # step 1 block only
sudo nginx -t && sudo systemctl reload nginx
sudo certbot certonly --webroot -w /var/www/certbot -d api.cbygroyals.com
sudo certbot certonly --webroot -w /var/www/certbot -d staging-api.cbygroyals.com
# step 3: add the two 443 blocks, then
sudo nginx -t && sudo systemctl reload nginx
curl -sI https://api.cbygroyals.com/health          # HTTP/2 200
```

**Then, in each server's environment:**
- production: `ARCH_PUBLIC_BASE_URL=https://api.cbygroyals.com`;
- staging: `ARCH_PUBLIC_BASE_URL=https://staging-api.cbygroyals.com`.

Restart both. Reset links and image URLs switch to HTTPS.

**Then item 23:**
- Apple: App Store Server Notifications V2, production and sandbox, set to `https://api.cbygroyals.com/v1/webhooks/apple`.
- Google: RTDN Pub/Sub push set to `https://api.cbygroyals.com/v1/webhooks/google`.

**Later:** once the app only uses HTTPS, bind uvicorn to `127.0.0.1`. Otherwise anyone calling `:8010` directly can set `X-Forwarded-For` and get round the rate limits.

---

## Round 5 · 18 November 2026 · in-app purchases are connected in the app

The app now buys memberships through the App Store (StoreKit 2) and Google
Play, and confirms every purchase on the server. The next TestFlight build
uses it. Purchases can't work until the server can verify them: on 18
November both ports answer **503 `BILLING_NOT_CONFIGURED`** to
`POST /v1/billing/apple/verify` and `/google/verify`.

### What the app sends

| Step | Call | Body |
|---|---|---|
| Account link | reads `app_account_token` from `GET /v1/me/entitlements` | passed to the store: StoreKit 2 `appAccountToken`, Play `obfuscatedAccountId` |
| Products | reads `offer.products.apple` / `.google` from the same response | `com.cbygroyals.arch.monthly` / `.annual`; `arch_monthly` / `arch_annual` |
| After the purchase sheet (iOS) | `POST /v1/billing/apple/verify` | `{"signed_transaction": "<Transaction.jwsRepresentation>"}` |
| After the purchase sheet (Android) | `POST /v1/billing/google/verify` | `{"purchase_token": "<Play purchase token>"}` |
| Restore purchase (64) | `POST /v1/billing/restore` | iOS `{"platform":"apple","signed_transactions":[JWS…]}` (from `Transaction.currentEntitlements`); Android `{"platform":"google","purchase_tokens":[…]}` |
| Afterwards | `GET /v1/me/entitlements` | membership must show at once |

The app finishes the store transaction only **after a 2xx from verify**
(iOS). On Android the app doesn't acknowledge; the server does (handover
6.2, round 6). If verify fails, the
store hands the purchase back on the next launch and the app sends it to
verify again, in the background, whenever she's signed in. So the same JWS or
token can arrive more than once.

### Items to fix

**19. Set up billing verification on both ports (blocker).**
- **Apple:** an In-App Purchase key from App Store Connect → Users and Access
  → Integrations → In-App Purchase. You need the `.p8` file, Key ID and
  Issuer ID, plus `ARCH_APPLE_BUNDLE_ID=com.cbyg.arch` and Apple's root
  certificates for the JWS chain check.
- **Google:** a service account with "View financial data" and "Manage
  orders and subscriptions" in the Play Console. Use package
  `com.cbygroyals.arch`.

**Done when** a real sandbox purchase from TestFlight returns 200 and
entitlements show `is_member: true`.

**20. Accept sandbox transactions on production.** TestFlight and App Review
buy with sandbox accounts, and their JWS carries
`"environment": "Sandbox"`. Production (:8010) must accept them. Call
the App Store Server API sandbox host for those, or verify the JWS locally,
or App Review can't unlock membership and will reject the app. Google test
purchases (license testers) likewise.

**21. Verify, and restore, must be idempotent.** The same transaction sent
twice returns 200 with the current membership, never an error. Check the
JWS `appAccountToken` against the signed-in account. When it belongs to
another ARCH account, return a clear 409, for example
`PURCHASE_OTHER_ACCOUNT` with `route_to: null` and a readable `detail`,
rather than moving the membership silently. Tell us which code you choose.

**22. Don't acknowledge Play purchases twice.** The app acknowledges by
finishing the purchase after verify. If the server also acknowledges, treat
"already acknowledged" as success.

**23. Store notifications (needs HTTPS, item 5).**
- **Apple:** set App Store Server Notifications V2, production and sandbox,
  to `https://api.cbygroyals.com/v1/webhooks/apple`.
- **Google:** point RTDN Pub/Sub push at `/v1/webhooks/google`.

These are what move renewals, billing problems (68), cancellations (72) and
refunds. Neither store will call a plain-HTTP IP address.

**24. `BILLING_NOT_CONFIGURED` and other 5xx should carry `route_to: "88"`**
as section 4.2 of the handover says. Today they return `null`. The app
shows `detail` either way, so this is low priority.

### Also still open from round 4

The round 4 changes aren't deployed yet (see "Recheck · 18 November"
below): the app-link file still lacks `FTQ9GSY7QA.com.cbyg.arch`, and
`https://api.cbygroyals.com` doesn't answer.

### Recheck · 19 November 2026

| # | Backend says | Live on 19 November |
|---|---|---|
| Round 4 app-link | Done | **8010:** lists `FTQ9GSY7QA.com.cbyg.arch` only. The `cbygroyals.arch` fallback that was promised is missing. That's fine for iOS, but please confirm it's intended. **8011:** still the old file (`cbygroyals.arch` only). Deploy staging too. |
| 24 | `route_to: "88"` on billing errors | **Not live.** `POST :8010/v1/billing/apple/verify` still returns 503 `BILLING_NOT_CONFIGURED` with `route_to: null`. |
| 20, 21, 22 | Done | Can't be checked until 19 is configured (needs a real store transaction). The 409 code is `ACCOUNT_MISMATCH`. The app shows its `detail`. |
| 19 | Waiting for the client's keys | 503 `BILLING_NOT_CONFIGURED` on both ports |
| 23 / 5 | Waiting for HTTPS | `api.cbygroyals.com` has **no DNS record**. The domain's DNS is on Cloudflare. The server already runs nginx 1.24 with ports 80 and 443 open (default 404). |

### Round 5 checklist

- [ ] 19 Apple and Google verification configured on 8010 and 8011
- [ ] 20 Sandbox / TestFlight purchases accepted on production
- [ ] 21 Verify and restore idempotent; other-account code chosen and shared
- [ ] 22 Play "already acknowledged" treated as success
- [ ] 23 Store notification URLs set (after HTTPS)
- [ ] 24 5xx billing errors carry `route_to: "88"`
- [ ] Round 4 deployed, and HTTPS on `api.cbygroyals.com`

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

### Recheck · 18 November 2026: the round 4 changes aren't live yet

The backend reported items 17 and 18 as done and sent handover v5. The live
servers still run the old code:

| Check | Expected (handover v5) | Live on 18 November |
|---|---|---|
| `GET :8010/.well-known/apple-app-site-association` | lists `FTQ9GSY7QA.com.cbyg.arch` and `…cbygroyals.arch` | only `FTQ9GSY7QA.com.cbygroyals.arch` (same on `:8011`) |
| `https://api.cbygroyals.com/...` | serves the same file | no answer (connection fails), so iOS can't fetch the app-link file at all |
| `POST :8011/v1/dev/grant-membership` with no body | `details: [{"field":"body", …}]` | `details: [{"field":"", …}]` |

Deploy the latest commit to both ports, and get HTTPS working on
`api.cbygroyals.com`, because iOS only reads the app-link file over HTTPS.
After that, the three checks above should match.

The product ids are received (iOS `com.cbygroyals.arch.monthly` / `.annual`,
Android `arch_monthly` / `arch_annual`). The app's purchase flow is still a
stand-in, and wiring the stores to `/v1/billing/*/verify` is mobile work.

### Round 4 checklist

- [ ] 17 App-link file lists `FTQ9GSY7QA.com.cbyg.arch` (keep the other id too)
- [ ] 18 iOS bundle-id settings on the server are `com.cbyg.arch`; Android unchanged
- [ ] Reply with the iOS in-app purchase product ids

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
- [ ] 14 Two-factor codes sent again on both ports
- [ ] 15 `intensity` on `POST /v1/looks`: fill it, or document `INTENSITY_REQUIRED`
- [ ] 16 Missing-body validation errors name the field; document the grant-membership body

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
