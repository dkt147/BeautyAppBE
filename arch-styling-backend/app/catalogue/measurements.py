"""
Loads the client's ARCH brow measurement reference (JSON v1.3.1).

This file is the single source of truth for style geometry and the
face shape -> style table. Nothing in the code repeats these numbers:
when the client sends a new JSON, drop it into catalogue/data/ and point
MEASUREMENTS_FILE at it.

Units (from the JSON): every length is a ratio of EYE WIDTH (inner to outer
eye corner = 1.0), measured in the eye-line frame. Peak position is a % of
brow length from the Head.
"""

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DATA_DIR = Path(__file__).parent / "data"
MEASUREMENTS_FILE = DATA_DIR / "arch_brow_measurements_v1.3.1.json"


@dataclass(frozen=True)
class StyleSpec:
    id: str
    name: str
    length_ew: float
    peak_type: str                      # pointed | plateau | level
    peak_position_pct: Optional[float]  # None for Straight
    plateau_range_pct: Optional[Tuple[float, float]]
    peak_position_range_pct: Optional[Tuple[float, float]]
    peak_height_ew: float
    thickness_head_ew: float
    thickness_body_ew: float
    thickness_tail_ew: float
    tail_direction: str
    tail_offset_ew: float

    def peak_for_face(self, adjustment_pts: float) -> Optional[float]:
        """Peak position after the face shape adjustment (None for Straight)."""
        if self.peak_position_pct is None:
            return None
        return self.peak_position_pct + adjustment_pts

    def plateau_for_face(self, adjustment_pts: float) -> Optional[Tuple[float, float]]:
        if not self.plateau_range_pct:
            return None
        a, b = self.plateau_range_pct
        return (a + adjustment_pts, b + adjustment_pts)


@dataclass(frozen=True)
class FaceShapeSpec:
    id: str
    name: str
    recommended_style: str
    alternate_style: str
    peak_adjustment_pts: float
    recommended_peak_pct: Optional[float]
    alternate_peak_pct: Optional[float]
    peak_note: Optional[str]
    avoid_styles: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class Measurements:
    version: str
    date: str
    styles: Dict[str, StyleSpec]
    face_shapes: Dict[str, FaceShapeSpec]
    raw: dict

    def style(self, style_id: str) -> StyleSpec:
        return self.styles[style_id]

    def face_shape(self, face_shape_id: str) -> FaceShapeSpec:
        return self.face_shapes[face_shape_id]

    def peak_pct(self, style_id: str, face_shape_id: Optional[str]) -> Optional[float]:
        """Peak position for this style on this face shape.

        The JSON says the adjustment belongs to the face shape and applies to
        the recommended AND alternate style alike. We apply it to every style
        tried on that face, so a style keeps the same peak whether she reaches
        it through the recommendation or by browsing. (Assumption, see README.)
        """
        st = self.styles[style_id]
        adj = self.face_shapes[face_shape_id].peak_adjustment_pts if face_shape_id else 0.0
        return st.peak_for_face(adj)

    def plateau(self, style_id: str, face_shape_id: Optional[str]):
        st = self.styles[style_id]
        adj = self.face_shapes[face_shape_id].peak_adjustment_pts if face_shape_id else 0.0
        return st.plateau_for_face(adj)


def _tuple(v):
    return tuple(v) if v else None


@lru_cache(maxsize=1)
def load_measurements(path: str = str(MEASUREMENTS_FILE)) -> Measurements:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    styles = {}
    for s in raw["styles"]:
        styles[s["id"]] = StyleSpec(
            id=s["id"],
            name=s["name"],
            length_ew=float(s["length_ew"]),
            peak_type=s["peak_type"],
            peak_position_pct=s["peak_position_pct_from_head"],
            plateau_range_pct=_tuple(s.get("peak_plateau_range_pct")),
            peak_position_range_pct=_tuple(s.get("peak_position_range_pct")),
            peak_height_ew=float(s["peak_height_ew"]),
            thickness_head_ew=float(s["thickness_head_ew"]),
            thickness_body_ew=float(s["thickness_body_ew"]),
            thickness_tail_ew=float(s["thickness_tail_ew"]),
            tail_direction=s["tail_vs_head"]["direction"],
            tail_offset_ew=float(s["tail_vs_head"]["offset_ew"]),
        )
    shapes = {}
    for f in raw["face_shapes"]:
        shapes[f["id"]] = FaceShapeSpec(
            id=f["id"],
            name=f["name"],
            recommended_style=f["recommended_style"],
            alternate_style=f["alternate_style"],
            peak_adjustment_pts=float(f["peak_position_adjustment_pct_points"]),
            recommended_peak_pct=f["recommended_peak_position_pct"],
            alternate_peak_pct=f["alternate_peak_position_pct"],
            peak_note=f.get("peak_position_note"),
            avoid_styles=list(f.get("avoid_styles") or []),
        )
    return Measurements(raw["version"], raw["date"], styles, shapes, raw)
