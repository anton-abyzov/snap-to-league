"""Locate the green 'Double-checked' badge (bg ~ rgb(228,242,233)) per capture over time, in CSS px."""
import json, subprocess, sys
import numpy as np
P = __import__("pathlib").Path(__file__).resolve().parent.parent
def frames(n, t0, t1, fps=4):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-i", P / f"assets/footage/{n}.mp4", "-t", str(t1 - t0), "-vf", f"fps={fps},scale=390:844",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, 844, 390, 3).astype(int)
out = {}
for n in sys.argv[1:]:
    vt = json.loads((P / f"capture/raw/{n}.json").read_text())["video_times"]
    fr = frames(n, vt["review"], vt["end"]); res = []
    for i, f in enumerate(fr):
        m = (np.abs(f[..., 0] - 228) < 8) & (np.abs(f[..., 1] - 241) < 6) & (np.abs(f[..., 2] - 233) < 8)
        rows = np.nonzero(m.sum(1) > 150)[0]
        if len(rows) > 12:
            cols = np.nonzero(m[rows].sum(0) > 5)[0]
            res.append([round(vt["review"] + i / 4, 2), [int(cols.min()), int(rows.min()), int(cols.max()), int(rows.max())]])
    out[n] = res
    print(n, res[:3], "...", res[-2:] if res else None)
(P / "capture/raw/badges.json").write_text(json.dumps(out, indent=1) + "\n")
