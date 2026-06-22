#!/usr/bin/env python3
"""Build a 1280x800 Chrome Web Store promo tile."""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "store")
os.makedirs(OUT, exist_ok=True)

W, H = 1280, 800
img = Image.new("RGB", (W, H), "#EEF1FB")
d = ImageDraw.Draw(img)

# soft top band
d.rectangle([0, 0, W, 260], fill="#3483FA")


def font(sz, bold=False):
    for p in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


# big icon, left
icon = Image.open(os.path.join(ROOT, "icons", "icon128.png")).convert("RGBA").resize((240, 240))
img.paste(icon, (90, 120), icon)

# title + tagline
d.text((360, 150), "MeLi Local Delivery", font=font(56, bold=True), fill="#FFFFFF")
d.text((362, 300), "Solo envíos desde Argentina.", font=font(34, bold=True), fill="#2D3277")
d.text((362, 352), "Aplica el filtro “Origen del envío: Local”", font=font(30), fill="#444")
d.text((362, 394), "en cada búsqueda, automáticamente.", font=font(30), fill="#444")
d.text((362, 470), "Sin demoras de aduana ni envíos internacionales.", font=font(24), fill="#777")

# popup screenshot bottom-right with shadow
shot = Image.open(os.path.join(ROOT, "popup-shot.png")).convert("RGBA")
sw = 360
sh = int(shot.height * sw / shot.width)
shot = shot.resize((sw, sh))
px, py = W - sw - 110, H - sh - 90
d.rectangle([px + 8, py + 10, px + sw + 8, py + sh + 10], fill="#D5DAEC")  # shadow
img.paste(shot, (px, py), shot)

img.save(os.path.join(OUT, "promo-1280x800.png"))
print("wrote", os.path.join(OUT, "promo-1280x800.png"))
