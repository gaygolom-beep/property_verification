"""
Generates 5 simple, license-free illustrated property images (not real
photos) for the demo slideshow, using only PIL primitives -- no external
image downloads, so there's no attribution/copyright concern.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "demo_photos")
W, H = 900, 600


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky_gradient(draw, top, bottom):
    for y in range(H):
        t = y / H
        draw.line([(0, y), (W, y)], fill=lerp(top, bottom, t))


def sun(draw, cx, cy, r, color):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def ground(draw, y0, color):
    draw.rectangle([0, y0, W, H], fill=color)


def house(draw, x, y, w, h, wall, roof, door, n_windows=2):
    draw.rectangle([x, y, x + w, y + h], fill=wall)
    draw.polygon([(x - 15, y), (x + w // 2, y - h * 0.45), (x + w + 15, y)], fill=roof)
    dw, dh = w * 0.16, h * 0.4
    draw.rectangle([x + w / 2 - dw / 2, y + h - dh, x + w / 2 + dw / 2, y + h], fill=door)
    win_w, win_h = w * 0.14, h * 0.18
    gap = w / (n_windows + 1)
    for i in range(n_windows):
        wx = x + gap * (i + 1) - win_w / 2
        if abs(wx - (x + w / 2 - dw / 2)) < win_w:
            continue
        wy = y + h * 0.2
        draw.rectangle([wx, wy, wx + win_w, wy + win_h], fill="#eaf4fb")
        draw.line([(wx, wy + win_h / 2), (wx + win_w, wy + win_h / 2)], fill="#7b8a99", width=2)
        draw.line([(wx + win_w / 2, wy), (wx + win_w / 2, wy + win_h)], fill="#7b8a99", width=2)


def tree(draw, x, y, scale=1.0):
    trunk_w, trunk_h = 10 * scale, 40 * scale
    draw.rectangle([x - trunk_w / 2, y - trunk_h, x + trunk_w / 2, y], fill="#6b4a34")
    for dx, dy, r in [(0, -trunk_h - 10, 32), (-20, -trunk_h + 5, 24), (20, -trunk_h + 5, 24)]:
        rr = r * scale
        draw.ellipse([x + dx - rr, y + dy - rr, x + dx + rr, y + dy + rr], fill="#3f8c5a")


def cloud(draw, x, y, scale=1.0):
    for dx, dy, r in [(0, 0, 26), (22, 4, 20), (-22, 4, 20), (10, -10, 18), (-10, -10, 18)]:
        rr = r * scale
        draw.ellipse([x + dx - rr, y + dy - rr, x + dx + rr, y + dy + rr], fill="#ffffff")


def scene_villa():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    sky_gradient(d, (255, 214, 153), (255, 154, 139))
    cloud(d, 150, 90, 1.1); cloud(d, 700, 60, 0.9)
    ground(d, 430, "#8bc78e")
    for x in range(-50, W + 50, 40):
        tree(d, x, 440, 0.5) if x % 80 == 0 else None
    house(d, 300, 320, 340, 170, "#f5efe6", "#b5533f", "#5a3d2b", n_windows=3)
    tree(d, 120, 470, 1.3); tree(d, 800, 460, 1.1)
    img = img.filter(ImageFilter.SMOOTH)
    return img, "Modern Villa"


def scene_apartments():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    sky_gradient(d, (183, 222, 232), (232, 244, 240))
    cloud(d, 200, 80, 1.0); cloud(d, 650, 110, 0.8)
    ground(d, 470, "#cfd8d1")
    colors = ["#e8ede9", "#dfe6e0", "#e3e9e4"]
    for i, x in enumerate(range(60, W - 60, 170)):
        h = 260 + (i % 3) * 30
        y = 470 - h
        d.rectangle([x, y, x + 140, 470], fill=colors[i % 3])
        for row in range(int(h // 45)):
            for col in range(3):
                wx = x + 15 + col * 40
                wy = y + 15 + row * 45
                d.rectangle([wx, wy, wx + 26, wy + 26], fill="#8fb4d1")
    img = img.filter(ImageFilter.SMOOTH)
    return img, "Apartment Complex"


def scene_farmland():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    sky_gradient(d, (168, 214, 234), (235, 245, 220))
    sun(d, 750, 90, 46, "#ffe08a")
    cloud(d, 180, 70, 1.0)
    ground(d, 360, "#d9c96a")
    for row in range(360, H, 18):
        shade = "#c8b955" if (row // 18) % 2 == 0 else "#d9c96a"
        d.line([(0, row), (W, row)], fill=shade, width=9)
    for x in range(40, W, 90):
        tree(d, x, 380, 0.6)
    img = img.filter(ImageFilter.SMOOTH)
    return img, "Farmland Plot"


def scene_bungalow():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    sky_gradient(d, (255, 195, 160), (255, 230, 190))
    sun(d, 130, 100, 50, "#ffd27a")
    ground(d, 420, "#9ac98f")
    house(d, 260, 330, 300, 140, "#f2d9b8", "#6b4a34", "#4a3221", n_windows=2)
    tree(d, 100, 460, 1.2); tree(d, 780, 450, 1.0); tree(d, 650, 470, 0.8)
    img = img.filter(ImageFilter.SMOOTH)
    return img, "Bungalow"


def scene_interior():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 380], fill="#f4ede1")
    d.rectangle([0, 380, W, H], fill="#c9a876")
    for x in range(0, W, 60):
        d.line([(x, 380), (x, H)], fill="#b8944f", width=2)
    d.rectangle([120, 120, 380, 340], fill="#bcdcec")
    d.line([(250, 120), (250, 340)], fill="#8fa6b3", width=4)
    d.line([(120, 230), (380, 230)], fill="#8fa6b3", width=4)
    d.rectangle([520, 260, 760, 420], fill="#8a6f56")
    d.rectangle([540, 220, 620, 260], fill="#a9866a")
    d.ellipse([600, 60, 660, 120], fill="#f9e79b")
    img = img.filter(ImageFilter.SMOOTH)
    return img, "Living Room Interior"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    scenes = [scene_villa(), scene_apartments(), scene_farmland(), scene_bungalow(), scene_interior()]
    for i, (img, caption) in enumerate(scenes, 1):
        path = os.path.join(OUT_DIR, f"demo_{i}.jpg")
        img.save(path, quality=88)
        print(f"Wrote {path} ({caption})")


if __name__ == "__main__":
    main()
