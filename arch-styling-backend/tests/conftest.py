import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("ARCH_DATA_DIR", tempfile.mkdtemp(prefix="arch_test_"))
# The suite signs up many accounts from one address; rate limits get their own test.
os.environ.setdefault("ARCH_RATE_LIMITS", "false")
