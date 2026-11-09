"""Write app/catalogue/data/library_manifest.csv from the naming convention.

The client's own manifest CSV has not arrived. Until it does, this builds the
expected one from Dev Notes 7 / build plan M5:

    v1/<finish>/<tone>/ARCH_<Tone>_<Style>_<Intensity>_{1254|512}.webp

252 images (144 Full = 6 tones x 8 styles x 3 intensities; 108 Ombre = 6 x 6
x 3, no Straight or Micro), each at 1254 and 512 px. Every row is marked
source=convention. When the client's manifest arrives, drop it in place of
this file (same columns) and the API serves it unchanged.

    python tools/build_library_manifest.py
"""
import csv
import os
import sys

os.environ.setdefault("ARCH_ENV", "dev")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import config  # noqa: E402
from app.catalogue import content as C  # noqa: E402

VERSION = "v1"
SIZES = (1254, 512)
COLUMNS = ["version", "finish", "tone", "style", "intensity", "size", "path", "source"]


def rows():
    for finish in C.FINISH_ORDER:
        for tone in C.SKIN_TONES:
            for style in C.STYLE_ORDER:
                if finish == "ombre" and not C.SUPPORTS_OMBRE[style]:
                    continue
                for intensity in C.INTENSITY_ORDER:
                    for size in SIZES:
                        name = (f"ARCH_{tone['name']}_{style.title()}_{intensity.title()}_{size}.webp")
                        yield {"version": VERSION, "finish": finish, "tone": tone["id"], "style": style,
                               "intensity": intensity, "size": size,
                               "path": f"{VERSION}/{finish}/{tone['id']}/{name}", "source": "convention"}


def main():
    out = config.LIBRARY_MANIFEST
    out.parent.mkdir(parents=True, exist_ok=True)
    data = list(rows())
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(data)
    images = len(data) // len(SIZES)
    print(f"wrote {out} ({images} images, {len(data)} rows)")


if __name__ == "__main__":
    main()
