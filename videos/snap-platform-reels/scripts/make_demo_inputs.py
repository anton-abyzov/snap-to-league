"""Synthetic demo inputs for the platform reels. Every image says DEMO DATA on it.

  hoops-bracket.jpg      3x3 basketball knockout drawn on a whiteboard, final played
  padel-ladder.jpg       padel doubles ladder on a lined notebook page
  smash-screenshot.png   phone screenshot of a generic, unbranded bracket app

python scripts/make_demo_inputs.py assets/synthetic
Style follows snap-to-league/scripts/make_shellhacks.py (same fonts and photo roughening).
"""
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HAND = "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf"
MARKER = "/System/Library/Fonts/Supplemental/Chalkboard.ttc"
SANS = "/System/Library/Fonts/SFNS.ttf"


def rough(img, seed, rot, blur=1.0):
    random.seed(seed)
    np.random.seed(seed)
    img = img.rotate(rot, expand=True, fillcolor=(34, 34, 38)).filter(ImageFilter.GaussianBlur(blur))
    a = np.array(img).astype(float)
    a += np.random.normal(0, 7, a.shape)
    a *= np.linspace(0.82, 1.05, a.shape[1])[None, :, None]
    return Image.fromarray(a.clip(0, 255).astype("uint8"))


def hoops_bracket(out: Path):
    random.seed(11)
    img = Image.new("RGB", (1960, 1240), (240, 242, 243))
    d = ImageDraw.Draw(img)
    f = lambda n: ImageFont.truetype(MARKER, n)
    h = lambda n: ImageFont.truetype(HAND, n)
    ink, red, blue, green = (28, 30, 44), (190, 40, 30), (25, 50, 140), (20, 110, 60)
    d.text((60, 30), "3x3 HOOPS NIGHT  -  BRACKET", fill=(210, 90, 15), font=f(62))
    d.text((64, 108), "first to 21  -  court 1  -  demo data", fill=(120, 120, 120), font=h(32))

    def slot(x, y, name, score=None, w=370):
        d.text((x, y - 50), name, fill=ink, font=f(40))
        d.line((x - 6, y, x + w, y + random.randint(-3, 3)), fill=blue, width=4)
        if score is not None:
            d.text((x + w - 58, y - 52), score, fill=red, font=f(42))

    qf = [("Rim Runners", "21", "Alley Cats", "14"), ("Net Profit", "18", "Glass Cleaners", "21"),
          ("Buzzer Beaters", "21", "Pick & Roll", "19"), ("Fast Breaks", "12", "Court Jesters", "21")]
    ys = [240, 340, 470, 570, 700, 800, 930, 1030]
    for i, (a, sa, b, sb) in enumerate(qf):
        slot(70, ys[2 * i], a, sa)
        slot(70, ys[2 * i + 1], b, sb)
        d.line((440, ys[2 * i], 440, ys[2 * i + 1]), fill=blue, width=4)
    sy = [(ys[0] + ys[1]) // 2 + 60, (ys[2] + ys[3]) // 2 + 60, (ys[4] + ys[5]) // 2 + 60, (ys[6] + ys[7]) // 2 + 60]
    for i, (a, sa, b, sb) in enumerate([("Rim Runners", "21", "Glass Cleaners", "16"),
                                        ("Buzzer Beaters", "20", "Court Jesters", "22")]):
        slot(510, sy[2 * i], a, sa)
        slot(510, sy[2 * i + 1], b, sb)
        d.line((880, sy[2 * i], 880, sy[2 * i + 1]), fill=blue, width=4)
    fy = [(sy[0] + sy[1]) // 2 + 40, (sy[2] + sy[3]) // 2 + 40]
    slot(950, fy[0], "Rim Runners", "21")
    slot(950, fy[1], "Court Jesters", "17")
    d.line((1320, fy[0], 1320, fy[1]), fill=blue, width=4)
    mid = (fy[0] + fy[1]) // 2
    d.line((1320, mid, 1640, mid + 3), fill=blue, width=4)
    d.text((1360, mid - 120), "FINAL", fill=green, font=f(44))
    d.text((1355, mid - 58), "Rim Runners", fill=ink, font=f(42))
    d.text((1370, mid + 22), "CHAMPS!", fill=red, font=h(40))
    rough(img, 25, 1.6).save(out / "hoops-bracket.jpg", quality=76)


def padel_ladder(out: Path):
    random.seed(23)
    img = Image.new("RGB", (1400, 1560), (251, 250, 243))
    d = ImageDraw.Draw(img)
    for y in range(190, 1560, 70):
        d.line((0, y, 1400, y), fill=(186, 203, 228), width=2)
    d.line((110, 0, 110, 1560), fill=(232, 158, 158), width=3)
    t, m, s = ImageFont.truetype(HAND, 60), ImageFont.truetype(HAND, 46), ImageFont.truetype(HAND, 32)
    d.text((140, 55), "Thursday PADEL Ladder", fill=(20, 45, 125), font=t)
    d.text((142, 130), "court 3  -  one set each  -  demo data", fill=(120, 120, 120), font=s)
    games = [("Ana / Leo", "6-3", "Sam / Kim"), ("Rui / Mia", "4-6", "Tom / Eva"),
             ("Ana / Leo", "6-4", "Rui / Mia"), ("Sam / Kim", "7-5", "Tom / Eva"),
             ("Ana / Leo", "5-7", "Tom / Eva"), ("Sam / Kim", "6-2", "Rui / Mia")]
    y = 215
    for a, sc, b in games:
        x = 150 + random.randint(-8, 8)
        d.text((x, y), a, fill=(25, 25, 32), font=m)
        d.text((x + 420, y + random.randint(-4, 4)), sc, fill=(170, 25, 25), font=m)
        d.text((x + 600, y), b, fill=(25, 25, 32), font=m)
        y += 140
    d.text((150, y + 20), "next Thu: top pair moves up a court", fill=(30, 110, 60), font=s)
    rough(img, 35, -2.2).save(out / "padel-ladder.jpg", quality=76)


def smash_screenshot(out: Path):
    """Generic dark bracket-app screenshot, 1170x2532 (phone). No real app name or logo."""
    W, H = 1170, 2532
    img = Image.new("RGB", (W, H), (17, 19, 28))
    d = ImageDraw.Draw(img)
    f = lambda n: ImageFont.truetype(SANS, n)
    white, mute, accent, win = (238, 240, 246), (138, 144, 166), (255, 120, 80), (120, 220, 160)
    d.text((70, 48), "9:45", fill=white, font=f(46))
    d.rounded_rectangle((980, 58, 1090, 96), 10, outline=white, width=3)
    d.rectangle((988, 66, 1060, 88), fill=white)
    d.text((70, 190), "Friday Smash Night", fill=white, font=f(74))
    d.text((72, 285), "Top 8  ·  Single elimination  ·  Demo data", fill=mute, font=f(38))
    tabs = ["Bracket", "Players", "Info"]
    x = 70
    for i, tb in enumerate(tabs):
        d.text((x, 380), tb, fill=white if i == 0 else mute, font=f(40))
        if i == 0:
            d.rectangle((x, 440, x + 150, 446), fill=accent)
        x += 260
    d.line((0, 470, W, 470), fill=(40, 44, 60), width=2)

    def card(y, round_name, a, sa, b, sb):
        d.text((70, y), round_name.upper(), fill=mute, font=f(32))
        y += 56
        d.rounded_rectangle((70, y, W - 70, y + 176), 26, fill=(29, 32, 45))
        for j, (name, score) in enumerate(((a, sa), (b, sb))):
            yy = y + 22 + j * 82
            won = int(score) > int(sa if j else sb)
            d.text((110, yy), name, fill=white if won else mute, font=f(48))
            d.text((W - 160, yy), score, fill=win if won else mute, font=f(52))
        d.line((110, y + 90, W - 110, y + 90), fill=(46, 50, 68), width=2)
        return y + 210

    y = 520
    rows = [("Quarterfinal 1", "Vexx", "2", "Mako", "0"), ("Quarterfinal 2", "Juno", "2", "Pixelhart", "1"),
            ("Quarterfinal 3", "Orbit", "1", "Tanuki", "2"), ("Quarterfinal 4", "Ferro", "2", "Lumi", "1"),
            ("Semifinal 1", "Vexx", "2", "Juno", "1"), ("Semifinal 2", "Tanuki", "0", "Ferro", "2"),
            ("Grand final", "Vexx", "3", "Ferro", "1")]
    for r in rows:
        y = card(y, *r)
        if y > H - 120:
            break
    img.save(out / "smash-screenshot.png")


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    folder.mkdir(parents=True, exist_ok=True)
    hoops_bracket(folder)
    padel_ladder(folder)
    smash_screenshot(folder)
