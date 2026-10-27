"""Generate the glow images for the connection light (hobo/assets/halo_*.png) and the app icon.

Button icons and the lamp itself are vector drawings in hobo/widgets.py, so they stay sharp on Retina.

Dev-time only; needs Pillow. The generated files are committed, so users don't need to run this.
Run from the project folder:  .venv/bin/python scripts/make_icons.py
"""
import math
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "hobo", "assets")
BLUE, RED, GREEN, GRAY = "#2e86ab", "#d1495b", "#3a9d5d", "#555555"
S = 8  # supersampling factor for smooth edges


def halo(rgb, strength, size=44):
    """Soft coloured glow with a transparent background (blurred, so low resolution is invisible)."""
    n = size * 2
    img = Image.new("RGBA", (n, n), rgb + (0,))
    d = ImageDraw.Draw(img)
    r = n * 0.20
    c = n / 2
    d.ellipse([c - r, c - r, c + r, c + r], fill=rgb + (int(255 * strength),))
    img = img.filter(ImageFilter.GaussianBlur(n * 0.06))
    core = Image.new("RGBA", (n, n), rgb + (0,))
    ImageDraw.Draw(core).ellipse([c - r * .75, c - r * .75, c + r * .75, c + r * .75], fill=rgb + (int(150 * strength),))
    img = Image.alpha_composite(img, core.filter(ImageFilter.GaussianBlur(n * 0.04)))
    return img.resize((size, size), Image.LANCZOS)


def app_icon(size=1024):
    """Blue squircle with one smooth data trace, a soft fill under it and a green 'live' marker at the end."""
    n = size * 2                                   # draw at 2x, downscale for smooth edges
    m = int(n * 0.098)                             # macOS icon grid: ~824/1024 body
    box = [m, m, n - m, n - m]
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    grad = Image.new("RGBA", (n, n))
    gd = ImageDraw.Draw(grad)
    top, bot = (52, 150, 190), (18, 52, 96)
    for y in range(n):
        t = y / n
        gd.line([(0, y), (n, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,))
    mask = Image.new("L", (n, n), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=int(n * 0.185), fill=255)
    img.paste(grad, (0, 0), mask)

    # faint grid lines
    grid = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for f in (0.34, 0.50, 0.66):
        gd.line([(n * 0.25, n * f), (n * 0.75, n * f)], fill=(255, 255, 255, 36), width=int(n * 0.008))
    img = Image.alpha_composite(img, grid)

    # the trace: one gentle rise, dip and climb
    x0, x1 = n * 0.24, n * 0.76
    pts = []
    for i in range(1201):
        t = i / 1200
        y = n * (0.54 - 0.15 * math.sin(t * 2 * math.pi * 1.0 - 0.6) - 0.045 * math.sin(t * 2 * math.pi * 2.2))
        pts.append((x0 + (x1 - x0) * t, y))

    # soft fill under the line, fading downward
    floor = n * 0.70
    fill_mask = Image.new("L", (n, n), 0)
    ImageDraw.Draw(fill_mask).polygon(pts + [(x1, floor), (x0, floor)], fill=255)
    fade = Image.new("L", (n, n), 0)
    fd = ImageDraw.Draw(fade)
    for y in range(int(n * 0.30), int(floor)):
        fd.line([(0, y), (n, y)], fill=int(110 * (1 - (y - n * 0.30) / (floor - n * 0.30))))
    fill_a = ImageChops.multiply(fill_mask, fade)
    fill_img = Image.new("RGBA", (n, n), (255, 255, 255, 0))
    fill_img.putalpha(fill_a)
    img = Image.alpha_composite(img, fill_img)

    # drop shadow, then the line itself
    w = int(n * 0.050)
    shadow = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for x, y in pts:
        sd.ellipse([x - w / 2, y + n * 0.012 - w / 2, x + w / 2, y + n * 0.012 + w / 2], fill=(5, 25, 50, 110))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(n * 0.012)))
    d = ImageDraw.Draw(img)
    for x, y in pts:                               # stamped circles give a clean, round-capped stroke
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill="white")

    # live marker on the last reading: glow, white ring, green core
    ex, ey = pts[-1]
    glow = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    gr = n * 0.095
    ImageDraw.Draw(glow).ellipse([ex - gr, ey - gr, ex + gr, ey + gr], fill=(76, 217, 100, 150))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(n * 0.03)))
    d = ImageDraw.Draw(img)
    r = n * 0.062
    d.ellipse([ex - r, ey - r, ex + r, ey + r], fill="white")
    r2 = r * 0.68
    d.ellipse([ex - r2, ey - r2, ex + r2, ey + r2], fill="#35c759")
    return img.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(ASSETS, exist_ok=True)
    green, amber = (40, 215, 80), (255, 159, 10)
    frames = 20                                              # frames for a smooth, gentle pulse
    for i in range(frames):
        st = 0.62 + 0.14 * math.sin(2 * math.pi * i / frames)   # 0.48 .. 0.76: a slow, subtle swell
        halo(green, st).save(os.path.join(ASSETS, f"halo_ok_{i:02d}.png"))
    halo(amber, 0.5).save(os.path.join(ASSETS, "halo_detected.png"))
    big = app_icon(1024)
    big.resize((256, 256), Image.LANCZOS).save(os.path.join(ASSETS, "app.png"))
    tmp = tempfile.mkdtemp(suffix=".iconset")
    for sz in (16, 32, 128, 256, 512):
        big.resize((sz, sz), Image.LANCZOS).save(os.path.join(tmp, f"icon_{sz}x{sz}.png"))
        big.resize((sz * 2, sz * 2), Image.LANCZOS).save(os.path.join(tmp, f"icon_{sz}x{sz}@2x.png"))
    out = os.path.join(ROOT, "assets")
    os.makedirs(out, exist_ok=True)
    subprocess.run(["iconutil", "-c", "icns", tmp, "-o", os.path.join(out, "app.icns")], check=True)
    shutil.rmtree(tmp)
    print("wrote icons to", ASSETS, "and", out)


if __name__ == "__main__":
    main()
