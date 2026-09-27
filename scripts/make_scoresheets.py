"""Two handwritten scoresheets from the same futsal league, taken a week apart, for testing
multi-photo import: scorers, a misspelled team ("Sharcs") and a game that gets its result later.

python scripts/make_scoresheets.py tests/fixtures
"""
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf"
SHEETS = {
    "sheet1": ("Sunday Futsal League - Week 3", [
        ("Lions", "3", "Sharks", "1", "Diaz 2, Kim  /  Lee"),
        ("Hawks", "2", "Wolves", "2", "Ortega, Brooks  /  Nakamura 2"),
        ("Lions", "", "Hawks", "", "Sun 7pm  Court 2"),
    ]),
    "sheet2": ("Sunday Futsal - Week 4", [
        ("Lions", "3", "Sharks", "1", "Diaz 2, Kim  /  Lee"),
        ("Lions", "0", "Hawks", "1", "  /  Ortega"),
        ("Sharcs", "4", "Wolves", "2", "Lee 3, Patel  /  Nakamura, Reyes"),
    ]),
}


def draw(title, rows, out, seed):
    random.seed(seed)
    np.random.seed(seed)
    img = Image.new("RGB", (1500, 1100), (246, 243, 232))
    d = ImageDraw.Draw(img)
    font = lambda s: ImageFont.truetype(FONT, s)
    for y in range(160, 1100, 62):  # ruled paper
        d.line((0, y, 1500, y), fill=(190, 205, 230), width=2)
    d.line((110, 0, 110, 1100), fill=(230, 160, 160), width=3)
    d.text((140, 50), title, fill=(25, 45, 120), font=font(56))
    y = 190
    for h, hs, a, as_, note in rows:
        x = 140 + random.randint(-8, 8)
        score = f"{hs} - {as_}" if hs else "  v  "
        d.text((x, y), f"{h}   {score}   {a}", fill=(20, 20, 30), font=font(48))
        y += 70
        d.text((x + 40, y), ("Goals: " if hs else "") + note, fill=(120, 30, 30) if hs else (30, 110, 60), font=font(36))
        y += 110
    img = img.rotate(random.choice([-3, 2.5]), expand=True, fillcolor=(35, 35, 35)).filter(ImageFilter.GaussianBlur(1.0))
    a = np.array(img).astype(float)
    a += np.random.normal(0, 7, a.shape)
    a *= np.linspace(0.8, 1.05, a.shape[1])[None, :, None]
    Image.fromarray(a.clip(0, 255).astype("uint8")).save(out, quality=74)


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    for i, (name, (title, rows)) in enumerate(SHEETS.items()):
        draw(title, rows, folder / f"{name}.jpg", 11 + i)
