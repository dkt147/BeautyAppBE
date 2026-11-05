"""
Locked catalogue content and screen copy for screens 12 to 38.

Where the copy is quoted from the client package it says so (source=...).
Where the client has not supplied a value yet, the entry is marked
`provisional: True` so the app and the client can see what still needs a
decision. Change values here only; routers never hard-code copy.
"""

# ---------------------------------------------------------------- styles
# Grid order and readings: Developer Handoff, "Style library (eight styles,
# locked)". Ids match the Measurement JSON v1.3.1.
STYLE_ORDER = ["arch", "structured", "feathered", "bold",
               "straight", "micro", "sharp", "rounded"]

STYLE_READINGS = {
    "arch": "Pronounced lift",
    "structured": "Clean architectural line",
    "feathered": "Visible hair separation",
    "bold": "Fuller body",
    "straight": "Flat, level line",
    "micro": "Finer hair",
    "sharp": "Defined angle",
    "rounded": "Soft curve",
}

# Screen 30 (Style Applied) copy. Only Structured is drawn in the screen map;
# the other seven are drafted in the same voice and marked provisional.
STYLE_APPLIED_COPY = {
    "structured": {
        "headline": "Notice how structure frames your eyes.",
        "body": "A structured line gives the upper face clear shape and quiet precision.",
        "provisional": False,
    },
    "arch": {
        "headline": "Notice what the arch does to your eyes.",
        "body": "A clear, elegant lift that frames the upper face with precision.",
        "provisional": True,
    },
    "feathered": {
        "headline": "Notice how softly it settles.",
        "body": "Brushed-up texture and visible hairs keep the shape light and natural.",
        "provisional": True,
    },
    "bold": {
        "headline": "Notice the presence it gives you.",
        "body": "A fuller body that holds its shape and makes the brow the point of focus.",
        "provisional": True,
    },
    "straight": {
        "headline": "Notice how the line carries across.",
        "body": "A level brow draws the eye across the face rather than up.",
        "provisional": True,
    },
    "micro": {
        "headline": "Notice how little it takes.",
        "body": "Fine, precise hairs close to the skin. Modern, clean and understated.",
        "provisional": True,
    },
    "sharp": {
        "headline": "Notice the lift at the peak.",
        "body": "A defined angle with a quick rise and fall gives the face a clear point of focus.",
        "provisional": True,
    },
    "rounded": {
        "headline": "Notice how the curve softens.",
        "body": "Curved from head to tail with no hard angle. Gentle, and quietly full.",
        "provisional": True,
    },
}

# Editorial titles (24, style x intensity): Developer Handoff, locked.
EDITORIAL_TITLES = {
    "arch":       {"understated": "A Suggestion of Lift", "defined": "The Shape That Was Always There", "deliberate": "The Highest Point"},
    "structured": {"understated": "Quietly Composed", "defined": "The One She Keeps Returning To", "deliberate": "Every Line Decided"},
    "feathered":  {"understated": "As If You Woke Up With It", "defined": "Effortless, On Purpose", "deliberate": "Full, and Still Soft"},
    "bold":       {"understated": "Strength, Held Back", "defined": "She Means It", "deliberate": "Nothing Held Back"},
    "straight":   {"understated": "Level, and Light", "defined": "The Modern Line", "deliberate": "Horizon"},
    "micro":      {"understated": "The Lightest Touch", "defined": "Fine, and Exact", "deliberate": "Every Hair Accounted For"},
    "sharp":      {"understated": "A Hint of an Edge", "defined": "Cut Clean", "deliberate": "Drawn With a Steady Hand"},
    "rounded":    {"understated": "A Gentle Turn", "defined": "Warmth, Given Shape", "deliberate": "The Full Curve"},
}

# ------------------------------------------------------------ intensities
# Names locked (Understated, Defined, Deliberate). Opacity bands from the
# master reference B3/B4 (30-40 / 60-70 / 90-100 %, default mid-point).
# Intensity changes fill weight and colour density ONLY, never shape.
INTENSITY_ORDER = ["understated", "defined", "deliberate"]

INTENSITIES = {
    "understated": {
        "name": "Understated",
        "opacity": 0.35,
        "selector_lines": ["A whisper. Barely there.", "Effortless. Natural confidence."],
        "tagline": "Present, not pronounced.",
        "body": {
            "reshape": "The style's shape, softly placed on your brow.",
            "refine": "The brow your face was wearing all along, simply made clearer.",
        },
    },
    "defined": {
        "name": "Defined",
        "opacity": 0.65,
        "selector_lines": ["Polished and present.", "Your everyday at its best."],
        "tagline": "Polished. Present. Effortlessly exact.",
        "body": {
            "reshape": "A brow that has clearly been thought about. Not overdone.",
            "refine": "Your own shape, filled and defined with a groomed, polished finish.",
        },
    },
    "deliberate": {
        "name": "Deliberate",
        "opacity": 0.95,
        "selector_lines": ["Precise. Intentional.", "A brow with a point of view."],
        "tagline": "This is a brow with a point of view.",
        "body": {
            "reshape": "Strong. Assured. Makes a statement without asking for permission.",
            "refine": "Your own shape, built up and sharply defined. Unmistakably groomed.",
        },
    },
}

# --------------------------------------------------------------- modes
# Screen 30a copy is quoted from the screen map.
MODES = {
    "refine": {
        "label": "REFINE MINE",
        "line": "Your own shape, filled and groomed toward the style.",
        # Working assumption (not confirmed by the client): Refine mine keeps
        # her own brow and fills / grooms it toward the style.
        "assumed_behaviour": "Keeps her own brow, fills sparse areas and grooms it toward the style shape.",
    },
    "reshape": {
        "label": "RESHAPE MINE",
        "line": "The style's shape, placed on your brow.",
        "assumed_behaviour": "Softly conceals her own brow and renders the style's exact shape on it.",
    },
}
MODE_INTRO = {
    "title": "TWO WAYS TO SEE IT",
    "items": [MODES["refine"], MODES["reshape"]],
    "cta": "GOT IT",
}
DEFAULT_MODE = "reshape"   # the screen map draws RESHAPE MINE as selected

# ---------------------------------------------------------------- colours
# Screen 29 shows eight swatches, light to dark, with Dark Brown seventh.
# Hex values are sampled from the screen map; names other than Dark Brown
# are PROVISIONAL until the client confirms the palette.
COLOURS = [
    {"id": "blonde",       "name": "Blonde",       "hex": "#D6B081", "provisional": True},
    {"id": "light_taupe",  "name": "Light Taupe",  "hex": "#BD9970", "provisional": True},
    {"id": "taupe",        "name": "Taupe",        "hex": "#A6845F", "provisional": True},
    {"id": "light_brown",  "name": "Light Brown",  "hex": "#8C6C4E", "provisional": True},
    {"id": "medium_brown", "name": "Medium Brown", "hex": "#72573C", "provisional": True},
    {"id": "chestnut",     "name": "Chestnut",     "hex": "#5B402C", "provisional": True},
    {"id": "dark_brown",   "name": "Dark Brown",   "hex": "#422A1C", "provisional": False},
    {"id": "soft_black",   "name": "Soft Black",   "hex": "#29150B", "provisional": True},
]
COLOUR_BY_ID = {c["id"]: c for c in COLOURS}
DEFAULT_COLOUR = "dark_brown"  # Dev note on 29: preview renders as Dark Brown

# -------------------------------------------------------------- profile
# Screen 14 skin tone row and screen 15 "brow shades for this tone".
SKIN_TONES = [
    {"id": "fair",   "name": "Fair",   "hex": "#F3DCC4"},
    {"id": "light",  "name": "Light",  "hex": "#E9C39C"},
    {"id": "medium", "name": "Medium", "hex": "#C99A5B"},
    {"id": "tan",    "name": "Tan",    "hex": "#A86A3D"},
    {"id": "deep",   "name": "Deep",   "hex": "#7A4A2C"},
    {"id": "rich",   "name": "Rich",   "hex": "#4E2E20"},
]
SKIN_TONE_BY_ID = {t["id"]: t for t in SKIN_TONES}
UNDERTONES = ["warm", "neutral", "cool"]

# Best + two close shades per tone (screen 15). PROVISIONAL mapping: the
# client has not supplied this table. Cool undertones swap the warm
# 'close' shade for an ash one.
BROW_SHADES_FOR_TONE = {
    "fair":   {"best": "light_taupe",  "close": ["blonde", "taupe"]},
    "light":  {"best": "taupe",        "close": ["light_taupe", "light_brown"]},
    "medium": {"best": "chestnut",     "close": ["dark_brown", "medium_brown"]},
    "tan":    {"best": "dark_brown",   "close": ["chestnut", "medium_brown"]},
    "deep":   {"best": "dark_brown",   "close": ["soft_black", "chestnut"]},
    "rich":   {"best": "soft_black",   "close": ["dark_brown", "chestnut"]},
}
COOL_SWAP = {"chestnut": "medium_brown", "light_brown": "taupe", "medium_brown": "taupe"}

BROW_GOALS = [
    {"id": "shape", "name": "Shape"},
    {"id": "colour", "name": "Colour"},
    {"id": "both", "name": "Both"},
]

# Screens 16 and 17. Refined & natural copy is quoted; the other two
# confirmation lists are drafted to match and marked provisional.
STYLE_DIRECTIONS = {
    "refined_natural": {
        "name": "Refined & natural",
        "line": "Soft shaping that works with your features, not over them.",
        "confirmation": ["Arch presented first",
                         "Colours that enhance rather than overpower.",
                         "Understated intensity recommended by default"],
        "first_style": "arch",
        "default_intensity": "understated",
        "default_mode": "refine",
        "provisional": False,
    },
    "precise_defined": {
        "name": "Precise & defined",
        "line": "A brow with intention. Clear lines, confident shape.",
        "confirmation": ["Structured presented first",
                         "Colours with clear definition.",
                         "Defined intensity recommended by default"],
        "first_style": "structured",
        "default_intensity": "defined",
        "default_mode": "reshape",
        "provisional": True,
    },
    "show_me": {
        "name": "Show me what suits me",
        "line": "A brief discovery to find the shape that's meant for you.",
        "confirmation": ["Your face scan chooses the first style",
                         "Colours matched to your tone.",
                         "Defined intensity recommended by default"],
        "first_style": None,
        "default_intensity": "defined",
        "default_mode": "reshape",
        "provisional": True,
    },
}
DIRECTION_ORDER = ["refined_natural", "precise_defined", "show_me"]

# ------------------------------------------------------------- face shapes
# Taglines: master reference, Part E2.
FACE_SHAPE_TAGLINES = {
    "oval": "Every style was made for you.",
    "round": "Soft lines deserve a beautiful lift.",
    "square": "Your structure is your statement.",
    "heart": "The most romantic face shape there is.",
    "diamond": "Rare proportions. Rare possibilities.",
    "oblong": "Length is elegance in its purest form.",
    "triangle": "Strength below. Width above. Your brow leads the eye.",
}

# ------------------------------------------------------------- error routes
# Error code -> screen the app should show. Scan errors per the screen map.
ERROR_ROUTES = {
    "ACCOUNT_REQUIRED": "13",       # Scan Gate (13a for Looks / Profile)
    "CONSENT_REQUIRED": "23",
    "NO_FACE": "26",
    "MULTIPLE_FACES": "26",
    "FACE_NOT_CENTRED": "26",
    "FACE_TOO_SMALL": "26",
    "FACE_TURNED": "26",
    "BROWS_NOT_VISIBLE": "26",
    "LOW_LIGHT": "84",
    "SCAN_NOT_FOUND": "22",
    "BAD_IMAGE": "26",
}


def colour_label(colour_id: str) -> str:
    return COLOUR_BY_ID[colour_id]["name"]


def look_caption(style_id: str, intensity: str, colour_id: str, upper=False) -> str:
    from app.catalogue.measurements import load_measurements
    name = load_measurements().style(style_id).name
    s = f"{name} · {INTENSITIES[intensity]['name']} · {colour_label(colour_id)}"
    return s.upper() if upper else s
