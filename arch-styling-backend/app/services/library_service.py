"""Brow library (M5): screens 89 to 94, 12a and the no-scan preview on 29.

Image URLs come only from the manifest CSV (never from files in the repo).
A revised image goes under the next version prefix in the manifest.
"""
import csv
from functools import lru_cache

from app import config
from app.catalogue import content as C
from app.catalogue.measurements import load_measurements
from app.core.errors import ApiError

PER_PAGE = 4                      # 89 to 94 each show four cards
FIRST_LIBRARY_SCREEN = 89


@lru_cache(maxsize=1)
def manifest():
    """{(finish, tone, style, intensity): {"512": path, "1254": path, "version", "source"}}"""
    out = {}
    if not config.LIBRARY_MANIFEST.exists():
        return out, "missing"
    sources = set()
    with open(config.LIBRARY_MANIFEST, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (r["finish"], r["tone"], r["style"], r["intensity"])
            item = out.setdefault(key, {"version": r["version"], "source": r.get("source") or "client"})
            item[str(r["size"])] = r["path"]
            sources.add(item["source"])
    return out, ("convention" if sources == {"convention"} else "client")


def url_for(path):
    if not path:
        return None
    return f"{config.LIBRARY_CDN_BASE}/{path}" if config.LIBRARY_CDN_BASE else None


def image(finish, tone, style, intensity):
    items, _ = manifest()
    it = items.get((finish, tone, style, intensity))
    if not it:
        return None
    return {"path_1254": it.get("1254"), "path_512": it.get("512"),
            "url_1254": url_for(it.get("1254")), "url_512": url_for(it.get("512")), "version": it["version"]}


def resolve_tone(tone, profile):
    if tone:
        if tone not in C.SKIN_TONE_BY_ID:
            raise ApiError("VALIDATION_ERROR", f"Unknown tone '{tone}'.", 422)
        return tone, "request"
    if profile and profile.get("skin_tone"):
        return profile["skin_tone"], "brow_profile"
    raise ApiError("TONE_REQUIRED", "Choose a skin tone to see the library in it.", 422)


def library(tone, finish, style=None, page=None):
    if finish not in C.FINISHES:
        raise ApiError("VALIDATION_ERROR", f"Unknown finish '{finish}'. Use full or ombre.", 422)
    if style and style not in C.STYLE_ORDER:
        raise ApiError("VALIDATION_ERROR", f"Unknown style '{style}'.", 422)
    M = load_measurements()
    items = []
    for sid in C.STYLE_ORDER:
        if style and sid != style:
            continue
        if finish == "ombre" and not C.SUPPORTS_OMBRE[sid]:
            continue
        for it in C.INTENSITY_ORDER:
            items.append({
                "style": sid, "style_name": M.style(sid).name,
                "intensity": it, "intensity_name": C.INTENSITIES[it]["name"],
                "label": C.INTENSITIES[it]["name"].upper(),
                "editorial_title": C.EDITORIAL_TITLES[sid][it],
                "image": image(finish, tone, sid, it),
                "open": {"to": "36", "style": sid, "intensity": it, "finish": finish, "route_to_confirm": True},
            })
    pages = max(1, -(-len(items) // PER_PAGE))
    out = {"title": "Eight shapes. Three intensities.", "label": "THE LIBRARY", "tone": tone, "finish": finish,
           "total": len(items), "pages": pages, "per_page": PER_PAGE}
    if page is not None:
        if not 1 <= page <= pages:
            raise ApiError("VALIDATION_ERROR", f"Page must be 1 to {pages}.", 422)
        out.update(page=page, screen=str(FIRST_LIBRARY_SCREEN + page - 1) if not style else None,
                   items=items[(page - 1) * PER_PAGE: page * PER_PAGE])
    else:
        out["items"] = items
    _, source = manifest()
    out["manifest_source"] = source
    out["cdn_configured"] = bool(config.LIBRARY_CDN_BASE)
    return out


def editorial():
    M = load_measurements()
    return {"display_status": "undecided",       # question 16: are the 24 titles shown anywhere?
            "titles": [{"style": s, "style_name": M.style(s).name, "intensity": i,
                        "intensity_name": C.INTENSITIES[i]["name"], "title": C.EDITORIAL_TITLES[s][i]}
                       for s in C.STYLE_ORDER for i in C.INTENSITY_ORDER]}


def catalogue():
    M = load_measurements()
    return {
        "measurement_version": M.version,
        "styles": [{"id": s, "name": M.style(s).name, "reading": C.STYLE_READINGS[s],
                    "supports_ombre": C.SUPPORTS_OMBRE[s]} for s in C.STYLE_ORDER],
        "intensities": [{"id": k, "name": C.INTENSITIES[k]["name"]} for k in C.INTENSITY_ORDER],
        "tones": C.SKIN_TONES, "undertones": C.UNDERTONES,
        "colours": C.COLOURS,
        "colour_by_tone": None,   # Dev Notes 7 per-tone hex (deeper for Deep / Rich): values not received
        "finishes": [C.FINISHES[f] for f in C.FINISH_ORDER], "base_finish": C.BASE_FINISH,
        "modes": C.MODES, "starting_mode": C.STARTING_MODE,
    }
