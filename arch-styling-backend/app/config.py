"""Runtime settings. Override any value with an environment variable."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env_file(path) -> None:
    """Read KEY=VALUE lines from .env into os.environ. A variable already set
    in the real environment wins. ARCH_ENV_FILE= (empty) skips the file; the
    tests do that so they never use the real SMTP account."""
    if not path or not Path(path).is_file():
        return
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.removeprefix("export ").strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_env_file(os.getenv("ARCH_ENV_FILE", str(ROOT / ".env")))

API_VERSION = "2.0.0"
DATA_DIR = Path(os.getenv("ARCH_DATA_DIR", ROOT / "data"))
MODEL_PATH = Path(os.getenv("ARCH_MODEL_PATH", ROOT / "models" / "face_landmarker.task"))
DB_PATH = DATA_DIR / "arch.db"
# How long a write waits for the SQLite lock before failing (QA item 1).
DB_BUSY_TIMEOUT_MS = int(os.getenv("ARCH_DB_BUSY_TIMEOUT_MS", "5000"))
MEDIA_DIR = DATA_DIR / "media"

# dev | staging | production. Defaults to production, so a server started
# without it never exposes the dev tools (QA report item 2). run.sh / run.bat
# and the tests set dev; the staging server sets staging.
ENV = os.getenv("ARCH_ENV", "production").lower()
if ENV not in ("dev", "staging", "production"):
    raise RuntimeError(f"ARCH_ENV must be dev, staging or production, not {ENV!r}.")

# ------------------------------------------------------------------ auth (M1)
# Requests carry "Authorization: Bearer <access token>". Tokens are HS256 JWTs
# with the user id in "sub", the same format the existing auth service
# (../app/auth) issues, so a token from either service is accepted when both
# share the secret. JWT_SECRET is the name ../app reads, so one value serves both.
JWT_SECRET = os.getenv("ARCH_JWT_SECRET") or os.getenv("JWT_SECRET") or ""
JWT_ALGORITHM = os.getenv("ARCH_JWT_ALGORITHM") or os.getenv("JWT_ALGORITHM") or "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ARCH_ACCESS_TOKEN_MINUTES", "15"))
REFRESH_TOKEN_DAYS = int(os.getenv("ARCH_REFRESH_TOKEN_DAYS", "30"))
PENDING_2FA_MINUTES = 10
OTP_MINUTES = int(os.getenv("ARCH_OTP_MINUTES", "10"))
OTP_MAX_ATTEMPTS = 5                                 # build plan: lock after 5 wrong tries
OTP_RESEND_SECONDS = int(os.getenv("ARCH_OTP_RESEND_SECONDS", "30"))   # screen 11 "Resend in 0:28"
RESET_LINK_MINUTES = int(os.getenv("ARCH_RESET_LINK_MINUTES", "60"))
# Public base for image URLs and links in emails. Empty = relative URLs (/media/...).
# The test server is http://2.25.159.7:8010 until the client's domain is live.
PUBLIC_BASE_URL = os.getenv("ARCH_PUBLIC_BASE_URL", "").rstrip("/")
# Reset email link (QA report item 7): <RESET_LINK_URL>?token=<token>. Defaults
# to <ARCH_PUBLIC_BASE_URL>/reset-password. The same URL opens the app
# (universal link / app link, see the .well-known files) or, in a desktop
# browser, the small form served at /reset-password.
RESET_LINK_URL = (os.getenv("ARCH_RESET_LINK_URL")
                  or f"{PUBLIC_BASE_URL or 'http://127.0.0.1:8000'}/reset-password").rstrip("?")
# App links for that URL. Empty = the .well-known file answers 404.
APPLE_TEAM_ID = os.getenv("ARCH_APPLE_TEAM_ID", "")
ANDROID_CERT_SHA256 = [f.strip() for f in os.getenv("ARCH_ANDROID_CERT_SHA256", "").split(",") if f.strip()]
APPLE_CLIENT_ID = os.getenv("ARCH_APPLE_CLIENT_ID", "")    # bundle id / services id
GOOGLE_CLIENT_IDS = [c for c in os.getenv("ARCH_GOOGLE_CLIENT_IDS", "").split(",") if c]

if not JWT_SECRET:
    if ENV != "dev":
        raise RuntimeError("Set ARCH_JWT_SECRET (or JWT_SECRET) outside dev.")
    JWT_SECRET = "dev-only-insecure-secret-change-me"

# Dev shortcut, off by default. When ARCH_DEV_AUTO_LOGIN=true, a request with
# no token is the test user, and "X-User-Id: <id>" acts as that user. Never
# enable outside dev. "X-Guest: true" (or no token) acts as a guest.
DEV_AUTO_LOGIN = ENV == "dev" and os.getenv("ARCH_DEV_AUTO_LOGIN", "false").lower() == "true"
TEST_USER_ID = os.getenv("ARCH_TEST_USER_ID", "test-user")
TEST_USER_NAME = os.getenv("ARCH_TEST_USER_NAME", "Mary")

# ----------------------------------------------------------- consent (M2)
# Policy version stamped on every consent record (Dev Notes 5.2).
POLICY_VERSION = os.getenv("ARCH_POLICY_VERSION", "2026-10-16")
# Dev Notes 1.1 rule 5: one server flag can remove screen 23 later.
SCREEN_23_ENABLED = os.getenv("ARCH_SCREEN_23_ENABLED", "true").lower() == "true"
# Open question 2: whether a new policy version shows 23 again. Off until decided.
RECONSENT_ON_POLICY_CHANGE = os.getenv("ARCH_RECONSENT_ON_POLICY_CHANGE", "false").lower() == "true"

# ------------------------------------------------------ privacy (M4, M12)
DELETION_GRACE_DAYS = int(os.getenv("ARCH_DELETION_GRACE_DAYS", "14"))
RETENTION_MONTHS = int(os.getenv("ARCH_RETENTION_MONTHS", "24"))
# Built but switched off until the client defines "last interaction" (Q17).
RETENTION_SWEEP_ENABLED = os.getenv("ARCH_RETENTION_SWEEP_ENABLED", "false").lower() == "true"
MAX_UPLOAD_MB = float(os.getenv("ARCH_MAX_UPLOAD_MB", "8"))

# ---------------------------------------------------------- library (M5)
# CDN in front of the public brow-library bucket. Empty = paths only.
LIBRARY_CDN_BASE = os.getenv("ARCH_LIBRARY_CDN_BASE", "").rstrip("/")
LIBRARY_MANIFEST = Path(os.getenv("ARCH_LIBRARY_MANIFEST",
                                  ROOT / "app" / "catalogue" / "data" / "library_manifest.csv"))

# ------------------------------------------------------------ media (F2)
# Face photos, renders and look photos are private. Every /media URL the API
# returns is signed and expires (build plan: 15 minutes).
MEDIA_URL_MINUTES = int(os.getenv("ARCH_MEDIA_URL_MINUTES", "15"))

# ----------------------------------------------------- membership (M10, M13)
# Prices, plan names, trial length and grace length come from configuration,
# never code (Dev Notes 5.1 rule 4, 6).
CURRENCY = os.getenv("ARCH_CURRENCY", "USD")
PRICE_MONTHLY = float(os.getenv("ARCH_PRICE_MONTHLY", "19.99"))
PRICE_ANNUAL = float(os.getenv("ARCH_PRICE_ANNUAL", "179.99"))
PLAN_NAMES = {"monthly": os.getenv("ARCH_PLAN_NAME_MONTHLY", "ARCH Membership · Monthly"),
              "annual": os.getenv("ARCH_PLAN_NAME_ANNUAL", "ARCH Membership · Annual")}
TRIAL_DAYS = int(os.getenv("ARCH_TRIAL_DAYS", "14"))
GRACE_DAYS = int(os.getenv("ARCH_GRACE_DAYS", "16"))          # screen 68 "continues for 16 days"
# Store product ids -> plan
APPLE_PRODUCTS = {os.getenv("ARCH_APPLE_PRODUCT_MONTHLY", "com.cbygroyals.arch.monthly"): "monthly",
                  os.getenv("ARCH_APPLE_PRODUCT_ANNUAL", "com.cbygroyals.arch.annual"): "annual"}
GOOGLE_PRODUCTS = {os.getenv("ARCH_GOOGLE_PRODUCT_MONTHLY", "arch_monthly"): "monthly",
                   os.getenv("ARCH_GOOGLE_PRODUCT_ANNUAL", "arch_annual"): "annual"}
APPLE_BUNDLE_ID = os.getenv("ARCH_APPLE_BUNDLE_ID", "com.cbygroyals.arch")
# Apple Root CA - G3 (PEM). App Store signed transactions and notifications
# are verified up to this root. Empty = Apple billing answers 503.
APPLE_ROOT_CA_PATH = os.getenv("ARCH_APPLE_ROOT_CA_PATH", "")
GOOGLE_PACKAGE_NAME = os.getenv("ARCH_GOOGLE_PACKAGE_NAME", "com.cbygroyals.arch")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("ARCH_GOOGLE_SERVICE_ACCOUNT_JSON", "")   # path to the key file
GOOGLE_PUBSUB_AUDIENCE = os.getenv("ARCH_GOOGLE_PUBSUB_AUDIENCE", "")
WEB_BILLING_PROVIDER = os.getenv("ARCH_WEB_BILLING_PROVIDER", "")      # open: provider for 66 / 69
WEB_WEBHOOK_SECRET = os.getenv("ARCH_WEB_WEBHOOK_SECRET", "")

# ------------------------------------------------------- email (M11, QA item 6)
# Codes, reset links and account emails go out over SMTP. No SMTP_HOST = email
# is not sent (logged only), and 2FA codes answer 503 EMAIL_NOT_SENT.
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM") or SMTP_USER or "office@cbygroyals.com"
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "ARCH")
SMTP_TLS = os.getenv("SMTP_TLS", "starttls").lower()          # starttls | ssl | none
SMTP_TIMEOUT = float(os.getenv("SMTP_TIMEOUT", "15"))

# ------------------------------------------------------- support (M13)
SUPPORT_EMAIL = os.getenv("ARCH_SUPPORT_EMAIL", "office@cbygroyals.com")
PRIVACY_POLICY_URL = os.getenv("ARCH_PRIVACY_POLICY_URL", "https://cbygroyals.com/privacy")

# ------------------------------------------------------ rate limits (F19)
# Per client and per key, in one process. Moves to Redis with M0.
# Off by default on staging so QA can sign up and sign in repeatedly (QA item 4).
# Each limit's size is set in ratelimit.py and overridden with
# ARCH_RL_<NAME>_MAX / ARCH_RL_<NAME>_SECONDS.
# ARCH_RATE_LIMITS_ENABLED is accepted as the same setting.
RATE_LIMITS_ENABLED = (os.getenv("ARCH_RATE_LIMITS") or os.getenv("ARCH_RATE_LIMITS_ENABLED")
                       or ("false" if ENV == "staging" else "true")).lower() == "true"

# Uploads larger than this are downscaled before landmarking.
MAX_IMAGE_SIDE = int(os.getenv("ARCH_MAX_IMAGE_SIDE", "1600"))
CONSENT_TEXT_VERSION = os.getenv("ARCH_CONSENT_VERSION", "23-face-scan-2026-10-16")

DATA_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def media_url(rel_path: str) -> str:
    rel = str(rel_path).replace("\\", "/").lstrip("/")
    return f"{PUBLIC_BASE_URL}/media/{rel}"
