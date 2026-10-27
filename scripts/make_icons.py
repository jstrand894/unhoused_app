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

from PIL import Image, ImageDraw, ImageFilter

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
    """Flat app icon: a white tent with a door on a plain blue rounded square. No gradients or shadows."""
    n = size * 2                                   # draw at 2x, downscale for smooth edges
    m = int(n * 0.098)                             # macOS icon grid: ~824/1024 body
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([m, m, n - m, n - m], radius=int(n * 0.185), fill=BLUE)
    d.polygon([(n * 0.50, n * 0.28), (n * 0.22, n * 0.70), (n * 0.78, n * 0.70)], fill="white")
    d.polygon([(n * 0.50, n * 0.45), (n * 0.41, n * 0.70), (n * 0.59, n * 0.70)], fill=BLUE)
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
