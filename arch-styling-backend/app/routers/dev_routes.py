"""Platform (M0) and test tools: health, config, style diagrams, scan debug
overlay and the browser live-test page."""
import cv2
import numpy as np
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse, HTMLResponse, Response

from app import config
from app.catalogue import content as C
from app.catalogue.measurements import load_measurements
from app.core.auth import User, current_user, require
from app.rendering.geometry import check_profile, style_profile
from app.services.scan_service import get_scan, load_scan_assets, recommendation_for

router = APIRouter()


@router.get("/health", tags=["Platform"], summary="Liveness + model check")
def health():
    return {"status": "ok", "version": config.API_VERSION, "model_found": config.MODEL_PATH.exists(),
            "measurement_version": load_measurements().version}


@router.get("/v1/config", tags=["Platform"], summary="Versions and enums the app needs at launch")
def app_config():
    M = load_measurements()
    return {"api_version": config.API_VERSION, "measurement_version": M.version,
            "styles": C.STYLE_ORDER, "intensities": C.INTENSITY_ORDER, "modes": list(C.MODES),
            "colours": [c["id"] for c in C.COLOURS], "face_shapes": list(M.face_shapes),
            "starting_mode": C.STARTING_MODE,
            "error_routes": C.ERROR_ROUTES}


def _draw_profile(prof, w=900, h=360, scale=380):
    img = np.full((h, w, 3), (10, 10, 10), np.uint8)
    ox, oy = 60, int(h * 0.62)
    cv2.line(img, (20, oy), (w - 20, oy), (60, 60, 60), 1)
    top = np.stack([ox + prof["x"] * scale, oy - prof["top"] * scale], 1)
    bot = np.stack([ox + prof["x"] * scale, oy - prof["bottom"] * scale], 1)
    poly = np.concatenate([top, bot[::-1]]).astype(np.int32)
    cv2.fillPoly(img, [poly], (28, 42, 66), lineType=cv2.LINE_AA)
    cv2.polylines(img, [poly], True, (76, 168, 201), 2, cv2.LINE_AA)
    pk = int(np.argmax(prof["top"]))
    cv2.circle(img, tuple(top[pk].astype(int)), 5, (76, 168, 201), -1, cv2.LINE_AA)
    cv2.circle(img, (ox, oy), 5, (240, 246, 250), -1, cv2.LINE_AA)
    return img


@router.get("/v1/styles/{style_id}/diagram.png", tags=["Catalogue 29"],
            summary="The style's measured shape drawn from the JSON (QA / thumbnail placeholder)")
def style_diagram(style_id: str, face_shape: str = Query(None)):
    M = load_measurements()
    if style_id not in M.styles or (face_shape and face_shape not in M.face_shapes):
        from app.core.errors import ApiError
        raise ApiError("NOT_FOUND", "Unknown style or face shape.", 404)
    st = M.style(style_id)
    prof = style_profile(st, M.peak_pct(style_id, face_shape), M.plateau(style_id, face_shape))
    img = _draw_profile(prof)
    chk = check_profile(st, prof)
    cv2.putText(img, f"{st.name}  peak {chk['peak_position_pct']}%  height {chk['peak_height_ew']} EW  "
                f"length {chk['length_ew']} EW", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv2.LINE_AA)
    ok, buf = cv2.imencode(".png", img)
    return Response(buf.tobytes(), media_type="image/png")


@router.get("/v1/dev/scan-debug/{scan_id}", tags=["Dev tools"],
            summary="Her photo with the traced natural brow (white) and the recommended style outline (gold)")
def scan_debug(scan_id: str, style: str = Query(None), user: User = Depends(current_user)):
    require(user, "scan")
    sc = get_scan(user, scan_id)
    image, lm, naturals = load_scan_assets(sc)
    M = load_measurements()
    style = style or sc["recommendation"]["recommended"]["style"]
    from app.rendering.brow_renderer import BrowRenderer
    R = BrowRenderer()
    prof = style_profile(M.style(style), M.peak_pct(style, sc["face_shape"]["id"]),
                         M.plateau(style, sc["face_shape"]["id"]))
    out = image.copy()
    for side, nb in naturals.items():
        for edge in (nb.upper, nb.lower):
            pts = nb.frame.to_image(edge[:, 0], edge[:, 1]).astype(np.int32)
            cv2.polylines(out, [pts], False, (255, 255, 255), 1, cv2.LINE_AA)
        geo = R._place(nb, prof, "reshape", 0)
        poly = np.concatenate([nb.frame.to_image(geo["s"], geo["top"]),
                               nb.frame.to_image(geo["s"][::-1], geo["bottom"][::-1])]).astype(np.int32)
        cv2.polylines(out, [poly], True, (76, 168, 201), 1, cv2.LINE_AA)
        e_in = nb.frame.o.astype(int)
        cv2.circle(out, tuple(e_in), 3, (0, 140, 255), -1)
    for i in (234, 454, 54, 284, 172, 397, 10, 152):
        cv2.circle(out, tuple(lm[i, :2].astype(int)), 3, (0, 200, 0), -1)
    ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return Response(buf.tobytes(), media_type="image/jpeg")


@router.get("/live", include_in_schema=False)
def live_page():
    return FileResponse(config.ROOT / "app" / "static" / "live_test.html")
