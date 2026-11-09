"""ARCH styling backend (screens 12 to 38).

Run:  uvicorn app.main:app --reload --port 8000
Docs: http://127.0.0.1:8000/docs     Live test: http://127.0.0.1:8000/live
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import config
from app.core.errors import install_error_handlers
from app.core.media import SignMediaMiddleware
from app.core.media import router as media_router
from app.routers import (account_routes, auth_routes, dev_routes, library_routes, privacy_routes, profile_routes,
                         styling_routes, tracing_routes, web_routes)

app = FastAPI(
    title="ARCH Styling API",
    version=config.API_VERSION,
    description=(
        "Backend for the ARCH styling journey, screens 12 to 38 of the Visual Screen Map.\n\n"
        "**Sign in first.** Call `POST /v1/auth/register` (or `/v1/auth/login`), copy `access_token`, "
        "click **Authorize** and paste it. With no token you are a guest. Errors come back as "
        "`{\"detail\", \"code\", \"route_to\"}`, where `route_to` is the screen to open.\n\n"
        "Order to test: register (05) → consent (23) → scan (25) → styles (29) → try-on render (30) "
        "→ intensities (31) → compare (35b) → save look (37/38)."
    ),
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
install_error_handlers(app)
# /media is private (F2): signed, expiring URLs only. See app/core/media.py.
app.add_middleware(SignMediaMiddleware)
app.mount("/static", StaticFiles(directory=str(config.ROOT / "app" / "static")), name="static")

app.include_router(media_router)
app.include_router(dev_routes.router)
app.include_router(auth_routes.router)
app.include_router(profile_routes.router)
app.include_router(styling_routes.router)
app.include_router(library_routes.router)
app.include_router(privacy_routes.router)
app.include_router(tracing_routes.router)
app.include_router(account_routes.router)
app.include_router(web_routes.router)
