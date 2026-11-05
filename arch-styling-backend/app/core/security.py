"""Passwords, tokens and one-time codes (M1).

* Passwords: bcrypt. Hashes from the existing auth service (passlib bcrypt,
  "$2b$...") verify here unchanged.
* Access token: HS256 JWT {"sub": user_id, "exp", "iat", "typ": "access"}.
  Tokens from ../app have no "typ" and are accepted as access tokens.
* Pending 2FA token: the same JWT with "typ": "2fa_pending", only valid on
  /v1/auth/2fa/*.
* Refresh token: random opaque string, stored as a SHA-256 hash, rotated on
  every refresh and revoked on sign out.
* One-time codes: 6 digits, stored as an HMAC, with expiry and attempt count.
"""
import hashlib
import hmac
import secrets
import time

import bcrypt
import jwt

from app import config

PASSWORD_MIN = 8
PASSWORD_MAX_BYTES = 72          # bcrypt limit


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("ascii"))
    except ValueError:
        return False


def create_token(user_id: str, typ: str = "access", minutes: int = None, **claims) -> str:
    now = int(time.time())
    minutes = minutes if minutes is not None else config.ACCESS_TOKEN_MINUTES
    payload = {"sub": user_id, "iat": now, "exp": now + minutes * 60, "typ": typ, **claims}
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Raises jwt.ExpiredSignatureError / jwt.InvalidTokenError."""
    payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM],
                         options={"require": ["sub", "exp"]})
    payload.setdefault("typ", "access")       # ../app tokens carry no typ
    return payload


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def new_code() -> str:
    return f"{secrets.randbelow(10**6):06d}"


def hash_code(code: str) -> str:
    return hmac.new(config.JWT_SECRET.encode(), code.encode(), hashlib.sha256).hexdigest()


def codes_match(code: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_code(code), hashed)
