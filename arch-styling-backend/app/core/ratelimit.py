"""Rate limits (F19, QA report item 4): sliding windows in one process.

Production moves this to Redis (M0) with the same calls.

* Every limit can be changed with environment variables:
  ARCH_RL_<NAME>_MAX and ARCH_RL_<NAME>_SECONDS, for example
  ARCH_RL_REGISTER_MAX=30. All limits are off with ARCH_RATE_LIMITS=false,
  and off by default on staging (ARCH_ENV=staging).
* Sign-up and sign-in count only what matters (QA item 4):
  - register: successful sign-ups per address (30 an hour), and failed
    attempts per email (10 an hour). A failed attempt never uses up the
    address's allowance, so offices and shared mobile addresses are not
    locked out.
  - login: failed attempts only, per email and per address. A correct
    password is never refused for rate.
* Other routes (2FA, forgot password, social, contact) count every call.
"""
import os
import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app import config
from app.core.errors import ApiError

_hits = defaultdict(deque)
_lock = threading.Lock()


def _setting(name: str, max_calls: int, per_seconds: int):
    key = name.upper().replace("-", "_")
    return (int(os.getenv(f"ARCH_RL_{key}_MAX", max_calls)),
            int(os.getenv(f"ARCH_RL_{key}_SECONDS", per_seconds)))


def client_address(request: Request) -> str:
    return (request.headers.get("x-forwarded-for") or "").split(",")[0].strip() or \
        (request.client.host if request.client else "unknown")


class Window:
    """One named sliding window. `check` refuses when full, `hit` records."""

    def __init__(self, name: str, max_calls: int, per_seconds: int):
        self.name = name
        self.max_calls, self.per_seconds = _setting(name, max_calls, per_seconds)

    def _queue(self, subject: str, now: float) -> deque:
        q = _hits[f"{self.name}:{subject}"]
        while q and q[0] <= now - self.per_seconds:
            q.popleft()
        return q

    def check(self, subject: str):
        if not config.RATE_LIMITS_ENABLED:
            return
        now = time.time()
        with _lock:
            q = self._queue(subject, now)
            if len(q) >= self.max_calls:
                wait = int(q[0] + self.per_seconds - now) + 1
                raise ApiError("RATE_LIMITED", "Too many tries. Please wait a moment and try again.", 429,
                               {"retry_after": wait, "route_to": None})

    def hit(self, subject: str):
        if not config.RATE_LIMITS_ENABLED:
            return
        now = time.time()
        with _lock:
            self._queue(subject, now).append(now)

    def clear(self, subject: str):
        with _lock:
            _hits.pop(f"{self.name}:{subject}", None)


def limit(name: str, max_calls: int, per_seconds: int):
    """Dependency that counts every call from one address."""
    window = Window(name, max_calls, per_seconds)

    def dep(request: Request):
        subject = client_address(request)
        window.check(subject)
        window.hit(subject)
    return dep


# Sign-up and sign-in (QA item 4).
REGISTER_PER_ADDRESS = Window("register", 30, 3600)              # successful sign-ups
REGISTER_FAILED_PER_EMAIL = Window("register_failed_email", 10, 3600)
LOGIN_FAILED_PER_EMAIL = Window("login_failed_email", 10, 900)
LOGIN_FAILED_PER_ADDRESS = Window("login_failed_address", 30, 900)


def guarded_register(request: Request, email: str, run):
    """Run a sign-up. Only a success counts against the address; a failure
    counts against the email."""
    address, email = client_address(request), email.strip().lower()
    REGISTER_PER_ADDRESS.check(address)
    REGISTER_FAILED_PER_EMAIL.check(email)
    try:
        result = run()
    except ApiError as e:
        if e.status < 500:
            REGISTER_FAILED_PER_EMAIL.hit(email)
        raise
    REGISTER_PER_ADDRESS.hit(address)
    return result


def guarded_login(request: Request, email: str, run):
    """Run a sign-in. Only failures count; a success clears the email's count."""
    address, email = client_address(request), email.strip().lower()
    LOGIN_FAILED_PER_EMAIL.check(email)
    LOGIN_FAILED_PER_ADDRESS.check(address)
    try:
        result = run()
    except ApiError as e:
        if e.status < 500:
            LOGIN_FAILED_PER_EMAIL.hit(email)
            LOGIN_FAILED_PER_ADDRESS.hit(address)
        raise
    LOGIN_FAILED_PER_EMAIL.clear(email)
    return result


def reset():
    with _lock:
        _hits.clear()
