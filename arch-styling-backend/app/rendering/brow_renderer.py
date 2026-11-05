"""Realistic still-photo brow renderer for RESHAPE MINE and REFINE MINE.

RESHAPE MINE ("The style's shape, placed on your brow")
  1. Place the style's measured shape (geometry.style_profile) on her face:
     eye-line frame per eye, scaled by that eye's width, Head anchored on
     her own brow's lower inner end.
  2. Conceal her natural brow: skin is rebuilt from the surrounding skin,
     with the photo's own grain, so the old brow does not show through.
  3. Paint a soft powder body plus hundreds of tapered, curved hairs whose
     growth follows the client's stroke-direction zones (B7).
  4. Light the pigment with the photo's own shading and match its blur.

REFINE MINE ("Your own shape, filled and groomed toward the style")
  Her own brow stays. The target is her shape moved part of the way toward
  the style. Sparse areas are filled, stray hairs outside the target are
  softened away, new hairs go mostly where she has none, and her own hairs
  take on the chosen colour. This is the project's working assumption.

Intensity (Understated / Defined / Deliberate) changes fill weight and
colour density only. The shape never changes between intensities, and the
hairs of a lighter intensity are a subset of the heavier ones, so the three
previews read as "the same shape, three expressions".
"""
import math
from dataclasses import dataclass

import cv2
import numpy as np

from app.catalogue.measurements import StyleSpec
from app.rendering.geometry import style_profile
from app.vision.brow_measure import NaturalBrow, hair_map, ipd, read_natural_brow

SUPERSAMPLE = 4
REFINE_PULL = 0.5      # how far Refine moves her shape toward the style
MIN_LID_GAP_EW = 0.24  # lower brow edge stays this far above the upper lid
UPPER_LID = {"right": [33, 246, 161, 160, 159, 158, 157, 173, 133],
             "left": [263, 466, 388, 387, 386, 385, 384, 398, 362]}


@dataclass(frozen=True)
class Texture:
    """How a style's hairs look. Shape comes from the JSON, not from here."""
    density: float = 1.0       # hairs relative to standard
    length: float = 1.0        # hair length relative to standard
    width: float = 1.0         # hair width relative to standard
    fill: float = 0.50         # powder body at Defined
    spread: float = 6.0        # random angle spread, degrees
    spec_weight: float = 0.30  # how strongly B7 zone angles steer the hairs
    zones: tuple = (75, 87, 62)  # B7 stroke angles from horizontal: front, peak, tail
    crisp: float = 1.0         # edge crispness (structured / sharp are cleaner)


TEXTURES = {
    "arch":       Texture(zones=(75, 87, 62)),
    "structured": Texture(fill=0.58, spread=4.5, crisp=1.5, zones=(75, 87, 62)),
    "feathered":  Texture(density=0.9, length=1.15, fill=0.32, spread=11.0, spec_weight=0.45, crisp=0.7, zones=(68, 85, 62)),
    "bold":       Texture(density=1.55, fill=0.68, width=1.1, zones=(75, 87, 62)),
    "straight":   Texture(fill=0.52, zones=(80, 80, 80), spec_weight=0.25),
    "micro":      Texture(density=0.85, length=0.7, width=0.7, fill=0.26, spread=4.0, crisp=1.2, zones=(77, 85, 65)),
    "sharp":      Texture(fill=0.55, crisp=1.4, spread=5.0, zones=(72, 89, 60)),
    "rounded":    Texture(fill=0.50, crisp=0.9, zones=(75, 86, 63)),
}

INTENSITY_LEVEL = {"understated": 0.35, "defined": 0.65, "deliberate": 0.95}


def _smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def _odd(n):
    n = max(3, int(round(n)))
    return n if n % 2 == 1 else n + 1


def _luma(img):
    return 0.114 * img[..., 0] + 0.587 * img[..., 1] + 0.299 * img[..., 2]


def hex_to_bgr(h):
    h = h.lstrip("#")
    return (int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16))


class BrowRenderer:
    _lm_cache = None

    def render(self, image, lm, style: StyleSpec, peak_pct, plateau, colour_hex,
               intensity="defined", mode="reshape", seed=1234, naturals=None):
        """image: BGR uint8. lm: (478, >=2) landmarks in pixels."""
        out = image.astype(np.float32)
        self._lm_cache = np.asarray(lm, np.float64)[:, :2]
        level = INTENSITY_LEVEL[intensity]
        tex = TEXTURES.get(style.id, Texture())
        colour = np.array(hex_to_bgr(colour_hex), np.float32)
        prof = style_profile(style, peak_pct, plateau)
        geos = {}
        for i, side in enumerate(("right", "left")):
            nb = (naturals or {}).get(side) or read_natural_brow(image, lm, side)
            geo = self._place(nb, prof, mode, ipd(lm))
            rng = np.random.default_rng(seed + 7919 * i)
            out = self._render_side(out, image, nb, geo, tex, colour, level, mode, rng)
            geos[side] = geo
        return np.clip(out, 0, 255).astype(np.uint8), geos

    # ------------------------------------------------------------ placement

    def _place(self, nb: NaturalBrow, prof, mode, ipd_px):
        ew = nb.ew
        # Head x: spec start point is above the inner eye corner (s = 0);
        # follow her own head when it is close, so the brow sits on hers.
        head_s = float(np.clip(0.6 * nb.head_s, -0.18 * ew, 0.12 * ew))
        L_style = prof["x"][-1] * ew
        u = prof["u"]
        s_style = head_s + prof["x"] * ew
        # Vertical placement: fit the style's centre line to her own brow's
        # centre line over head-to-peak (robust median), so the new brow sits
        # ON her brow rather than hanging off one noisy point.
        sel = (u > 0.05) & (u < 0.60) & (s_style > nb.head_s) & (s_style < nb.tail_s)
        if sel.sum() >= 5:
            nat_c = 0.5 * (nb.top(s_style[sel]) + nb.bottom(s_style[sel]))
            sty_c = 0.5 * (prof["top"][sel] + prof["bottom"][sel]) * ew
            head_y = float(np.median(nat_c - sty_c))
        else:
            head_y = float(nb.bottom(head_s + 0.1 * L_style))
        top_style = head_y + prof["top"] * ew
        bot_style = head_y + prof["bottom"] * ew
        if mode == "reshape":
            s, top, bot = s_style, top_style, bot_style
        else:
            # Refine: her own outline, moved REFINE_PULL of the way to the style.
            w = REFINE_PULL
            nat_head, nat_tail = nb.head_s, nb.tail_s
            nh = (1 - w) * nat_head + w * head_s
            nt = (1 - w) * nat_tail + w * s_style[-1]
            s = nh + u * (nt - nh)
            ns = nat_head + u * (nat_tail - nat_head)
            nat_top, nat_bot = nb.top(ns), nb.bottom(ns)
            top = (1 - w) * nat_top + w * top_style
            bot = (1 - w) * nat_bot + w * bot_style
            # taper her tail like a groomed brow
            tip = np.clip((u - 0.85) / 0.15, 0, 1)
            mid = 0.5 * (top + bot)
            top = top - (top - mid) * 0.75 * tip ** 1.5
            bot = bot + (mid - bot) * 0.75 * tip ** 1.5
        # Never sit on the eyelid: keep the lower edge a minimum distance
        # above the upper lid, lifting the whole brow (shape unchanged).
        lid = nb.frame.to_local(self._lm_cache[UPPER_LID[nb.side]]) if self._lm_cache is not None else None
        if lid is not None:
            lid = lid[np.argsort(lid[:, 0])]
            inside = (s > lid[0, 0]) & (s < lid[-1, 0])
            if inside.any():
                clear = bot[inside] - np.interp(s[inside], lid[:, 0], lid[:, 1])
                need = MIN_LID_GAP_EW * ew - float(clear.min())
                if need > 0:
                    lift = min(need, 0.25 * ew)
                    top = top + lift
                    bot = bot + lift
        T0 = float(np.max(top - bot))
        return {"u": u, "s": s, "top": top, "bottom": bot, "T0": max(T0, 3.0),
                "L": float(s[-1] - s[0]), "ipd": ipd_px, "frame": nb.frame}

    # ------------------------------------------------------------ rendering

    def _render_side(self, img, original, nb, geo, tex, colour, level, mode, rng):
        h, w = img.shape[:2]
        frame, T0 = geo["frame"], geo["T0"]
        poly_new = np.concatenate([frame.to_image(geo["s"], geo["top"]),
                                   frame.to_image(geo["s"][::-1], geo["bottom"][::-1])])
        nat = np.concatenate([nb.upper, nb.lower])
        pts = np.concatenate([poly_new, frame.to_image(nat[:, 0], nat[:, 1])])
        m = 1.4 * T0
        x0 = int(max(0, np.floor(pts[:, 0].min() - m))); y0 = int(max(0, np.floor(pts[:, 1].min() - m)))
        x1 = int(min(w, np.ceil(pts[:, 0].max() + m))); y1 = int(min(h, np.ceil(pts[:, 1].max() + m)))
        if x1 - x0 < 8 or y1 - y0 < 8:
            return img
        roi = img[y0:y1, x0:x1].copy()
        rh, rw = roi.shape[:2]
        off = np.array([x0, y0], np.float64)
        photo_blur = self._estimate_blur(roi)
        new_mask = self._poly_mask(poly_new - off, rh, rw, blur=0.08 * T0 / tex.crisp)
        existing = hair_map(original[y0:y1, x0:x1], T0)

        if mode == "reshape":
            roi = self._conceal(roi, nb, frame, T0, off, new_mask, inner_keep=0.25)
        else:
            outside = 1.0 - self._poly_mask(poly_new - off, rh, rw, blur=0.12 * T0, dilate=0.12 * T0)
            roi = self._conceal(roi, nb, frame, T0, off, outside, inner_keep=0.0, only_mask=True)

        # intensity: fill weight + colour density only
        k = (level - 0.35) / 0.60          # 0 at Understated, 1 at Deliberate
        fill_scale = 1.4 * level / 0.65
        hair_frac = 0.55 + 0.45 * k
        hair_op = 0.78 + 0.22 * k
        if mode == "refine":
            fill_scale *= 0.45
            hair_frac *= 0.55

        fill_a = self._fill_alpha(frame, geo, off, rh, rw, rng, tex) * tex.fill * fill_scale
        hair_a, hair_tone = self._hairs(frame, geo, off, rh, rw, rng, tex, hair_frac,
                                        existing if mode == "refine" else None)
        hair_a *= hair_op
        reach = self._poly_mask(poly_new - off, rh, rw, blur=0.10 * T0, dilate=0.10 * T0 / tex.crisp)
        hair_a *= reach

        match = max(0.0, photo_blur - 0.5) * 0.65
        if match > 0.15:
            hair_a = cv2.GaussianBlur(hair_a, (0, 0), match)
            hair_tone = cv2.GaussianBlur(hair_tone, (0, 0), match)
            fill_a = cv2.GaussianBlur(fill_a, (0, 0), match)

        tint_existing = None
        if mode == "refine":
            tint_existing = existing * self._poly_mask(poly_new - off, rh, rw, blur=0.1 * T0) * (0.25 + 0.35 * k)
        roi = self._composite(roi, fill_a, hair_a, hair_tone, T0, colour, level, tint_existing)
        img[y0:y1, x0:x1] = roi
        return img

    @staticmethod
    def _estimate_blur(roi):
        g = _luma(roi.astype(np.float32))

        def edge(x):
            gx = cv2.Sobel(x, cv2.CV_32F, 1, 0); gy = cv2.Sobel(x, cv2.CV_32F, 0, 1)
            return float(np.percentile(np.hypot(gx, gy), 97)) + 1e-3

        q = float(np.clip(edge(cv2.GaussianBlur(g, (0, 0), 1.0)) / edge(g), 0.3, 0.97))
        return float(np.clip(np.sqrt(q * q / (1 - q * q)), 0.0, 3.0))

    @staticmethod
    def _poly_mask(poly, rh, rw, blur=0.0, dilate=0.0):
        S = SUPERSAMPLE
        mask = np.zeros((rh * S, rw * S), np.uint8)
        cv2.fillPoly(mask, [np.round(poly * S).astype(np.int32)], 255)
        mask = cv2.resize(mask, (rw, rh), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        if dilate > 0.5:
            kk = _odd(2 * dilate)
            mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kk, kk)))
        if blur > 0.3:
            mask = cv2.GaussianBlur(mask, (0, 0), blur)
        return mask

    def _conceal(self, roi, nb, frame, T0, off, mask, inner_keep=0.25, only_mask=False):
        """Rebuild skin over natural hair. Reshape: the whole natural brow
        (a little real texture kept under the new brow). Refine: only hair
        outside the target (grooming strays)."""
        rh, rw = roi.shape[:2]
        up, lo = nb.upper, nb.lower
        grow = 0.30 * T0
        top_s = np.concatenate([[up[0, 0] - grow], up[:, 0], [up[-1, 0] + grow]])
        top_n = np.concatenate([[up[0, 1]], up[:, 1], [up[-1, 1]]]) + 0.45 * T0
        bot_s = np.concatenate([[lo[0, 0] - grow], lo[:, 0], [lo[-1, 0] + grow]])
        bot_n = np.concatenate([[lo[0, 1]], lo[:, 1], [lo[-1, 1]]]) - 0.18 * T0
        region = np.concatenate([frame.to_image(top_s, top_n), frame.to_image(bot_s[::-1], bot_n[::-1])]) - off
        region = self._poly_mask(region, rh, rw, blur=0.30 * T0)
        core = np.concatenate([frame.to_image(up[:, 0], up[:, 1]),
                               frame.to_image(lo[::-1, 0], lo[::-1, 1])]) - off
        core = self._poly_mask(core, rh, rw, blur=0.20 * T0)

        f = roi.astype(np.float32)
        L = _luma(f)
        kk = _odd(2.0 * T0)
        Ls = cv2.morphologyEx(L, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kk, kk)))
        Ls = cv2.GaussianBlur(Ls, (0, 0), max(1.0, 0.25 * T0))
        hairness = np.clip((Ls - L) / (0.10 * Ls + 6.0), 0.0, 1.0)
        hairness = cv2.GaussianBlur(hairness, (0, 0), max(0.8, 0.06 * T0))
        hairness = np.clip(hairness * 1.6, 0.0, 1.0)

        wgt = ((1.0 - hairness) ** 2 * (hairness < 0.25)).astype(np.float32)
        skin = None
        for sig in (1.8 * T0, 0.9 * T0, 0.4 * T0):
            sig = max(1.0, sig)
            den = cv2.GaussianBlur(wgt, (0, 0), sig)
            num = cv2.GaussianBlur(f * wgt[..., None], (0, 0), sig)
            est = num / np.maximum(den, 1e-4)[..., None]
            if skin is None:
                skin = est
            else:
                trust = np.clip(den / 0.35, 0.0, 1.0)[..., None]
                skin = skin * (1 - trust) + est * trust

        if only_mask:
            amount = region * mask * np.clip(hairness * 1.2, 0, 1) * 0.85
        else:
            # replace hair everywhere in the region, but only force a full
            # skin rebuild inside her brow itself (no visible patch edge)
            amount = region * np.maximum(np.clip(hairness * 1.4, 0.0, 1.0), 0.55 * core)
            amount *= 1.0 - mask * inner_keep

        hp = _luma(f - cv2.GaussianBlur(f, (0, 0), 1.5))
        outside = hp[region < 0.05]
        sigma = 1.4826 * float(np.median(np.abs(outside - np.median(outside)))) if outside.size > 50 else 1.0
        grain = np.random.default_rng(0).normal(0, 1, f.shape[:2]).astype(np.float32)
        grain = cv2.GaussianBlur(grain, (0, 0), 0.7)
        grain *= sigma / (float(np.std(grain)) + 1e-6)
        skin = skin + grain[..., None]
        a = amount[..., None]
        return f * (1 - a) + skin * a

    def _fill_alpha(self, frame, geo, off, rh, rw, rng, tex):
        """Powder body: soft ombre head, denser low, airy upper edge."""
        T0 = geo["T0"]
        u, s, top, bot = geo["u"], geo["s"], geo["top"], geo["bottom"]
        ramp = 0.15 + 0.85 * _smoothstep(u / 0.22)
        ramp *= 1.0 - 0.25 * _smoothstep((u - 0.85) / 0.15)
        S = SUPERSAMPLE
        canvas = np.zeros((rh * S, rw * S), np.float32)
        bands = np.linspace(0.0, 1.0, 6)
        step = 2
        for i in range(0, len(u) - step, step):
            sl = slice(i, i + step + 1)
            for j in range(len(bands) - 1):
                v0, v1 = bands[j], bands[j + 1]
                lo = bot[sl] + v0 * (top[sl] - bot[sl])
                hi = bot[sl] + v1 * (top[sl] - bot[sl])
                q = np.concatenate([frame.to_image(s[sl], hi), frame.to_image(s[sl][::-1], lo[::-1])]) - off
                vm = 0.5 * (v0 + v1)
                cv2.fillPoly(canvas, [np.round(q * S).astype(np.int32)], float(ramp[i] * (1.0 - 0.45 * vm * vm)))
        a = cv2.resize(canvas, (rw, rh), interpolation=cv2.INTER_AREA)
        a = cv2.GaussianBlur(a, (0, 0), max(0.6, 0.07 * T0 / tex.crisp))
        noise = rng.normal(0, 1, (max(2, rh // 6), max(2, rw // 6))).astype(np.float32)
        noise = cv2.resize(noise, (rw, rh), interpolation=cv2.INTER_CUBIC)
        a *= np.clip(1.0 + 0.12 * noise, 0.75, 1.25)
        # break up the outline a little: real edges are made of hair roots
        fine = rng.normal(0, 1, (max(2, rh // 2), max(2, rw // 2))).astype(np.float32)
        fine = cv2.resize(fine, (rw, rh), interpolation=cv2.INTER_LINEAR)
        edge = np.clip(4.0 * a * (1.0 - a), 0, 1)
        a = a * np.clip(1.0 + 0.35 * edge * fine, 0.5, 1.3)
        return np.clip(a, 0, 1)

    def _hairs(self, frame, geo, off, rh, rw, rng, tex, frac, existing):
        T0 = geo["T0"]
        u_s, s_s, top_s, bot_s = geo["u"], geo["s"], geo["top"], geo["bottom"]
        thick = top_s - bot_s
        center = 0.5 * (top_s + bot_s)
        tangent = np.arctan2(np.gradient(center), np.gradient(s_s))

        n_max = int(np.clip(tex.density * 64 * geo["L"] / T0, 140, 1100))
        # Every hair's parameters are drawn up front so a lighter intensity
        # is an exact subset of a heavier one.
        pdf = thick * (0.45 + 0.55 * _smoothstep(u_s / 0.18))
        cdf = np.cumsum(pdf); cdf /= cdf[-1]
        us = np.interp(rng.random(n_max), cdf, u_s)
        vs = rng.beta(1.3, 1.5, n_max) * 1.06 - 0.05   # a few roots just below the edge
        noise_ang = rng.normal(0, 1, n_max)
        len_r = rng.uniform(0.45, 0.80, n_max)
        bend_r = rng.normal(0.10, 0.06, n_max)
        wid_r = rng.uniform(0.75, 1.25, n_max)
        op_r = rng.uniform(0.55, 1.0, n_max)
        tone_r = rng.uniform(0.0, 1.0, n_max)
        keep_r = rng.random(n_max)
        n = int(n_max * frac)

        S = SUPERSAMPLE
        n_layers = 4
        layers = [np.zeros((rh * S, rw * S, 2), np.uint8) for _ in range(n_layers)]
        root_w = max(0.85, 0.024 * T0) * S * tex.width
        deg = math.radians
        z1, z2, z3 = tex.zones
        sw = tex.spec_weight

        for k in range(n):
            u, v = float(us[k]), float(vs[k])
            sb = float(np.interp(u, u_s, s_s)); tb = float(np.interp(u, u_s, top_s))
            bb = float(np.interp(u, u_s, bot_s)); phi = float(np.interp(u, u_s, tangent))
            n0 = bb + v * (tb - bb)
            if existing is not None:
                # Refine: new hairs go mostly where she has none.
                p = frame.to_image(sb, n0) - off
                xi, yi = int(np.clip(p[0], 0, rw - 1)), int(np.clip(p[1], 0, rh - 1))
                if existing[yi, xi] > 0.45 and keep_r[k] < 0.75:
                    continue
            loc_thick = tb - bb
            head = 1.0 - _smoothstep((u - 0.08) / 0.17)
            tail = _smoothstep((u - 0.72) / 0.15)
            # natural growth (herringbone) ...
            body_ang = phi + deg(40.0 - 48.0 * v)
            head_ang = deg(84.0) + deg(10.0) * (v - 0.5)
            tail_ang = phi + deg(10.0 - 14.0 * v)
            nat = (head * head_ang + (1 - head) * body_ang)
            nat = (1 - tail) * nat + tail * tail_ang
            # ... steered toward the client's zone angles (B7)
            zone = z1 if u < 0.30 else (z2 if u < 0.70 else z3)
            spec_ang = deg(zone) if u < 0.70 else phi + deg(zone) * 0.35
            wz = sw * (1.4 if u < 0.30 else 1.0)
            ang = (1 - wz) * nat + wz * spec_ang + deg(tex.spread) * noise_ang[k]

            length = T0 * len_r[k] * tex.length
            length = head * min(length, 0.75 * T0) + (1 - head) * length
            if tail > 0.3:
                length = max(length, 0.6 * T0 * tex.length)
            length = min(length, max(loc_thick * 2.2, 0.35 * T0))
            if u > 0.92:   # fine, flat hairs at the very tip
                length = min(length, 0.45 * T0)
                ang = 0.5 * ang + 0.5 * phi

            d = np.array([math.cos(ang), math.sin(ang)])
            perp = np.array([d[1], -d[0]])
            bend = length * bend_r[k]
            p0 = np.array([sb, n0]); p2 = p0 + d * length; p1 = p0 + d * 0.5 * length + perp * bend
            t = np.linspace(0.0, 1.0, 9)[:, None]
            curve = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2
            img_pts = (frame.to_image(curve[:, 0], curve[:, 1]) - off) * S
            seg = np.gradient(img_pts, axis=0)
            seg /= np.linalg.norm(seg, axis=1, keepdims=True) + 1e-9
            nrm = np.stack([-seg[:, 1], seg[:, 0]], axis=1)
            width = np.maximum(root_w * (1.0 - t[:, 0]) ** 0.85 * wid_r[k], 0.0)
            poly = np.concatenate([img_pts + nrm * width[:, None] / 2, (img_pts - nrm * width[:, None] / 2)[::-1]])
            op = op_r[k] * (0.32 + 0.68 * (1 - head)) * (1.0 - 0.15 * tail)
            col = (int(255 * op), int(255 * op * tone_r[k]))
            cv2.fillPoly(layers[k % n_layers], [np.round(poly).astype(np.int32)], col)

        keep = np.ones((rh, rw), np.float32)
        tone_acc = np.zeros((rh, rw), np.float32); a_acc = np.zeros((rh, rw), np.float32)
        for layer in layers:
            small = cv2.resize(layer.astype(np.float32) / 255.0, (rw, rh), interpolation=cv2.INTER_AREA)
            a = small[..., 0]
            tone_acc += small[..., 1]; a_acc += a; keep *= 1.0 - a
        return (1.0 - keep) * 0.95, tone_acc / np.maximum(a_acc, 1e-4)

    def _composite(self, roi, fill_a, hair_a, hair_tone, T0, colour, level, tint_existing):
        f = roi.astype(np.float32)
        L = _luma(f)
        flat = f.reshape(-1, 3)
        lum = _luma(flat)
        skin_ref = np.median(flat[lum >= np.percentile(lum, 50)], axis=0)
        skin_ref_l = float(_luma(skin_ref[None])[0]) + 1e-3
        shading = np.clip(cv2.GaussianBlur(L, (0, 0), max(1.5, 0.9 * T0)) / skin_ref_l, 0.55, 1.25)[..., None]
        detail = np.clip(L / (cv2.GaussianBlur(L, (0, 0), max(1.0, 0.25 * T0)) + 1.0), 0.75, 1.25)[..., None]

        # A light colour on deep skin must still read: keep the pigment from
        # being lighter than the skin it sits on (multiply never lightens).
        col = colour.copy()
        skin_l = skin_ref_l
        col_l = float(_luma(col[None])[0])
        if col_l > 0.92 * skin_l:
            col = col * (0.92 * skin_l / max(col_l, 1.0))

        # Translucency: hair and powder pick up a little of the skin's own
        # warmth, which is what keeps light shades from reading olive.
        chroma = np.clip(skin_ref / (skin_l + 1e-3), 0.6, 1.6)
        col = np.clip(col * chroma ** 0.30, 0, 255)

        out = f
        if tint_existing is not None:
            # her own hairs take on the chosen colour
            # recolour (not repaint): keep each hair's own light and dark
            ta = np.clip(tint_existing, 0, 1)[..., None]
            hm = tint_existing > 0.15
            ref = np.median(out[hm], axis=0) if hm.sum() > 20 else out.reshape(-1, 3).mean(0)
            gain = np.clip(col * 0.8 / (ref + 1.0), 0.35, 1.6)
            out = out * (1 - ta) + np.minimum(out * gain, out * 1.05) * ta

        # Powder body: the pigment colour itself, lit by the photo's own
        # light and pores. (Multiplying the skin by colour/skin shifts hue:
        # on pink skin a taupe turns olive, so it is not used.)
        lit = np.clip(L / skin_ref_l, 0.45, 1.3)[..., None]
        tint = np.minimum(col[None, None, :] * lit, out)
        fa = np.clip(fill_a, 0, 1)[..., None]
        out = out * (1 - fa) + tint * fa

        dark = col * 0.66
        light = np.minimum(col * 1.30 + 4.0, 255.0)
        tone = hair_tone[..., None]
        hair_col = (dark * (1 - tone) + light * tone) * shading * detail ** 0.4
        ha = np.clip(hair_a, 0, 1)[..., None]
        return out * (1 - ha) + hair_col * ha
