"""Draw a messy handwritten 8-player bracket for testing: python scripts/make_bracket.py out.jpg

Quarterfinals and semifinals are played (winner written in the next round, games won beside
each name); the final is not played yet.
"""
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf"
QF = [("Kirbo", "2", "NeoZ", "0"), ("Pika_Pal", "1", "Marth4", "2"),
      ("Shellby", "2", "Byte", "1"), ("Lumen", "0", "Ganonz", "2")]
SF = [("Kirbo", "2", "Marth4", "1"), ("Shellby", "1", "Ganonz", "2")]
FINAL = ("Kirbo", "Ganonz")


def main(out: str, seed: int = 5) -> None:
    random.seed(seed)
    np.random.seed(seed)
    img = Image.new("RGB", (1600, 1100), (238, 240, 236))
    d = ImageDraw.Draw(img)
    font = lambda s: ImageFont.truetype(FONT, s)
    ink, red = (25, 30, 60), (170, 25, 25)
    d.text((60, 25), "Smash Night Bracket", fill=(20, 40, 120), font=font(58))
    d.text((1080, 45), "best of 3", fill=(90, 90, 90), font=font(34))

    def slot(x, y, name, score=None):
        d.text((x, y - 42), name, fill=ink, font=font(40))
        d.line((x - 5, y, x + 260, y + random.randint(-3, 3)), fill=ink, width=3)
        if score is not None:
            d.text((x + 215, y - 44), score, fill=red, font=font(40))

    ys = [200, 300, 420, 520, 640, 740, 860, 960]
    for i, (a, sa, b, sb) in enumerate(QF):
        slot(60, ys[2 * i], a, sa)
        slot(60, ys[2 * i + 1], b, sb)
        d.line((320, ys[2 * i], 320, ys[2 * i + 1]), fill=ink, width=3)
    sf_y = [(ys[0] + ys[1]) // 2 + 60, (ys[2] + ys[3]) // 2 + 60, (ys[4] + ys[5]) // 2 + 60, (ys[6] + ys[7]) // 2 + 60]
    for i, (a, sa, b, sb) in enumerate(SF):
        slot(380, sf_y[2 * i], a, sa)
        slot(380, sf_y[2 * i + 1], b, sb)
        d.line((640, sf_y[2 * i], 640, sf_y[2 * i + 1]), fill=ink, width=3)
    f_y = [(sf_y[0] + sf_y[1]) // 2 + 40, (sf_y[2] + sf_y[3]) // 2 + 40]
    slot(700, f_y[0], FINAL[0])
    slot(700, f_y[1], FINAL[1])
    d.line((960, f_y[0], 960, f_y[1]), fill=ink, width=3)
    d.text((1000, (f_y[0] + f_y[1]) // 2 - 30), "FINAL  1:30am  Setup 2", fill=(20, 90, 40), font=font(36))
    img = img.rotate(-3, expand=True, fillcolor=(40, 40, 40)).filter(ImageFilter.GaussianBlur(1.1))
    a = np.array(img).astype(float)
    a += np.random.normal(0, 8, a.shape)
    a *= np.linspace(1.05, 0.8, a.shape[0])[:, None, None]
    Image.fromarray(a.clip(0, 255).astype("uint8")).save(out, quality=72)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bracket.jpg")
