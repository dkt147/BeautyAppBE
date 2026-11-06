"""Private media (F2).

Scan photos, renders, look photographs and guides are biometric or personal
data. They are never served from a public folder. Every /media URL the API
returns carries an HMAC signature and an expiry (ARCH_MEDIA_URL_MINUTES,
build plan: 15 minutes):

    /media/scans/scan_x/photo.jpg?exp=1793920000&sig=3f2a...

Stored documents keep the plain path. URLs are signed on the way out, in
`SignMediaMiddleware`, so a stored URL never goes stale. `GET /media/{path}`
serves a file only when the signature matches and has not expired.
"""
import hashlib
import hmac
import json
import time
from urllib.parse import quote

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app import config
from app.core.errors import ApiError

router = APIRouter()


def _prefix():
    return f"{config.PUBLIC_BASE_URL}/media/"


def _sig(path: str, exp: int) -> str:
    msg = f"media:{path}:{exp}".encode()
    return hmac.new(config.JWT_SECRET.encode(), msg, hashlib.sha256).hexdigest()[:32]


def sign_url(url: str, now: float = None) -> str:
    pre = _prefix()
    if not isinstance(url, str) or not url.startswith(pre) or "?sig=" in url or "&sig=" in url:
        return url
    path = url[len(pre):]
    exp = int((now or time.time()) + config.MEDIA_URL_MINUTES * 60)
    return f"{pre}{quote(path)}?exp={exp}&sig={_sig(path, exp)}"


def sign_all(obj):
    if isinstance(obj, str):
        return sign_url(obj)
    if isinstance(obj, list):
        return [sign_all(v) for v in obj]
    if isinstance(obj, dict):
        return {k: sign_all(v) for k, v in obj.items()}
    return obj


def path_of(url: str) -> str:
    """Media path from a stored or signed URL (no query string)."""
    return url.split("/media/", 1)[1].split("?", 1)[0]


class SignMediaMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if not (response.headers.get("content-type") or "").startswith("application/json"):
            return response
        body = b"".join([chunk async for chunk in response.body_iterator])
        if b"/media/" not in body:
            return Response(body, status_code=response.status_code, headers=dict(response.headers),
                            media_type="application/json")
        data = sign_all(json.loads(body))
        out = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()
        headers = {k: v for k, v in response.headers.items() if k.lower() != "content-length"}
        return Response(out, status_code=response.status_code, headers=headers, media_type="application/json")


@router.get("/media/{path:path}", include_in_schema=False)
def media(path: str, exp: int = Query(None), sig: str = Query(None)):
    if exp is None or not sig:
        raise ApiError("MEDIA_LINK_INVALID", "This image link is not valid.", 403)
    if exp < time.time():
        raise ApiError("MEDIA_LINK_EXPIRED", "This image link has expired. Load the screen again.", 403)
    if not hmac.compare_digest(sig, _sig(path, exp)):
        raise ApiError("MEDIA_LINK_INVALID", "This image link is not valid.", 403)
    root = config.MEDIA_DIR.resolve()
    target = (root / path).resolve()
    if root not in target.parents or not target.is_file():
        raise ApiError("NOT_FOUND", "Not found.", 404)
    return FileResponse(target, headers={"Cache-Control": "private, max-age=600"})
