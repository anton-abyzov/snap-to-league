"""Two more handwritten samples with scorers and goal minutes:

  groups.jpg     a futsal tournament board with Group A and Group B, scorers and minutes
  matchcard.jpg  one referee match card: final score, scorers with minutes

python scripts/make_groups.py tests/fixtures
"""
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HAND = "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf"
MARKER = "/System/Library/Fonts/Supplemental/Chalkboard.ttc"

GROUPS = {
    "A": [("Miami Heatwave", "3", "Doral United", "1", "Rivera 4', 31'  Chen 18'  /  Okafor 40'"),
          ("Coral Kings", "2", "Little Havana", "2", "Mejia 9', Mejia 27'  /  Santos 12', Diaz 38'"),
          ("Miami Heatwave", "1", "Coral Kings", "0", "Rivera 22'  /")],
    "B": [("Brickell FC", "0", "Wynwood Wolves", "4", "/  Park 3', 17', 29'  Lopez 35'"),
          ("Hialeah Hawks", "2", "Kendall Stars", "1", "Ortiz 11', Ruiz 30'  /  Adams 25'"),
          ("Brickell FC", "", "Hialeah Hawks", "", "Sat 6pm  Court 1")],
}


def noisy(img, seed, rot):
    random.seed(seed)
    np.random.seed(seed)
    img = img.rotate(rot, expand=True, fillcolor=(30, 30, 30)).filter(ImageFilter.GaussianBlur(1.0))
    a = np.array(img).astype(float)
    a += np.random.normal(0, 7, a.shape)
    a *= np.linspace(0.82, 1.05, a.shape[1])[None, :, None]
    return Image.fromarray(a.clip(0, 255).astype("uint8"))


def groups(out: Path):
    img = Image.new("RGB", (1700, 1300), (240, 242, 238))  # whiteboard
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(MARKER, 58)
    mid = ImageFont.truetype(MARKER, 40)
    small = ImageFont.truetype(HAND, 30)
    d.text((70, 40), "Miami Rec Futsal Cup", fill=(20, 40, 140), font=big)
    x = 70
    for g, rows in GROUPS.items():
        y = 150
        d.text((x, y), f"GROUP {g}", fill=(170, 30, 30), font=mid)
        d.line((x, y + 55, x + 700, y + 58), fill=(170, 30, 30), width=4)
        y += 90
        for h, hs, a, as_, note in rows:
            score = f"{hs}-{as_}" if hs else "v"
            d.text((x + random.randint(-6, 6), y), f"{h} {score} {a}", fill=(25, 25, 35), font=mid)
            y += 58
            d.text((x + 30, y), note, fill=(40, 100, 60) if not hs else (90, 90, 110), font=small)
            y += 88
        x += 820
    d.text((70, 1180), "top 2 each group -> semis Sunday", fill=(90, 90, 90), font=small)
    noisy(img, 21, 2.2).save(out / "groups.jpg", quality=74)


def matchcard(out: Path):
    img = Image.new("RGB", (1200, 1500), (250, 247, 236))
    d = ImageDraw.Draw(img)
    t = ImageFont.truetype(HAND, 50)
    m = ImageFont.truetype(HAND, 42)
    lines = [(80, 60, "MATCH CARD  -  U14 Spring League", t, (20, 40, 110)),
             (80, 150, "Round 6   Field 3   Sat 10:00", m, (60, 60, 60))]
    for x, y, s, f, c in lines:
        d.text((x, y), s, fill=c, font=f)
    d.rectangle((80, 250, 1120, 420), outline=(40, 40, 40), width=3)
    d.text((110, 290), "Palmetto Rays   3  -  2   Pinecrest SC", fill=(20, 20, 20), font=t)
    y = 480
    d.text((80, y), "Goals (home):", fill=(20, 20, 20), font=m)
    for s in ["#9  J. Alvarez  7'", "#9  J. Alvarez  55'", "#11 M. Brooks  38'"]:
        y += 62
        d.text((140, y), s, fill=(30, 30, 90), font=m)
    y += 100
    d.text((80, y), "Goals (away):", fill=(20, 20, 20), font=m)
    for s in ["#7  T. Nguyen  21'", "#10 R. Castillo 64'"]:
        y += 62
        d.text((140, y), s, fill=(30, 30, 90), font=m)
    y += 120
    d.text((80, y), "Referee: K. Moss", fill=(90, 90, 90), font=m)
    noisy(img, 33, -2).save(out / "matchcard.jpg", quality=74)


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    groups(folder)
    matchcard(folder)
