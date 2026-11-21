#!/usr/bin/env python3
"""VELTARA — a vintage travel poster for a place that isn't there.

Draws, with PIL only, a poster for Veltara: an island peak carved into a
colossal staircase, its terraces lantern-lit, rising out of a calm dusk
sea under a low sun. Writes the poster to /output/entry.png.
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------- canvas
SS = 2                      # supersample factor
W, H = 768 * SS, 1024 * SS  # drawn large, downscaled to 768x1024
OUT_W, OUT_H = 768, 1024

# ---------------------------------------------------------------- palette
INK = (24, 22, 48)          # deep indigo, outlines and silhouettes
CREAM = (247, 234, 205)     # poster cream, type and paper
GOLD = (246, 205, 116)      # sun gold
AMBER = (255, 176, 92)      # lantern amber
CORAL = (232, 122, 84)
SKY_STOPS = [               # (height fraction, colour) top -> horizon
    (0.00, (38, 36, 84)),
    (0.30, (84, 52, 102)),
    (0.52, (166, 84, 96)),
    (0.64, (232, 138, 88)),
    (0.70, (246, 178, 102)),
]
SEA_TOP = (30, 74, 84)
SEA_BOT = (13, 34, 52)
RIDGE_FAR = (74, 52, 96)
RIDGE_NEAR = (46, 36, 74)
PEAK = (38, 44, 72)
PEAK_SHADE = (28, 32, 58)
HOUSE = (27, 23, 46)

HORIZON = 0.695             # sea line, fraction of H

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
]


def load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def sky_colour(t):
    """Colour of the sky at height fraction t (posterised for a print feel)."""
    for (t0, c0), (t1, c1) in zip(SKY_STOPS, SKY_STOPS[1:]):
        if t0 <= t <= t1:
            return lerp(c0, c1, (t - t0) / (t1 - t0))
    return SKY_STOPS[-1][1]


def draw_sky(img):
    d = ImageDraw.Draw(img)
    horizon_y = int(H * HORIZON)
    bands = 140
    for i in range(bands):
        y0 = int(horizon_y * i / bands)
        y1 = int(horizon_y * (i + 1) / bands) + 1
        d.rectangle([0, y0, W, y1], fill=sky_colour(i / bands))


def draw_sea(img):
    """The sea, painted over the sun so the disc meets the water cleanly."""
    d = ImageDraw.Draw(img)
    horizon_y = int(H * HORIZON)
    bands = 90
    for i in range(bands):
        y0 = horizon_y + int((H - horizon_y) * i / bands)
        y1 = horizon_y + int((H - horizon_y) * (i + 1) / bands) + 1
        d.rectangle([0, y0, W, y1], fill=lerp(SEA_TOP, SEA_BOT, i / bands))
    # a soft wash of sun-gold on the water under the disc
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    wd.polygon([(W * 0.36, horizon_y), (W * 0.64, horizon_y),
                (W * 0.74, H * 0.97), (W * 0.26, H * 0.97)],
               fill=(246, 190, 105, 42))
    img.alpha_composite(wash.filter(ImageFilter.GaussianBlur(30 * SS)))
    # the peak's reflection: a soft dark stepped shadow on the water
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    rd.polygon([(W * 0.335, horizon_y), (W * 0.665, horizon_y),
                (W * 0.56, H * 0.86), (W * 0.44, H * 0.86)], fill=(8, 14, 26, 46))
    img.alpha_composite(refl.filter(ImageFilter.GaussianBlur(30 * SS)))


def draw_stars(img, rng):
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(90):
        x = rng.uniform(0, W)
        y = rng.uniform(0, H * 0.34)
        r = rng.uniform(0.8, 2.2) * SS
        a = int(rng.uniform(40, 130) * (1 - y / (H * 0.4)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 210, max(a, 0)))


def draw_sun(img):
    cx, cy, r = W * 0.5, H * (HORIZON - 0.055), W * 0.315
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - r * 1.5, cy - r * 1.5, cx + r * 1.5, cy + r * 1.5],
               fill=(255, 176, 92, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(60 * SS))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(250, 214, 132))


def draw_ridges(img):
    d = ImageDraw.Draw(img)
    hy = H * HORIZON
    # far ridge, left and right shoulders
    d.polygon([(0, hy), (0, H * 0.52), (W * 0.16, H * 0.47), (W * 0.30, H * 0.56),
               (W * 0.38, hy)], fill=RIDGE_FAR)
    d.polygon([(W, hy), (W, H * 0.50), (W * 0.85, H * 0.455), (W * 0.71, H * 0.55),
               (W * 0.63, hy)], fill=RIDGE_FAR)
    # near headlands reaching into the sea
    d.polygon([(0, H * 0.80), (0, H * 0.635), (W * 0.13, H * 0.60),
               (W * 0.24, H * 0.70), (W * 0.20, H * 0.80)], fill=RIDGE_NEAR)
    d.polygon([(W, H * 0.765), (W, H * 0.62), (W * 0.88, H * 0.585),
               (W * 0.78, H * 0.695), (W * 0.83, H * 0.765)], fill=RIDGE_NEAR)


def peak_geometry():
    """Stepped-pyramid silhouette: returns (polygon, terraces).

    terraces: list of (y, half_width) for each tread, top first.
    """
    cx = W * 0.5
    apex_y = H * 0.335
    base_y = H * (HORIZON + 0.012)
    n = 13
    step_h = (base_y - apex_y) / n
    base_hw = W * 0.335

    def hw(i):  # half width at tread i (1..n), slight convex curve
        return base_hw * (i / n) ** 0.92

    pts = [(cx, apex_y)]
    terraces = []
    for i in range(1, n + 1):
        y_top = apex_y + (i - 1) * step_h
        pts.append((cx - hw(i), y_top))            # tread, out to the left
        pts.append((cx - hw(i), y_top + step_h))   # riser, down
        terraces.append((y_top, hw(i)))
    pts.append((cx + base_hw, base_y))
    for i in range(n, 0, -1):
        y_top = apex_y + (i - 1) * step_h
        pts.append((cx + hw(i), y_top + step_h))
        pts.append((cx + hw(i), y_top))
    pts.append((cx, apex_y))
    return pts, terraces, apex_y, step_h


def draw_peak(img, rng):
    d = ImageDraw.Draw(img)
    pts, terraces, apex_y, step_h = peak_geometry()
    d.polygon(pts, fill=PEAK)
    cx = W * 0.5
    # shade the right flank of every riser for depth
    for (y_top, hw_i) in terraces:
        d.rectangle([cx, y_top + step_h * 0.55, cx + hw_i, y_top + step_h],
                    fill=PEAK_SHADE)
    # sunlit tread edges
    for (y_top, hw_i) in terraces:
        d.line([cx - hw_i, y_top, cx + hw_i, y_top], fill=(96, 84, 118), width=2 * SS)
    return terraces, apex_y, step_h


def draw_village(img, terraces, apex_y, step_h, rng):
    """Tiny houses with lit windows on the terraces, lanterns on the path."""
    d = ImageDraw.Draw(img, "RGBA")
    cx = W * 0.5
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for idx, (y_top, hw_i) in enumerate(terraces):
        if idx < 2:
            continue
        base = y_top + step_h  # floor of this tread
        span = hw_i * 0.86
        count = max(1, int(span / (W * 0.09)))
        for k in range(count):
            side = -1 if (k + idx) % 2 == 0 else 1
            hx = cx + side * rng.uniform(0.18, 0.92) * span
            hw_ = rng.uniform(W * 0.016, W * 0.026)
            hh = hw_ * rng.uniform(0.8, 1.15)
            d.polygon([(hx - hw_, base), (hx + hw_, base), (hx, base - hh * 1.55)],
                      fill=HOUSE)
            d.rectangle([hx - hw_ * 0.8, base - hh, hx + hw_ * 0.8, base], fill=HOUSE)
            # lit window
            wx, wy = hx + rng.uniform(-0.3, 0.3) * hw_, base - hh * 0.55
            wr = max(3.0 * SS, hw_ * 0.22)
            d.rectangle([wx - wr / 2, wy - wr / 2, wx + wr / 2, wy + wr / 2],
                        fill=(255, 196, 105, 255))
            gd.ellipse([wx - wr * 2.4, wy - wr * 2.4, wx + wr * 2.4, wy + wr * 2.4],
                       fill=(255, 170, 80, 60))
        # lantern dots marching up the outer corners of the steps
        for side in (-1, 1):
            lx, ly = cx + side * hw_i, y_top + step_h * 0.5
            r = 3.4 * SS
            d.ellipse([lx - r, ly - r, lx + r, ly + r], fill=(255, 205, 115, 255))
            gd.ellipse([lx - r * 3, ly - r * 3, lx + r * 3, ly + r * 3],
                       fill=(255, 175, 85, 55))
    glow = glow.filter(ImageFilter.GaussianBlur(7 * SS))
    img.alpha_composite(glow)


def draw_summit(img, apex_y):
    """A small pavilion with a warm beacon at the top of the stair."""
    d = ImageDraw.Draw(img, "RGBA")
    cx = W * 0.5
    base = apex_y + H * 0.004
    # a stone platform crowning the stair, wider than the top tread
    pw = W * 0.085
    d.rectangle([cx - pw, base - H * 0.006, cx + pw, base], fill=PEAK_SHADE)
    d.line([cx - pw, base - H * 0.006, cx + pw, base - H * 0.006],
           fill=(96, 84, 118), width=2 * SS)
    w_ = W * 0.052
    h_ = H * 0.030
    d.rectangle([cx - w_, base - h_, cx + w_, base], fill=HOUSE)
    d.polygon([(cx - w_ * 1.25, base - h_), (cx + w_ * 1.25, base - h_),
               (cx, base - h_ * 1.8)], fill=HOUSE)
    d.rectangle([cx - w_ * 0.28, base - h_ * 0.72, cx + w_ * 0.28, base],
                fill=(255, 198, 105, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    r = W * 0.05
    gd.ellipse([cx - r, base - h_ * 0.5 - r, cx + r, base - h_ * 0.5 + r],
               fill=(255, 180, 90, 70))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16 * SS)))


def draw_sea_life(img, rng):
    d = ImageDraw.Draw(img, "RGBA")
    hy = H * HORIZON
    # sun glitter: broken gold dashes on the water
    for i in range(52):
        y = hy + (H * 0.955 - hy) * (i / 52) ** 1.25 + rng.uniform(0, 4) * SS
        spread = W * (0.05 + 0.16 * (i / 52))
        seg = rng.uniform(W * 0.02, W * 0.075)
        x = W * 0.5 + rng.uniform(-spread, spread)
        a = int(150 * (1 - i / 52))
        d.line([x - seg / 2, y, x + seg / 2, y], fill=(250, 205, 120, max(a, 0)),
               width=max(2, int(3.2 * SS * (1 - i / 70))))
    # one small sailboat, left of the glitter path
    bx, by = W * 0.265, H * 0.845
    s = W * 0.030
    d.polygon([(bx - s, by), (bx + s, by), (bx + s * 0.55, by + s * 0.42),
               (bx - s * 0.55, by + s * 0.42)], fill=INK)
    d.line([bx, by, bx, by - s * 1.5], fill=INK, width=3 * SS)
    d.polygon([(bx + 3 * SS, by - s * 1.45), (bx + 3 * SS, by - s * 0.12),
               (bx + s * 0.95, by - s * 0.12)], fill=CREAM)
    d.polygon([(bx - 3 * SS, by - s * 1.3), (bx - 3 * SS, by - s * 0.12),
               (bx - s * 0.7, by - s * 0.12)], fill=(238, 214, 175))


def draw_clouds(img, rng):
    d = ImageDraw.Draw(img, "RGBA")
    for (fx, fy, fw, col) in [
        (0.17, 0.265, 0.17, (250, 190, 150, 56)),
        (0.82, 0.245, 0.15, (250, 190, 150, 46)),
        (0.76, 0.415, 0.20, (236, 150, 130, 38)),
        (0.20, 0.44, 0.13, (236, 150, 130, 34)),
    ]:
        x, y, w_ = W * fx, H * fy, W * fw
        h_ = w_ * 0.10
        d.rounded_rectangle([x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2],
                            radius=h_ / 2, fill=col)


def draw_masthead(img):
    """VELTARA, letterspaced, set into the sky at the top."""
    d = ImageDraw.Draw(img)
    text = "VELTARA"
    size = int(W * 0.155)
    font = load_font(size)
    spacing = size * 0.16
    widths = []
    for ch in text:
        box = d.textbbox((0, 0), ch, font=font)
        widths.append(box[2] - box[0])
    total = sum(widths) + spacing * (len(text) - 1)
    x = (W - total) / 2
    y = H * 0.052
    for ch, wch in zip(text, widths):
        d.text((x + 3 * SS, y + 4 * SS), ch, font=font, fill=(30, 24, 54))
        d.text((x, y), ch, font=font, fill=CREAM)
        x += wch + spacing
    # hairline rule beneath the name
    rule_y = y + size * 1.28
    d.line([W * 0.30, rule_y, W * 0.70, rule_y], fill=(247, 234, 205), width=3 * SS)
    dot_r = 5 * SS
    d.ellipse([W / 2 - dot_r, rule_y - dot_r, W / 2 + dot_r, rule_y + dot_r],
              fill=GOLD)


def add_grain_and_frame(img, rng):
    noise = Image.effect_noise((W, H), 16).convert("L")
    noise = noise.point(lambda v: 128 + int((v - 128) * 0.5))
    img.paste(Image.merge("RGB", (noise, noise, noise)),
              (0, 0), noise.point(lambda v: 14))
    # vignette
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-W * 0.25, -H * 0.18, W * 1.25, H * 1.18], fill=70)
    vig = vig.filter(ImageFilter.GaussianBlur(120 * SS))
    img.paste(Image.new("RGB", (W, H), (10, 8, 24)), (0, 0), vig)
    # cream keyline frame
    d = ImageDraw.Draw(img)
    m = int(W * 0.028)
    d.rectangle([m, m, W - m, H - m], outline=CREAM, width=4 * SS)
    m2 = m + 10 * SS
    d.rectangle([m2, m2, W - m2, H - m2], outline=(247, 234, 205), width=1 * SS)


def main():
    rng = random.Random(20261121)
    img = Image.new("RGB", (W, H), INK).convert("RGBA")
    draw_sky(img)
    draw_stars(img, rng)
    draw_sun(img)
    draw_sea(img)
    draw_clouds(img, rng)
    draw_ridges(img)
    terraces, apex_y, step_h = draw_peak(img, rng)
    draw_village(img, terraces, apex_y, step_h, rng)
    draw_summit(img, apex_y)
    draw_sea_life(img, rng)
    draw_masthead(img)
    img = img.convert("RGB")
    add_grain_and_frame(img, rng)
    img = img.resize((OUT_W, OUT_H), Image.LANCZOS)
    os.makedirs("/output", exist_ok=True)
    img.save("/output/entry.png", optimize=True)
    print("wrote /output/entry.png", img.size)


if __name__ == "__main__":
    main()
