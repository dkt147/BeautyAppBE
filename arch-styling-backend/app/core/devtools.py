"""Dev-only routes and fields (M0, F9, QA report item 2).

`/v1/dev/*`, `/live` and `face_shape_override` work only on dev and staging
(ARCH_ENV=dev or staging). On production they answer 404 and are hidden from
Swagger. ARCH_ENV defaults to production, so a server started without it
never exposes them."""
from app import config
from app.core.errors import ApiError

DEV_TOOLS_ENVS = ("dev", "staging")
IS_DEV = config.ENV in DEV_TOOLS_ENVS


def dev_only():
    if config.ENV not in DEV_TOOLS_ENVS:
        raise ApiError("NOT_FOUND", "Not found.", 404)
