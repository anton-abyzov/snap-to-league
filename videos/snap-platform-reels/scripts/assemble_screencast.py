"""Assemble CDP screencast frames (variable rate, wall-clock stamps) into 30 fps H.264.
Each output frame shows the latest screencast frame at or before its time. Event times in the
capture JSON are rewritten as video times (video_times) on the same clock."""
import json, subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parent.parent
for n in sys.argv[1:]:
    meta = json.loads((P / f"capture/raw/{n}.json").read_text())
    fr = meta["frames"]; t0 = fr[0][0]; fdir = P / f"capture/raw/{n}"
    end = max(fr[-1][0], meta["events"][-1]["t"]) - t0 + 0.2
    lst = fdir / "concat.txt"; lines = []
    for i, (ts, name) in enumerate(fr):
        nxt = fr[i + 1][0] if i + 1 < len(fr) else t0 + end
        lines += [f"file '{name}'", f"duration {max(nxt - ts, 0.001):.4f}"]
    lines.append(f"file '{fr[-1][1]}'")
    lst.write_text("\n".join(lines) + "\n")
    out = P / f"assets/footage/{n}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-vf",
                    "fps=30,scale=1170:2532:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-crf", "15", "-preset", "medium",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", out], check=True)
    meta["video_times"] = {e["event"]: round(e["t"] - t0, 3) for e in meta["events"]}
    gaps = [fr[i + 1][0] - fr[i][0] for i in range(len(fr) - 1)]
    meta["screencast_stats"] = {"frames": len(fr), "span_s": round(fr[-1][0] - t0, 3), "mean_fps": round(len(fr) / (fr[-1][0] - t0), 2),
                                "max_gap_s": round(max(gaps), 3)}
    (P / f"capture/raw/{n}.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(n, meta["screencast_stats"], meta["video_times"])
