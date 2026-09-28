"""Finish the rendered reels into deliverables.

final.mp4    video stream copied from the render; audio = one static gain + oversampled peak limiter to
             about -14 LUFS / <= -1.5 dBTP; container metadata stripped.
textless.mp4 same picture minus all text layers; audio = the music bed with the SAME gain as final.mp4, so the
             bed sits exactly where it sits in the final between narration lines.
cover.png    frame 0 of final.mp4 (the hook frame).
voice.wav / music.wav  narration only / un-ducked bed only (48 kHz, 16-bit, stereo).
Writes deliver/manifest.json with durations and sha256, and reports/finish.json with loudness receipts.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_reels import SPECS  # noqa: E402

P = Path(__file__).resolve().parent.parent
D = P / "deliver"
TARGET, CEIL = -14.0, -1.5


def run(args):
    r = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-2500:])
    return r


def loud(path):
    r = run(["ffmpeg", "-hide_banner", "-i", path, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    d = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group())
    return float(d["input_i"]), float(d["input_tp"])


def encode(src, dst, gain):
    filt = (f"aresample=192000,volume={gain:.4f}dB,alimiter=limit={10 ** (-1.9 / 20):.6f}:level=false:attack=5:release=60,"
            "aresample=48000")
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy", "-af", filt, "-c:a", "aac",
         "-b:a", "256k", "-ar", "48000", "-map_metadata", "-1", "-map_metadata:s:v", "-1", "-map_metadata:s:a", "-1",
         "-fflags", "+bitexact", "-movflags", "+faststart", dst])


def probe(path):
    d = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,sample_rate,channels",
                        "-of", "json", path]).stdout)
    v = [s for s in d["streams"] if s["codec_type"] == "video"]
    a = [s for s in d["streams"] if s["codec_type"] == "audio"]
    return dict(duration_s=round(float(d["format"]["duration"]), 3),
                video=dict(codec=v[0]["codec_name"], width=v[0]["width"], height=v[0]["height"]) if v else None,
                audio=dict(codec=a[0]["codec_name"], sample_rate=int(a[0]["sample_rate"]), channels=a[0]["channels"]) if a else None)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


receipts, manifest = {}, {"project": "Snap to League platform reels", "canvas": [1080, 1920], "fps": 30, "reels": {}}
for reel in SPECS:
    n = reel[0]
    out = D / reel
    out.mkdir(parents=True, exist_ok=True)
    src, srct = P / f"renders/reel-{n}.mp4", P / f"renders/reel-{n}-textless.mp4"
    i0, tp0 = loud(src)
    gain, passes = TARGET - i0, []
    for _ in range(4):
        encode(src, out / "final.mp4", gain)
        i1, tp1 = loud(out / "final.mp4")
        passes.append(dict(gain_db=round(gain, 3), lufs=i1, true_peak_dbtp=tp1))
        if abs(i1 - TARGET) <= 0.3 and tp1 <= CEIL:
            break
        gain += TARGET - i1
    encode(srct, out / "textless.mp4", gain)
    it, tpt = loud(out / "textless.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-i", out / "final.mp4", "-frames:v", "1", "-map_metadata", "-1", out / "cover.png"])
    shutil.copyfile(P / f"assets/audio/{n}-voice.wav", out / "voice.wav")
    shutil.copyfile(P / f"assets/audio/{n}-music.wav", out / "music.wav")
    receipts[reel] = dict(render_lufs=i0, render_tp=tp0, passes=passes, textless_lufs=it, textless_tp=tpt,
                          voice_lufs=loud(out / "voice.wav")[0], music_lufs=loud(out / "music.wav")[0])
    files = {}
    for f in sorted(out.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            e = dict(bytes=f.stat().st_size, sha256=sha(f))
            if f.suffix in (".mp4", ".wav"):
                e.update(probe(f))
            files[f.name] = e
    manifest["reels"][reel] = dict(title=SPECS[reel]["title"], duration_s=files["final.mp4"]["duration_s"],
                                   final_loudness_lufs=passes[-1]["lufs"], final_true_peak_dbtp=passes[-1]["true_peak_dbtp"],
                                   textless_audio="music bed only, same gain as final", files=files)
    print(reel, passes[-1], "textless", it, flush=True)

manifest["notes"] = [
    "All product footage is real headless capture of https://snap.easychamp.com and existing published demo leagues; demo data only.",
    "Header model chip and photo-reader picker hidden with CSS during capture; nothing was published.",
    "Narration: ElevenLabs stock voice, not a clone. Music: 'Deep Urban' by Eugenio Mininni, Mixkit Stock Music Free License.",
    "caption.txt contains {LINK} where the UTM link goes.",
]
(D / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
(P / "reports/finish.json").write_text(json.dumps(receipts, indent=1) + "\n")
