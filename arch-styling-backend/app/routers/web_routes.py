"""Pages and files served to browsers and phones, not the app (QA report item 7).

* GET /reset-password?token=...  The password reset link. On a phone with
  the app installed, the .well-known files below make the OS open the app at
  "set new password" with the token. Anywhere else this small form sets the
  new password with POST /v1/auth/password/reset.
* GET /.well-known/apple-app-site-association  (iOS universal links)
* GET /.well-known/assetlinks.json              (Android app links)
  Both are the files in app/static/well-known with the ids filled in from
  config. Each answers 404 until ARCH_APPLE_TEAM_ID / ARCH_ANDROID_CERT_SHA256 is set.
"""
import json

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from app import config
from app.core.errors import ApiError

router = APIRouter()
LINK_PATH = "/reset-password"
WELL_KNOWN = config.ROOT / "app" / "static" / "well-known"


@router.get(LINK_PATH, include_in_schema=False)
def reset_password_page():
    return FileResponse(config.ROOT / "app" / "static" / "reset_password.html", media_type="text/html")


def _well_known(name: str):
    return json.loads((WELL_KNOWN / name).read_text(encoding="utf-8"))


@router.get("/.well-known/apple-app-site-association", include_in_schema=False)
def apple_app_site_association():
    """app/static/well-known/apple-app-site-association, with the app id taken
    from ARCH_APPLE_TEAM_ID and ARCH_APPLE_BUNDLE_ID."""
    if not config.APPLE_TEAM_ID:
        raise ApiError("NOT_FOUND", "Not found.", 404)
    app_id = f"{config.APPLE_TEAM_ID}.{config.APPLE_BUNDLE_ID}"
    doc = _well_known("apple-app-site-association")
    for detail in doc["applinks"]["details"]:
        detail["appIDs"], detail["appID"] = [app_id], app_id
    return JSONResponse(doc)


@router.get("/.well-known/assetlinks.json", include_in_schema=False)
def android_asset_links():
    """app/static/well-known/assetlinks.json, with the package and signing
    fingerprints taken from ARCH_GOOGLE_PACKAGE_NAME and ARCH_ANDROID_CERT_SHA256."""
    if not config.ANDROID_CERT_SHA256:
        raise ApiError("NOT_FOUND", "Not found.", 404)
    doc = _well_known("assetlinks.json")
    for entry in doc:
        entry["target"]["package_name"] = config.GOOGLE_PACKAGE_NAME
        entry["target"]["sha256_cert_fingerprints"] = config.ANDROID_CERT_SHA256
    return JSONResponse(doc)
