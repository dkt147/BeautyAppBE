"""One error shape for every endpoint:

    {"error": {"code": "NO_FACE", "message": "...", "route_to": "26"}}

`route_to` is the screen number the app should open (see ERROR_ROUTES).
"""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.catalogue.content import ERROR_ROUTES


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, extra: dict = None):
        self.code = code
        self.message = message
        self.status = status
        self.extra = extra or {}


def _body(code, message, extra=None):
    err = {"code": code, "message": message, "route_to": ERROR_ROUTES.get(code)}
    if extra:
        err.update(extra)
    return {"error": err}


def install_error_handlers(app):
    @app.exception_handler(ApiError)
    async def _api(_: Request, exc: ApiError):
        return JSONResponse(_body(exc.code, exc.message, exc.extra), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def _val(_: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in e["loc"]), "issue": e["msg"]} for e in exc.errors()]
        return JSONResponse(_body("VALIDATION_ERROR", "Some fields are missing or invalid.",
                                  {"details": details}), status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return JSONResponse(_body(code, str(exc.detail)), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _any(_: Request, exc: Exception):
        return JSONResponse(_body("SERVER_ERROR", f"Unexpected error: {type(exc).__name__}"),
                            status_code=500)
