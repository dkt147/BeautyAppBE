"""Turns one row of the Measurement JSON into brow edge curves.

Output is in EYE-WIDTH units in the eye-line frame, origin at the Head
(the lower inner end of the brow), x toward the Tail, y toward the forehead:

    x(u) = u * length_ew,  u in [0, 1]
    top(u), bottom(u)

Every figure the JSON fixes is honoured:
  * length_ew                         -> x(1)
  * peak_position_pct (+ face shape)  -> where top() is highest
  * peak_height_ew                    -> top(peak) - Head
  * plateau range                     -> flat run (falls < 0.04 EW within it)
  * thickness head / body / tail      -> top - bottom at 10 %, thickest, 90 %
  * tail_vs_head offset               -> centre of the tail tip
Interpretation (see README): Head is the LOWER inner end of the brow. That is
the only reading under which Straight's "level top edge 0.25 above Head"
and its 0.27 head thickness agree.
"""
import numpy as np

from app.catalogue.measurements import StyleSpec

N = 200


def _smooth(y, frac):
    win = int(frac * len(y))
    if win < 2:
        return y
    k = np.hanning(2 * win + 1)
    k /= k.sum()
    return np.convolve(np.pad(y, win, mode="edge"), k, mode="valid")


def _ease(x):
    return 0.5 - 0.5 * np.cos(np.pi * np.clip(x, 0, 1))


def style_profile(st: StyleSpec, peak_pct=None, plateau=None, n=N):
    """Build the profile, then correct twice so the re-measured peak
    position, peak height and tail offset land on the JSON figures after the
    corner smoothing."""
    d_p = d_h = d_t = 0.0
    target_p = peak_pct if peak_pct is not None else st.peak_position_pct
    for _ in range(3):
        prof = _build(st, peak_pct, plateau, n, d_p, d_h, d_t)
        chk = check_profile(st, prof)
        d_t += st.tail_offset_ew - chk["tail_vs_head_offset_ew"]
        if st.peak_type != "level":
            d_h += st.peak_height_ew - chk["peak_height_ew"]
            if st.peak_type == "pointed" and target_p is not None:
                d_p += target_p - chk["peak_position_pct"]
    return prof


def _build(st, peak_pct, plateau, n, d_p, d_h, d_t):
    u = np.linspace(0.0, 1.0, n)
    ph = st.peak_height_ew + d_h
    th_h, th_b, th_t = st.thickness_head_ew, st.thickness_body_ew, st.thickness_tail_ew
    tip = 0.30 * th_t
    t_end = st.tail_offset_ew + 0.5 * tip + d_t

    kind = st.peak_type
    if kind == "level":
        a, b, p = 0.18, 0.70, 0.45
    elif kind == "plateau":
        a, b = [v / 100 for v in (plateau or st.plateau_range_pct)]
        p = (peak_pct if peak_pct is not None else st.peak_position_pct) / 100
    else:
        p = ((peak_pct if peak_pct is not None else st.peak_position_pct) + d_p) / 100
        a = b = p
    a, b, p = float(np.clip(a, 0.2, 0.85)), float(np.clip(b, 0.2, 0.88)), float(np.clip(p, 0.2, 0.88))

    # ---- thickness along the brow
    ub = float(np.clip(0.55 * a + 0.05, 0.22, 0.42))       # body = thickest
    u_pk_end = max(b, ub + 0.08)
    th_pk = th_b - 0.20 * (th_b - th_t) if kind != "level" else th_b - 0.08 * (th_b - th_t)
    th = np.interp(u, [0.0, 0.10, ub, u_pk_end, 0.90, 1.0],
                   [0.80 * th_h, th_h, th_b, th_pk, th_t, tip])
    th = _smooth(th, 0.05)

    # ---- top edge
    top = np.empty_like(u)
    t0 = th_h if kind != "plateau" else min(th_h, ph - 0.02)
    m0 = u <= 0.10
    top[m0] = t0
    mr = (u > 0.10) & (u <= a)
    x = (u[mr] - 0.10) / max(a - 0.10, 1e-3)
    if kind == "pointed":
        r = 0.65 * x + 0.35 * (1 - (1 - x) ** 2)      # nearly straight climb
        top[mr] = t0 + (ph - t0) * r
    elif kind == "plateau":
        top[mr] = t0 + (ph - 0.02 - t0) * _ease(x) ** 0.85
    else:
        top[mr] = t0 + (ph - t0) * _ease(x)
    mp_ = (u > a) & (u <= b)
    if mp_.any():
        half = max((b - a) / 2, 1e-3)
        top[mp_] = ph - 0.02 * ((u[mp_] - p) / half) ** 2 if kind == "plateau" else ph
    mf = u > b
    x = (u[mf] - b) / max(1 - b, 1e-3)
    start = top[mp_][-1] if mp_.any() else ph
    if kind == "pointed":
        f = x ** 1.12
    elif kind == "plateau":
        f = x ** 1.45
    else:
        f = x ** 1.9
    top[mf] = start + (t_end - start) * f

    corner = {"sharp": 0.02, "arch": 0.035, "feathered": 0.045}.get(st.id, 0.06)
    top = _smooth(top, corner)

    bottom = _smooth(top - th, 0.07)
    # rounded, tapering head instead of a square cut: thickness closes in
    # toward the very start around a slightly lowered centre line
    cap = 0.30 + 0.70 * np.sqrt(np.clip(u / 0.09, 0.0, 1.0))
    mid = bottom + 0.42 * (top - bottom)
    half_up, half_dn = top - mid, mid - bottom
    top = mid + half_up * cap
    bottom = mid - half_dn * cap
    top = np.maximum(top, bottom + 0.15 * tip)
    return {"u": u, "x": u * st.length_ew, "top": top, "bottom": bottom,
            "peak_u": p, "plateau": (a, b) if kind == "plateau" else None}


def check_profile(st: StyleSpec, prof) -> dict:
    """Re-measure a generated profile the way the JSON defines it (QA)."""
    u, top, bot = prof["u"], prof["top"], prof["bottom"]
    th = top - bot
    i = lambda q: int(round(q * (len(u) - 1)))
    ipk = int(np.argmax(top))
    tail_c = 0.5 * (top[-1] + bot[-1])
    return {
        "length_ew": round(float(prof["x"][-1]), 3),
        "peak_position_pct": round(float(u[ipk] * 100), 1),
        "peak_height_ew": round(float(top[ipk]), 3),
        "thickness_head_ew": round(float(th[i(0.10)]), 3),
        "thickness_body_ew": round(float(th.max()), 3),
        "thickness_tail_ew": round(float(th[i(0.90)]), 3),
        "tail_vs_head_offset_ew": round(float(tail_c), 3),
    }
