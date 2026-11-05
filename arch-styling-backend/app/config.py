"""Runtime settings. Override any value with an environment variable."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

API_VERSION = "2.0.0"
DATA_DIR = Path(os.getenv("ARCH_DATA_DIR", ROOT / "data"))
MODEL_PATH = Path(os.getenv("ARCH_MODEL_PATH", ROOT / "models" / "face_landmarker.task"))
DB_PATH = DATA_DIR / "arch.db"
MEDIA_DIR = DATA_DIR / "media"

ENV = os.getenv("ARCH_ENV", "dev").lower()          # dev | staging | production

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
RESET_LINK_BASE = os.getenv("ARCH_RESET_LINK_BASE", "https://cbygroyals.com/arch/reset?token=")
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

# Public base for image URLs. Empty = relative URLs (/media/...).
PUBLIC_BASE_URL = os.getenv("ARCH_PUBLIC_BASE_URL", "").rstrip("/")

# Uploads larger than this are downscaled before landmarking.
MAX_IMAGE_SIDE = int(os.getenv("ARCH_MAX_IMAGE_SIDE", "1600"))
CONSENT_TEXT_VERSION = os.getenv("ARCH_CONSENT_VERSION", "23-face-scan-2026-10-16")

DATA_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def media_url(rel_path: str) -> str:
    rel = str(rel_path).replace("\\", "/").lstrip("/")
    return f"{PUBLIC_BASE_URL}/media/{rel}"
