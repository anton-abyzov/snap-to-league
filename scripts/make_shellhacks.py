"""ShellHacks 2026 demo photos: the Panther Pit Break Cup (3v3 mini soccer between hacker teams at
FIU's Graham Center), its knockout round a few hours later, and the midnight Smash bracket.

  shellhacks-groups.jpg    whiteboard, Group A and Group B, scorers with minutes
  shellhacks-knockout.jpg  notebook page: semifinals played, final scheduled; one team misspelled
  shellhacks-smash.jpg     paper bracket from the midnight Smash tournament

python scripts/make_shellhacks.py tests/fixtures
"""
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HAND = "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf"
MARKER = "/System/Library/Fonts/Supplemental/Chalkboard.ttc"

GROUP_A = [("Null Pointers", "3", "Rubber Duckies", "1", "Maya 2', 14'  Luis 9'  /  Priya 11'"),
           ("Stack Overflow FC", "2", "Merge Conflicts", "2", "Andre 5', 12'  /  Sofia 3'  Kenji 15'"),
           ("Null Pointers", "1", "Merge Conflicts", "0", "Maya 7'  /"),
           ("Rubber Duckies", "2", "Stack Overflow FC", "4", "Priya 6', Omar 13'  /  Andre 2', 10'  Dani 8', 15'")]
GROUP_B = [("Segfault United", "2", "404 Not Found", "0", "Chloe 4'  Marco 12'  /"),
           ("Git Pushers", "1", "Infinite Loops", "3", "Tomas 9'  /  Aisha 1', 8', 14'"),
           ("Segfault United", "2", "Infinite Loops", "2", "Chloe 6', 11'  /  Aisha 3'  Ravi 13'"),
           ("404 Not Found", "", "Git Pushers", "", "Sat 11:30pm  Panther Pit")]


def rough(img, seed, rot, blur=1.0):
    random.seed(seed)
    np.random.seed(seed)
    img = img.rotate(rot, expand=True, fillcolor=(28, 28, 30)).filter(ImageFilter.GaussianBlur(blur))
    a = np.array(img).astype(float)
    a += np.random.normal(0, 7, a.shape)
    a *= np.linspace(0.8, 1.06, a.shape[1])[None, :, None]
    return Image.fromarray(a.clip(0, 255).astype("uint8"))


def groups(out: Path):
    img = Image.new("RGB", (1900, 1400), (238, 241, 239))
    d = ImageDraw.Draw(img)
    title = ImageFont.truetype(MARKER, 60)
    row = ImageFont.truetype(MARKER, 38)
    note = ImageFont.truetype(HAND, 28)
    d.text((60, 30), "ShellHacks '26  PANTHER PIT BREAK CUP", fill=(10, 45, 130), font=title)
    d.text((60, 105), "3v3 mini soccer  -  16 min games  -  Graham Center", fill=(120, 120, 120), font=note)
    x = 60
    for label, rows, colour in (("GROUP A", GROUP_A, (170, 25, 30)), ("GROUP B", GROUP_B, (20, 110, 60))):
        y = 175
        d.text((x, y), label, fill=colour, font=row)
        d.line((x, y + 50, x + 820, y + 53), fill=colour, width=4)
        y += 80
        for h, hs, a, as_, sc in rows:
            s = f"{hs}-{as_}" if hs else "v"
            d.text((x + random.randint(-5, 5), y), f"{h} {s} {a}", fill=(25, 25, 35), font=row)
            y += 52
            d.text((x + 28, y), sc, fill=(80, 80, 110) if hs else (20, 110, 60), font=note)
            y += 70
        x += 920
    d.text((60, 1300), "top 2 -> semis 1am   (winner gets the last Monster)", fill=(90, 90, 90), font=note)
    rough(img, 41, 1.8).save(out / "shellhacks-groups.jpg", quality=74)


def knockout(out: Path):
    img = Image.new("RGB", (1300, 1500), (251, 249, 240))
    d = ImageDraw.Draw(img)
    for y in range(170, 1500, 64):
        d.line((0, y, 1300, y), fill=(188, 204, 230), width=2)
    d.line((100, 0, 100, 1500), fill=(230, 160, 160), width=3)
    t = ImageFont.truetype(HAND, 54)
    m = ImageFont.truetype(HAND, 44)
    s = ImageFont.truetype(HAND, 34)
    d.text((130, 60), "Break Cup  -  KNOCKOUTS", fill=(20, 40, 120), font=t)
    y = 200
    for line, sub in [("SEMI 1:  Null Pointers  2 - 3  Segfault United", "Maya 4', 10'  /  Chloe 2', 9', 15'"),
                      ("SEMI 2:  Infinite Loops  1 - 0  Stack Overflow", "Aisha 13'"),
                      ("FINAL:  Infinite Loops  v  Segfault Utd", "Sun 1:30am  Panther Pit"),
                      ("3rd place:  Null Pointers  v  Stack Overflow FC", "Sun 1:10am")]:
        d.text((130 + random.randint(-6, 6), y), line, fill=(25, 25, 30), font=m)
        y += 64
        d.text((190, y), sub, fill=(130, 30, 30) if "'" in sub else (30, 110, 60), font=s)
        y += 128
    d.text((130, y + 20), "Rubber Duckys + Merge Conflicts + 404 + Git Pushers out", fill=(110, 110, 110), font=s)
    rough(img, 57, -2.4).save(out / "shellhacks-knockout.jpg", quality=74)


def smash(out: Path):
    img = Image.new("RGB", (1700, 1150), (239, 240, 236))
    d = ImageDraw.Draw(img)
    f = lambda n: ImageFont.truetype(HAND, n)
    ink, red = (25, 30, 60), (170, 25, 25)
    d.text((60, 25), "Midnight Smash  -  ShellHacks", fill=(20, 40, 120), font=f(56))
    d.text((1160, 40), "bo3  -  Room 140", fill=(90, 90, 90), font=f(34))

    def slot(x, y, name, score=None):
        d.text((x, y - 42), name, fill=ink, font=f(38))
        d.line((x - 5, y, x + 280, y + random.randint(-3, 3)), fill=ink, width=3)
        if score is not None:
            d.text((x + 235, y - 44), score, fill=red, font=f(38))

    qf = [("PantherByte", "2", "xX_Shell_Xx", "0"), ("Mentor Mike", "1", "CtrlAltDefeat", "2"),
          ("RoaringRoux", "2", "Kirby404", "1"), ("SegFaulted", "0", "INIT_Ness", "2")]
    ys = [200, 300, 420, 520, 640, 740, 860, 960]
    for i, (a, sa, b, sb) in enumerate(qf):
        slot(60, ys[2 * i], a, sa)
        slot(60, ys[2 * i + 1], b, sb)
        d.line((345, ys[2 * i], 345, ys[2 * i + 1]), fill=ink, width=3)
    sy = [(ys[0] + ys[1]) // 2 + 60, (ys[2] + ys[3]) // 2 + 60, (ys[4] + ys[5]) // 2 + 60, (ys[6] + ys[7]) // 2 + 60]
    for i, (a, sa, b, sb) in enumerate([("PantherByte", "2", "CtrlAltDefeat", "1"), ("RoaringRoux", "1", "INIT_Ness", "2")]):
        slot(410, sy[2 * i], a, sa)
        slot(410, sy[2 * i + 1], b, sb)
        d.line((695, sy[2 * i], 695, sy[2 * i + 1]), fill=ink, width=3)
    fy = [(sy[0] + sy[1]) // 2 + 40, (sy[2] + sy[3]) // 2 + 40]
    slot(760, fy[0], "PantherByte")
    slot(760, fy[1], "INIT_Ness")
    d.line((1045, fy[0], 1045, fy[1]), fill=ink, width=3)
    d.text((1090, (fy[0] + fy[1]) // 2 - 30), "GRAND FINAL  2:15am", fill=(20, 90, 40), font=f(34))
    rough(img, 63, -2.8, 1.1).save(out / "shellhacks-smash.jpg", quality=72)


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    groups(folder)
    knockout(folder)
    smash(folder)
