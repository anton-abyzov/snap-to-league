"""Draw a messy handwritten tournament board for testing: python scripts/make_board.py out.jpg"""
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf"


def main(out: str, seed: int = 3) -> None:
    random.seed(seed)
    np.random.seed(seed)
    img = Image.new("RGB", (1400, 1000), (236, 238, 232))
    d = ImageDraw.Draw(img)
    font = lambda s: ImageFont.truetype(FONT, s)
    d.text((60, 30), "Sat 7v7 Cup - Group A", fill=(20, 40, 120), font=font(56))
    games = [("Lions", "Sharks", "3-1"), ("Hawks", "Wolves", "2-2"), ("Lions", "Hawks", "0-1"),
             ("Sharks", "Wolves", "4-2"), ("Lions", "Wolves", "2-0"), ("Sharks", "Hawks", "1 - 3")]
    y = 140
    for a, b, s in games:
        x = 80 + random.randint(-10, 10)
        d.text((x, y), f"{a}  v  {b}", fill=(25, 25, 25), font=font(44))
        d.text((x + 560, y + random.randint(-6, 6)), s, fill=(160, 20, 20), font=font(48))
        y += 78
    d.text((80, y + 20), "Final: Hawks v Sharks  Sun 10am  Field 2", fill=(20, 90, 40), font=font(40))
    d.line((70, y + 80, 900, y + 84), fill=(60, 60, 60), width=3)
    d.text((80, y + 100), "top 2 go through. Wolves forfeit last game?", fill=(90, 90, 90), font=font(34))
    img = img.rotate(4, expand=True, fillcolor=(40, 40, 40)).filter(ImageFilter.GaussianBlur(1.2))
    a = np.array(img).astype(float)
    a += np.random.normal(0, 9, a.shape)
    a *= np.linspace(0.75, 1.05, a.shape[1])[None, :, None]
    Image.fromarray(a.clip(0, 255).astype("uint8")).save(out, quality=70)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "board.jpg")
