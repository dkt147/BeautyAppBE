"""Reads her natural brow and measures it with the client's own measures.

The landmark brow band is snapped onto the real hair in the photo, then the
brow is measured in the eye-line frame, in eye-width units, exactly as the
Measurement JSON defines length, peak position, peak height, thickness at
head / body / tail and tail vs head. That gives screen 27 its "BROW SHAPE"
reading and gives Refine mine her real shape to work from.
"""
from dataclasses import dataclass

import cv2
import numpy as np

from app.vision.landmarks import BROW, EYE, eye_frame, eye_width


def _luma(img):
    return 0.114 * img[..., 0] + 0.587 * img[..., 1] + 0.299 * img[..., 2]


def _odd(n):
    n = max(3, int(round(n)))
    return n if n % 2 == 1 else n + 1


def ipd(lm):
    return float(np.linalg.norm(lm[EYE["left"]["iris"], :2] - lm[EYE["right"]["iris"], :2]))


@dataclass
class NaturalBrow:
    side: str
    frame: object
    ew: float            # eye width, px
    upper: np.ndarray    # (k, 2) local (s, n) px, sorted by s
    lower: np.ndarray
    head_s: float
    tail_s: float

    def top(self, s):
        return np.interp(s, self.upper[:, 0], self.upper[:, 1])

    def bottom(self, s):
        return np.interp(s, self.lower[:, 0], self.lower[:, 1])

    @property
    def thickness_px(self):
        ss = np.linspace(self.head_s, self.tail_s, 20)[2:12]
        return float(np.median(self.top(ss) - self.bottom(ss)))


def hair_map(roi_bgr, scale_px):
    """0..1 'hairness': dark thin structure vs the local skin level."""
    L = cv2.GaussianBlur(_luma(roi_bgr.astype(np.float32)), (0, 0), 0.8)
    k = _odd(2.4 * scale_px)
    Ls = cv2.morphologyEx(L, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    Ls = cv2.GaussianBlur(Ls, (0, 0), max(1.0, 0.3 * scale_px))
    return np.clip((Ls - L) / (0.12 * Ls + 4.0), 0.0, 1.0)


def _snap_to_hair(image, frame, upper, lower, ipd_px):
    h, w = image.shape[:2]

    def top(s):
        return np.interp(s, upper[:, 0], upper[:, 1])

    def bot(s):
        return np.interp(s, lower[:, 0], lower[:, 1])

    head = max(upper[0, 0], lower[0, 0])
    tail = min(upper[-1, 0], lower[-1, 0])
    if tail - head < 0.1 * ipd_px:
        return upper, lower
    ss = np.linspace(head, tail, 24)
    tn = max(float(np.median(top(ss) - bot(ss))), 0.10 * ipd_px)

    pts = np.concatenate([frame.to_image(upper[:, 0], upper[:, 1] + 0.8 * tn),
                          frame.to_image(lower[:, 0], lower[:, 1] - 1.1 * tn)])
    m = 2.5 * tn
    x0 = int(max(0, pts[:, 0].min() - m)); x1 = int(min(w, pts[:, 0].max() + m))
    y0 = int(max(0, pts[:, 1].min() - m)); y1 = int(min(h, pts[:, 1].max() + m))
    if x1 - x0 < 8 or y1 - y0 < 8:
        return upper, lower
    hair = hair_map(image[y0:y1, x0:x1], tn)

    step = 0.5
    bots, tops, nb, nt, sec_s = [], [], [], [], []
    for s in ss[1:-1]:
        n = np.arange(bot(s) - 1.0 * tn, top(s) + 0.6 * tn, step)
        xy = frame.to_image(np.full_like(n, s), n) - np.array([x0, y0])
        prof = cv2.remap(hair, xy[:, 0].astype(np.float32)[None], xy[:, 1].astype(np.float32)[None],
                         cv2.INTER_LINEAR, borderValue=0)[0]
        on = prof > 0.35
        gap = max(1, int(0.15 * tn / step))
        on = cv2.morphologyEx(on.astype(np.uint8)[None], cv2.MORPH_CLOSE,
                              np.ones((1, 2 * gap + 1), np.uint8))[0] > 0
        c = 0.5 * (top(s) + bot(s))
        ci = int(np.argmin(np.abs(n - c)))
        if not on[ci]:
            cand = np.where(on)[0]
            if len(cand) == 0:
                continue
            ci = int(cand[np.argmin(np.abs(cand - ci))])
            if abs(n[ci] - c) > 0.6 * tn:
                continue
        i0 = ci
        while i0 > 0 and on[i0 - 1]:
            i0 -= 1
        i1 = ci
        while i1 < len(on) - 1 and on[i1 + 1]:
            i1 += 1
        thick = (i1 - i0) * step
        if thick < 0.3 * tn or thick > 2.6 * tn:
            continue
        bots.append(n[i0]); tops.append(n[i1]); nb.append(bot(s)); nt.append(top(s)); sec_s.append(s)

    if len(bots) < 4:
        return upper, lower
    bots, tops, nb, nt = map(np.array, (bots, tops, nb, nt))
    # MediaPipe's lower brow points rarely sit above the true lower edge, and
    # eye make-up below reads as "hair", so the lower edge may barely move down.
    d_bot = float(np.clip(np.median(bots - nb), -0.15 * tn, 0.6 * tn))
    d_top = float(np.clip(np.median(tops - nt), -0.6 * tn, 0.6 * tn))
    upper = upper.copy(); lower = lower.copy()
    upper[:, 1] += 0.85 * d_top
    lower[:, 1] += 0.85 * d_bot
    if len(bots) >= 8:
        # Trace the real edges where the photo shows them: per-section
        # measurements, median-filtered, kept within half a brow thickness
        # of the shifted landmark line.
        ks = np.array(sec_s)

        def trace(meas, base_s, base_n, lo=-0.4, hi=0.4):
            ref = np.interp(ks, base_s, base_n)
            dev = np.clip(meas - ref, lo * tn, hi * tn)
            pad = np.pad(dev, 2, mode="edge")
            dev = np.array([np.median(pad[i:i + 5]) for i in range(len(dev))])
            dev = np.convolve(np.pad(dev, 2, mode="edge"), np.hanning(7)[1:-1] / np.hanning(7)[1:-1].sum(), mode="valid")
            out_s = np.concatenate([[base_s[0]], ks, [base_s[-1]]])
            out_n = np.concatenate([[base_n[0]], ref + dev, [base_n[-1]]])
            o = np.argsort(out_s)
            return np.stack([out_s[o], out_n[o]], axis=1)

        upper = trace(tops, upper[:, 0], upper[:, 1])
        lower = trace(bots, lower[:, 0], lower[:, 1], lo=-0.12)
    return upper, lower


def read_natural_brow(image, lm, side) -> NaturalBrow:
    frame = eye_frame(lm, side)
    idx = BROW[side]
    upper = frame.to_local(lm[idx["upper"]])
    lower = frame.to_local(lm[idx["lower"]])
    upper = upper[np.argsort(upper[:, 0])]
    lower = lower[np.argsort(lower[:, 0])]
    upper, lower = _snap_to_hair(image, frame, upper, lower, ipd(lm))
    head = float(min(upper[0, 0], lower[0, 0]))
    tail = float(max(upper[-1, 0], lower[-1, 0]))
    return NaturalBrow(side, frame, eye_width(lm, side), upper, lower, head, tail)


def measure(nb: NaturalBrow) -> dict:
    """Her brow in the Measurement JSON's terms (eye-width ratios)."""
    ew = nb.ew
    L = nb.tail_s - nb.head_s
    u = np.linspace(0, 1, 101)
    s = nb.head_s + u * L
    top, bot = nb.top(s), nb.bottom(s)
    head_y = float(nb.bottom(nb.head_s + 0.1 * L))   # Head = lower inner end
    th = top - bot
    i_pk = int(np.argmax(top[5:96])) + 5
    peak_h = float(top[i_pk] - head_y)
    # pointed / plateau / level, per the JSON's own test (+-15 points)
    lo, hi = max(0, i_pk - 15), min(100, i_pk + 15)
    drop = float(top[i_pk] - max(top[lo], top[hi]) if hi > lo else 0) / ew
    rise = float(top[i_pk] - top[10]) / ew
    if rise < 0.035:
        peak_type = "level"
    elif drop >= 0.06:
        peak_type = "pointed"
    elif drop < 0.04:
        peak_type = "plateau"
    else:
        peak_type = "soft"
    tail_c = float(0.5 * (top[-1] + bot[-1]))
    return {
        "length_ew": round(L / ew, 3),
        "peak_position_pct_from_head": round(float(u[i_pk] * 100), 1),
        "peak_height_ew": round(peak_h / ew, 3),
        "peak_type": peak_type,
        "arch_rise_ew": round(rise, 3),
        "thickness_head_ew": round(float(th[10]) / ew, 3),
        "thickness_body_ew": round(float(th[5:80].max()) / ew, 3),
        "thickness_tail_ew": round(float(th[90]) / ew, 3),
        "tail_vs_head_offset_ew": round((tail_c - head_y) / ew, 3),
    }


def brow_shape_label(m: dict) -> str:
    """Plain-language reading for screen 27 (e.g. 'High arch')."""
    rise, kind = m["arch_rise_ew"], m["peak_type"]
    if kind == "level" or rise < 0.035:
        return "Straight"
    if rise >= 0.13:
        return "High arch"
    if kind == "pointed":
        return "Defined arch"
    if kind == "plateau" and m["peak_position_pct_from_head"] < 55:
        return "Rounded"
    if rise >= 0.08:
        return "Soft arch"
    return "Low arch"


def closest_style(m: dict, styles: dict) -> str:
    """Nearest of the eight styles to her natural brow (for copy, not for
    the recommendation, which comes from face shape)."""
    best, best_d = None, 1e9
    for sid, st in styles.items():
        pk = st.peak_position_pct if st.peak_position_pct is not None else 50.0
        d = (((m["peak_position_pct_from_head"] - pk) / 15.0) ** 2
             + ((m["peak_height_ew"] - st.peak_height_ew) / 0.08) ** 2
             + ((m["thickness_body_ew"] - st.thickness_body_ew) / 0.07) ** 2
             + ((m["tail_vs_head_offset_ew"] - st.tail_offset_ew) / 0.10) ** 2)
        if d < best_d:
            best, best_d = sid, d
    return best


def fullness(image, nb: NaturalBrow) -> float:
    """0..1 coverage of hair inside her brow band (sparse brows read low)."""
    T = max(nb.thickness_px, 3.0)
    ss = np.linspace(nb.head_s, nb.tail_s, 40)
    poly = np.concatenate([nb.frame.to_image(ss, nb.top(ss)),
                           nb.frame.to_image(ss[::-1], nb.bottom(ss[::-1]))])
    x0, y0 = np.floor(poly.min(0) - 2 * T).astype(int)
    x1, y1 = np.ceil(poly.max(0) + 2 * T).astype(int)
    h, w = image.shape[:2]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(w, x1), min(h, y1)
    if x1 - x0 < 6 or y1 - y0 < 6:
        return 0.0
    hm = hair_map(image[y0:y1, x0:x1], T)
    mask = np.zeros(hm.shape, np.uint8)
    cv2.fillPoly(mask, [np.round(poly - [x0, y0]).astype(np.int32)], 1)
    if mask.sum() < 10:
        return 0.0
    return float(np.clip((hm[mask > 0] > 0.3).mean(), 0, 1))
