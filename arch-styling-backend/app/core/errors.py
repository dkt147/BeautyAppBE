"""One error shape for every endpoint (F6):

    {"detail": "Readable message.", "code": "NO_FACE", "route_to": "26"}

`detail` and `code` are the shape the live Beauty Face API and the build plan
use. `route_to` is the screen number the app should open (see ERROR_ROUTES),
or null when the app should stay on the current screen (for example field
errors on 06). Any unexpected server error routes to 88, Generic Error (F7).
Some errors add fields, for example `details` (field errors) or
`retry_after` (seconds).
"""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.catalogue.content import ERROR_ROUTES

GENERIC_ERROR_SCREEN = "88"


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, extra: dict = None):
        self.code = code
        self.message = message
        self.status = status
        self.extra = extra or {}


def error_body(code: str, message: str, status: int, extra: dict = None) -> dict:
    route = ERROR_ROUTES.get(code)
    if route is None and status >= 500:
        route = GENERIC_ERROR_SCREEN
    body = {"detail": message, "code": code, "route_to": route}
    if extra:
        body.update(extra)
    return body


def install_error_handlers(app):
    @app.exception_handler(ApiError)
    async def _api(_: Request, exc: ApiError):
        headers = {"WWW-Authenticate": "Bearer"} if exc.status == 401 else None
        return JSONResponse(error_body(exc.code, exc.message, exc.status, exc.extra),
                            status_code=exc.status, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def _val(_: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in e["loc"] if p != "body"), "issue": e["msg"]}
                   for e in exc.errors()]
        return JSONResponse(error_body("VALIDATION_ERROR", "Some fields are missing or invalid.", 422,
                                       {"details": details}), status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(error_body(code, str(exc.detail), exc.status_code), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _any(_: Request, exc: Exception):
        return JSONResponse(error_body("SERVER_ERROR", "Something went wrong. Please try again in a moment.", 500),
                            status_code=500)
