import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("ARCH_ENV", "dev")
os.environ.setdefault("ARCH_DATA_DIR", tempfile.mkdtemp(prefix="arch_test_"))
# The suite signs up many accounts from one address; rate limits get their own test.
os.environ.setdefault("ARCH_RATE_LIMITS", "false")
# Never read the real .env (SMTP account, production settings) in tests.
os.environ["ARCH_ENV_FILE"] = ""

# Messages are captured here instead of sent (notify.transport is the only
# place that talks to SMTP). sent(to, template) reads them back.
from app.services import notify  # noqa: E402

SENT = []
REAL_TRANSPORT = notify.transport          # the SMTP one, for the SMTP test


def _capture(message):
    SENT.append(message)
    return "sent"


notify.transport = _capture


def sent(to, template=None):
    return [m for m in SENT if m["to"] == to and (template is None or m["template"] == template)]
