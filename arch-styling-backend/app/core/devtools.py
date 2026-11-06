"""Dev-only routes and fields (M0, F9). Outside ARCH_ENV=dev they answer 404
and are hidden from Swagger."""
from app import config
from app.core.errors import ApiError

IS_DEV = config.ENV == "dev"


def dev_only():
    if config.ENV != "dev":
        raise ApiError("NOT_FOUND", "Not found.", 404)
