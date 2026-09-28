"""Contact sheet of frames extracted from an encoded video: python3 scripts/sheet.py in.mp4 out.jpg t1 t2 ..."""
import subprocess, sys
from PIL import Image, ImageDraw
src, out, ts = sys.argv[1], sys.argv[2], [float(t) for t in sys.argv[3:]]
ims = []
for t in ts:
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", src, "-frames:v", "1", "-vf", "scale=360:640", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    im = Image.frombytes("RGB", (360, 640), b); ImageDraw.Draw(im).text((8, 8), f"{t:.2f}s", fill=(255, 80, 80)); ims.append(im)
cols = 6; rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (360 * cols, 640 * rows), "black")
for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 360, (i // cols) * 640))
sheet.save(out, quality=85)
