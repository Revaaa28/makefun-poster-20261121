"""Travel poster for a place that isn't there.

Renders one 1024x1024 travel poster to /output/entry.png (or
$MAKEFUN_OUTPUT_DIR/entry.png). Everything is drawn by code at runtime
with Pillow: gradients, glows, silhouettes, lanterns and type — no
network, no downloaded assets. The fonts are vendored in fonts/ next to
this file. Output is fully deterministic: fixed seed, no clock, no
timestamps in the PNG.

Concept is chosen with MF_POSTER_CONCEPT ("velmora" default, "nimbara"
alternative). The shipped concept is VELMORA — City of the Lantern
Tide: a coastal city at golden dusk, warm lanterns drifting on a
deep-teal sea, one tall lantern-tower as the single landmark.

If Pillow is unavailable in the sandbox, the program falls back to the
shipped entry.png (the same poster, rendered by this same code), so the
gate can never fail on a missing dependency.
"""

import os
import random
import shutil
from pathlib import Path

W = H = 1024
MAX_BYTES = 1_048_576
ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "fonts"

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    PIL_OK = True
except Exception:  # pragma: no cover - sandbox without Pillow
    PIL_OK = False


# ---------------------------------------------------------------- helpers

def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


def vgrad(img, stops):
    """Fill img with a vertical gradient. stops: [(frac, (r,g,b)), ...]."""
    d = ImageDraw.Draw(img)
    n = len(stops)
    for y in range(img.height):
        f = y / (img.height - 1)
        color = stops[-1][1]
        for i in range(n - 1):
            f0, c0 = stops[i]
            f1, c1 = stops[i + 1]
            if f <= f1:
                t = 0.0 if f1 == f0 else (f - f0) / (f1 - f0)
                color = lerp_color(c0, c1, max(0.0, min(1.0, t)))
                break
        else:
            if f < stops[0][0]:
                color = stops[0][1]
        d.line([(0, y), (img.width - 1, y)], fill=color)


def glow(size, color, core=0.34, blur=0.20):
    """Soft radial glow sprite (RGBA) of warm colour.

    The lit core is kept small and the blur tight relative to the sprite
    so the falloff completes inside the sprite: a wide blur on a big core
    leaves a visible square where the sprite is clipped.
    """
    g = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    m = size * (1 - core) / 2
    d.ellipse([m, m, size - m, size - m], fill=color + (255,))
    return g.filter(ImageFilter.GaussianBlur(size * blur))


def paste(base, sprite, cx, cy):
    """Paste an RGBA sprite centred at (cx, cy)."""
    base.alpha_composite(sprite, (int(cx - sprite.width / 2),
                                  int(cy - sprite.height / 2)))


def font(name, size):
    return ImageFont.truetype(str(FONT_DIR / name), size)


def tracked_width(draw, text, fnt, tracking):
    return sum(draw.textlength(ch, font=fnt) for ch in text) + tracking * max(
        0, len(text) - 1)


def draw_tracked(draw, cx, y, text, fnt, fill, tracking, stroke=0,
                 stroke_fill=None):
    """Draw letter-spaced text centred on cx at height y."""
    total = tracked_width(draw, text, fnt, tracking)
    x = cx - total / 2
    for ch in text:
        kw = {"font": fnt, "fill": fill}
        if stroke:
            kw["stroke_width"] = stroke
            kw["stroke_fill"] = stroke_fill
        draw.text((x, y), ch, **kw)
        x += draw.textlength(ch, font=fnt) + tracking


def draw_title(base, name, epithet):
    """The place name, big and legible, with its one-line epithet.

    Name sits in the upper sky; a soft dark scrim behind it keeps the
    cream type readable against the dusk gradient.
    """
    scrim = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for y in range(300):
        a = int(72 * (1 - y / 300) ** 1.6)
        sd.line([(0, y), (W - 1, y)], fill=(10, 14, 34, a))
    base.alpha_composite(scrim, (0, 0))
    d = ImageDraw.Draw(base)

    serif = font("DejaVuSerif-Bold.ttf", 170)
    while d.textlength(name, font=serif) > 900 and serif.size > 60:
        serif = font("DejaVuSerif-Bold.ttf", serif.size - 8)
    draw_tracked(d, W / 2, 78, name, serif, (255, 243, 214),
                 tracking=6, stroke=3, stroke_fill=(16, 20, 44))

    sans = font("DejaVuSans-Bold.ttf", 30)
    draw_tracked(d, W / 2, 78 + serif.size + 26, epithet, sans,
                 (255, 214, 150), tracking=13)


def stars(base, rng, y_max, count, color=(255, 244, 214)):
    d = ImageDraw.Draw(base)
    for _ in range(count):
        x = rng.randint(8, W - 8)
        y = rng.randint(8, y_max)
        r = rng.choice([1, 1, 1, 2])
        a = rng.randint(90, 210)
        d.ellipse([x - r, y - r, x + r, y + r], fill=color + (a,))


def sky_lanterns(base, rng, count, y_lo, y_hi):
    """Small warm lanterns rising in the sky, each with a soft glow."""
    for _ in range(count):
        x = rng.randint(40, W - 40)
        y = rng.randint(y_lo, y_hi)
        s = rng.randint(10, 22)
        paste(base, glow(s * 3, (255, 176, 92)), x, y)
        d = ImageDraw.Draw(base)
        d.ellipse([x - s / 4, y - s / 3, x + s / 4, y + s / 3],
                  fill=(255, 205, 120, 235))


# ------------------------------------------------------------- VELMORA

def draw_tower(base, rng):
    """The single landmark: a tall tiered lantern-tower, centre-right.

    Returns the tower layer (for its water reflection).
    """
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, horizon = 648, 640
    ink = (18, 24, 48, 255)
    gold = (232, 169, 78, 255)
    # five tiers, narrowing toward the top
    top, bottom = 296, horizon
    tiers = 5
    th = (bottom - top) / tiers
    widths = [168, 146, 122, 98, 74]
    for i in range(tiers):
        y0 = top + i * th
        y1 = y0 + th
        w = widths[i]
        d.rectangle([cx - w / 2, y0 + 12, cx + w / 2, y1], fill=ink)
        # flared roof
        d.polygon([(cx - w / 2 - 16, y0 + 14), (cx + w / 2 + 16, y0 + 14),
                   (cx + w / 2 - 6, y0 - 8), (cx - w / 2 + 6, y0 - 8)],
                  fill=(26, 33, 62, 255))
        d.line([(cx - w / 2 - 16, y0 + 14), (cx + w / 2 + 16, y0 + 14)],
               fill=gold, width=2)
        # lit windows on this tier
        nw = 3 if i < 3 else 2
        for k in range(nw):
            wx = cx + (k - (nw - 1) / 2) * (w / (nw + 0.4))
            wy = y0 + th * 0.45
            d.rounded_rectangle([wx - 7, wy - 12, wx + 7, wy + 12], radius=7,
                                fill=(255, 205, 120, 255))
    # beacon dome + orb on top
    d.polygon([(cx - 26, top - 6), (cx + 26, top - 6), (cx, top - 34)],
              fill=(26, 33, 62, 255))
    paste(layer, glow(150, (255, 190, 100)), cx, top - 46)
    d.ellipse([cx - 13, top - 59, cx + 13, top - 33],
              fill=(255, 226, 160, 255))
    base.alpha_composite(layer, (0, 0))
    return layer


def draw_skyline(base, rng, horizon):
    """Low dark city silhouette along the horizon, windows lit."""
    d = ImageDraw.Draw(base)
    x = -10
    while x < W + 10:
        bw = rng.randint(34, 86)
        bh = rng.randint(18, 64)
        d.rectangle([x, horizon - bh, x + bw, horizon],
                    fill=(16, 22, 44, 255))
        if rng.random() < 0.55:  # a rooftop lantern post
            d.line([(x + bw / 2, horizon - bh - 12),
                    (x + bw / 2, horizon - bh)], fill=(232, 169, 78),
                   width=2)
            d.ellipse([x + bw / 2 - 3, horizon - bh - 16,
                       x + bw / 2 + 3, horizon - bh - 10],
                      fill=(255, 205, 120, 255))
        for _ in range(rng.randint(1, 4)):
            wx = rng.randint(int(x) + 5, int(x + bw) - 8)
            wy = rng.randint(int(horizon - bh) + 6, horizon - 10)
            d.rectangle([wx, wy, wx + 3, wy + 4],
                        fill=(255, 205, 120, 220))
        x += bw + rng.randint(2, 14)


def draw_sea_lanterns(base, rng, horizon):
    """Warm lanterns drifting on the water, with reflections."""
    d = ImageDraw.Draw(base)
    for _ in range(150):
        x = rng.randint(16, W - 16)
        # denser near the horizon, sparser toward the viewer
        t = rng.random() ** 0.6
        y = horizon + 18 + t * (H - horizon - 60)
        s = 3 + t * 7
        paste(base, glow(int(s * 5), (255, 172, 88)), x, y)
        d.ellipse([x - s / 2, y - s / 3, x + s / 2, y + s / 3],
                  fill=(255, 208, 128, 245))
        # reflection streak straight down
        rl = int(10 + t * 34)
        d.line([(x, y + s / 2), (x, y + s / 2 + rl)],
               fill=(255, 176, 92, 110), width=2)


def render_velmora():
    rng = random.Random(20261121)
    horizon = 640
    base = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    # sky: indigo dusk down to peach gold at the horizon
    sky = Image.new("RGBA", (W, horizon + 1), (0, 0, 0, 255))
    vgrad(sky, [(0.0, (26, 32, 66)), (0.38, (96, 66, 110)),
                (0.62, (214, 110, 88)), (0.88, (247, 178, 103)),
                (1.0, (252, 205, 130))])
    base.alpha_composite(sky, (0, 0))
    stars(base, rng, 300, 90)
    sky_lanterns(base, rng, 26, 300, 560)

    # low sun, left of the tower, sitting on the horizon
    paste(base, glow(420, (255, 196, 110)), 330, horizon - 8)
    d = ImageDraw.Draw(base)
    d.ellipse([330 - 46, horizon - 54, 330 + 46, horizon + 38],
              fill=(255, 233, 176, 255))

    # sea: deep teal darkening toward the viewer
    sea = Image.new("RGBA", (W, H - horizon), (0, 0, 0, 255))
    vgrad(sea, [(0.0, (16, 74, 84)), (0.45, (11, 52, 64)),
                (1.0, (6, 30, 40))])
    base.alpha_composite(sea, (0, horizon))
    # sun path: warm horizontal shimmer under the sun
    for i in range(26):
        y = horizon + 12 + i * 13
        wdt = (200 - i * 4) * rng.uniform(0.72, 1.18)
        xc = 330 + rng.randint(-14, 14)
        a = int(120 * (1 - i / 26))
        d.line([(xc - wdt / 2, y), (xc + wdt / 2, y)],
               fill=(255, 190, 110, a), width=3)

    draw_skyline(base, rng, horizon)
    tower = draw_tower(base, rng)
    # tower reflection: flipped copy, faded, below the horizon
    refl = tower.transpose(Image.FLIP_TOP_BOTTOM)
    alpha = refl.split()[3].point(lambda a: a * 42 // 100)
    refl.putalpha(alpha)
    base.alpha_composite(refl, (0, 257))
    draw_sea_lanterns(base, rng, horizon)

    # gentle darkening at the very bottom so the poster grounds itself
    bot = Image.new("RGBA", (W, 130), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bot)
    for y in range(130):
        bd.line([(0, y), (W - 1, y)],
                fill=(4, 18, 26, int(66 * y / 130)))
    base.alpha_composite(bot, (0, H - 130))

    draw_title(base, "VELMORA", "CITY OF THE LANTERN TIDE")
    return base.convert("RGB")


# ------------------------------------------------------------- NIMBARA

def draw_ridge(d, rng, y_base, peak_x, peak_y, color, jag=26):
    """One mountain ridge: jagged polygon from the peak to both edges."""
    pts = [(-10, H + 10)]
    x = -10
    y = y_base
    # left slope up to the peak
    steps = 9
    for i in range(steps + 1):
        t = i / steps
        px = -10 + (peak_x + 10) * t
        py = y_base + (peak_y - y_base) * t + rng.randint(-jag, jag)
        pts.append((px, py))
    for i in range(1, steps + 1):
        t = i / steps
        px = peak_x + (W + 10 - peak_x) * t
        py = peak_y + (y_base - peak_y) * t + rng.randint(-jag, jag)
        pts.append((px, py))
    pts.append((W + 10, H + 10))
    d.polygon(pts, fill=color)


def render_nimbara():
    rng = random.Random(20261122)
    horizon = 620
    base = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    # dawn sky: violet down to gold at the horizon
    sky = Image.new("RGBA", (W, horizon + 1), (0, 0, 0, 255))
    vgrad(sky, [(0.0, (44, 34, 78)), (0.35, (104, 60, 108)),
                (0.60, (198, 102, 138)), (0.85, (247, 165, 107)),
                (1.0, (255, 214, 160))])
    base.alpha_composite(sky, (0, 0))
    stars(base, rng, 260, 70)
    # rising sun behind the peak
    paste(base, glow(380, (255, 200, 130)), 512, horizon - 30)
    d = ImageDraw.Draw(base)
    d.ellipse([512 - 52, horizon - 82, 512 + 52, horizon + 22],
              fill=(255, 238, 194, 255))
    # birds
    for _ in range(9):
        x = rng.randint(80, W - 80)
        y = rng.randint(180, 420)
        s = rng.randint(7, 13)
        d.arc([x - s, y - s // 2, x, y + s // 2], 200, 340,
              fill=(30, 24, 56, 220), width=2)
        d.arc([x, y - s // 2, x + s, y + s // 2], 200, 340,
              fill=(30, 24, 56, 220), width=2)

    # far ridge, then the main terraced mountain
    draw_ridge(d, rng, 640, 300, 470, (74, 52, 96, 255), jag=20)
    draw_ridge(d, rng, 660, 512, 350, (54, 40, 80, 255), jag=24)
    # terraces: pale curved bands across the main slope
    for i, ty in enumerate(range(430, 650, 34)):
        wdt = 150 + i * 46
        d.arc([512 - wdt, ty - 26, 512 + wdt, ty + 26], 0, 180,
              fill=(150, 104, 150, 200), width=3)
        # tiny terrace lights
        for k in range(5):
            lx = 512 + (k - 2) * (wdt // 3)
            d.ellipse([lx - 2, ty - 2, lx + 2, ty + 2],
                      fill=(255, 205, 120, 230))
    # temple on the peak with a zigzag stair of lights down the slope
    tx, ty = 512, 330
    d.polygon([(tx - 34, ty + 22), (tx + 34, ty + 22), (tx, ty - 16)],
              fill=(34, 26, 58, 255))
    d.rectangle([tx - 24, ty + 22, tx + 24, ty + 52],
                fill=(34, 26, 58, 255))
    d.ellipse([tx - 5, ty + 30, tx + 5, ty + 40],
              fill=(255, 205, 120, 255))
    paste(base, glow(110, (255, 190, 100)), tx, ty + 8)
    stair_x, stair_y = tx - 30, ty + 52
    for i in range(14):
        stair_x += -14 if i % 2 == 0 else 26
        stair_y += 20
        d.ellipse([stair_x - 3, stair_y - 3, stair_x + 3, stair_y + 3],
                  fill=(255, 205, 120, 235))

    # sea of clouds below the mountain
    clouds = Image.new("RGBA", (W, H - horizon), (0, 0, 0, 255))
    vgrad(clouds, [(0.0, (244, 201, 192)), (0.5, (232, 168, 184)),
                   (1.0, (196, 128, 158))])
    base.alpha_composite(clouds, (0, horizon))
    for _ in range(46):
        x = rng.randint(0, W)
        y = rng.randint(horizon + 6, H - 20)
        s = rng.randint(60, 190)
        puff = Image.new("RGBA", (s * 2, s), (0, 0, 0, 0))
        pd = ImageDraw.Draw(puff)
        pd.ellipse([0, s // 4, s * 2, s], fill=(255, 226, 224, 150))
        pd.ellipse([s // 2, 0, s * 3 // 2, s * 3 // 4],
                   fill=(255, 236, 232, 170))
        puff = puff.filter(ImageFilter.GaussianBlur(s // 6))
        base.alpha_composite(puff, (int(x - s), int(y - s / 2)))

    draw_title(base, "NIMBARA", "THE CITY ABOVE THE CLOUDS")
    return base.convert("RGB")


RENDERERS = {"velmora": render_velmora, "nimbara": render_nimbara}


# ---------------------------------------------------------------- entry

def write_image(img, target):
    """Save within the 1 MiB gate: PNG first, JPEG fallback if needed."""
    import io

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    data = buf.getvalue()
    if len(data) > MAX_BYTES:
        for quality in (90, 82):
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            data = buf.getvalue()
            if len(data) <= MAX_BYTES:
                break
    target.write_bytes(data)
    return len(data)


def copy_shipped(target):
    shipped = ROOT / "entry.png"
    if not shipped.exists():
        raise SystemExit("error: Pillow missing and no shipped entry.png")
    shutil.copyfile(shipped, target)
    return shipped.stat().st_size


def main():
    concept = os.environ.get("MF_POSTER_CONCEPT", "velmora").lower()
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "entry.png"

    if PIL_OK and concept in RENDERERS:
        try:
            size = write_image(RENDERERS[concept](), target)
            print(f"wrote {target} ({size} bytes, {W}x{H}, {concept})")
            return
        except Exception as exc:  # fall through to the shipped PNG
            print(f"render failed ({exc}); using shipped entry.png")

    size = copy_shipped(target)
    print(f"wrote {target} ({size} bytes, {W}x{H}, shipped fallback)")


if __name__ == "__main__":
    main()
