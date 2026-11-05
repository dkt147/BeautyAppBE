"""Runtime settings. Override any value with an environment variable."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

API_VERSION = "2.0.0"
DATA_DIR = Path(os.getenv("ARCH_DATA_DIR", ROOT / "data"))
MODEL_PATH = Path(os.getenv("ARCH_MODEL_PATH", ROOT / "models" / "face_landmarker.task"))
DB_PATH = DATA_DIR / "arch.db"
MEDIA_DIR = DATA_DIR / "media"

# Login is not built yet (module M1). Until it is, every request without an
# X-User-Id header is the test user. Send "X-Guest: true" to act as a guest.
DEV_AUTO_LOGIN = os.getenv("ARCH_DEV_AUTO_LOGIN", "true").lower() == "true"
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
