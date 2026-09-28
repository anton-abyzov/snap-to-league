"""Build the four Snap to League platform reels (1080x1920, 30 fps) as HyperFrames compositions.

For each reel this writes:
  reel-<n>/index.html            final composition (captions + on-screen copy)
  reel-<n>-textless/index.html   same picture with every text layer removed, music-only audio
  assets/footage/screen-<n>.mp4  phone-screen picture track (real captures, cut to the beats)
  assets/audio/<n>-voice.wav / -music.wav / -mix.wav
  deliver/<slug>/captions.srt, script.txt, text-layers.json, caption.txt
Inputs: capture/raw/*.json (real headless captures), assets/audio/vo/*.mp3 (ElevenLabs lines).
"""
import html
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from reels_script import REELS  # noqa: E402

P = Path(__file__).resolve().parent.parent
A = P / "assets"
FPS = 30
W, H = 1080, 1920
# Phone screen placement (composition px). Captures are 390x844 CSS at 3x.
SW = 600
K = SW / 390
SX, SY = (W - SW) // 2, 575
SH = round(844 * K)
BEZ = 18


def run(args):
    r = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-3000:])
    return r.stdout


def vt(name):
    return json.loads((P / f"capture/raw/{name}.json").read_text())["video_times"]


def events(name):
    return {e["event"]: e for e in json.loads((P / f"capture/raw/{name}.json").read_text())["events"]}


def css(x, y):
    return SX + x * K, SY + y * K


# ---------------------------------------------------------------- reel specs
SOC, HOO, PAD, SMA = vt("app-soccer"), vt("app-hoops"), vt("app-padel"), vt("app-smash")
PIT, SMS = vt("site-pit"), vt("site-smash")
FINAL_BOX = [183, 360, 356, 424]      # final match box after the bracket scroll (CSS px), see capture frames
BADGE_TOP = [35, 92, 354, 132]        # green double-check badge right after the read (CSS px)
BADGE_REVIEW = [35, 162, 354, 202]    # same badge after scrolling the review into view
PUBLISH = [35, 586, 190, 648]

SPECS = {
    "1-soccer-whiteboard": dict(
        title="Whiteboard to live table", sport="soccer", music_at=15.0,
        hook=dict(kind="photo", src="stills/sample-shellhacks-groups.jpg", w=1944, h=1460),
        gaps=[0.35, 0.25, 0.35, 0.3, 0.45, 0.45],
        labels=["Built-in sample board · demo data", "Live app capture · demo data", "Live app capture · demo data",
                "Live app capture · demo data", "Live app capture · demo data", "Published demo league · existing page", ""],
        screen=[
            [("app-soccer", 0.45, None)],
            [("app-soccer", SOC["tap-sample"] - 1.1, None)],
            [("app-soccer", SOC["tray"] + 0.7, 1.1), ("app-soccer", SOC["review"] + 0.05, None)],
            [("app-soccer", 28.95, 1.42, "freeze")],
            [("app-soccer", SOC["table"] - 0.6, 1.9), ("app-soccer", SOC["scorers"] - 0.45, None)],
            [("site-pit", PIT["Knockout"] - 0.9, 1.9), ("site-pit", PIT["Standings"] - 0.7, None)],
            [("app-soccer", 0.45, 1.1, "freeze")],
        ],
        taps=[(1, "app-soccer", "tap-sample")],
        focus={3: dict(rect=BADGE_REVIEW, zoom=1.55, at=0.25)},
        keywords=[["WHITEBOARD"], ["ONE", "PHOTO"], ["EVERY", "SCORE", "SCORER"], ["DOUBLE-CHECKS"],
                  ["GROUP", "TABLES", "TOP", "SCORERS"], ["LIVE", "LEAGUE"], []],
        social=("Saturday cup still living on a whiteboard? Snap one photo and Snap to League reads every score "
                "and every scorer, double-checks every result, and builds your group tables and top scorers. "
                "Sign in with EasyChamp to publish it as a live league your players can follow.\n\n"
                "Free. Any sport. Try it: {LINK}\n\n#futsal #soccer #sundayleague #grassroots"),
    ),
    "2-hoops-bracket": dict(
        title="Drawn bracket to live knockout", sport="basketball", music_at=120.0,
        hook=dict(kind="photo", src="synthetic/hoops-bracket.jpg", w=1994, h=1296),
        gaps=[0.35, 0.3, 0.3, 0.35, 0.4, 0.45],
        labels=["Synthetic demo photo · demo data", "Live app capture · demo data", "Live app capture · demo data",
                "Live app capture · demo data", "Live app capture · demo data", "Live app capture · demo data", ""],
        screen=[
            [("app-hoops", 0.45, None)],
            [("app-hoops", HOO["tap-choose"] - 0.35, None)],
            [("app-hoops", HOO["tap-read"] + 0.2, 1.2), ("app-hoops", HOO["review"] + 0.05, None)],
            [("app-hoops", HOO["checked"] - 0.8, None)],
            [("app-hoops", HOO["table"] - 0.4, 1.3), ("app-hoops", HOO["bracket-final"] - 1.75, None, "freeze")],
            [("app-hoops", HOO["publish-button"] - 1.0, None, "freeze")],
            [("app-hoops", 0.45, 1.1, "freeze")],
        ],
        taps=[(1, "app-hoops", "tap-choose"), (2, "app-hoops", "tap-read")],
        focus={3: dict(rect=BADGE_TOP, zoom=1.55, at=0.7), 4: dict(rect=FINAL_BOX, zoom=1.75, at=2.9),
               5: dict(rect=PUBLISH, zoom=1.45, at=1.0)},
        keywords=[["BRACKET", "WHITEBOARD"], ["ONE", "PHOTO"], ["SECONDS"], ["DOUBLE-CHECKS"],
                  ["FINAL", "KNOCKOUT"], ["PUBLISH"], []],
        social=("Drew your 3x3 bracket on a whiteboard? Take one photo. Snap to League reads every game and every "
                "score in seconds, double-checks every result, and rebuilds the knockout: quarterfinals, semis and "
                "the final. Sign in to publish it to your EasyChamp account.\n\n"
                "Free. Any sport. Try it: {LINK}\n\n#3x3basketball #basketball #streetball #tournament"),
    ),
    "3-padel-ladder": dict(
        title="Paper sheet to standings", sport="padel", music_at=160.0,
        hook=dict(kind="video", src="footage/real-r3.mp4"),
        card=dict(src="synthetic/padel-ladder.jpg", w=1460, h=1614),
        gaps=[0.3, 0.3, 0.3, 0.35, 0.4, 0.45],
        labels=["Real event footage · ShellHacks 2026", "Synthetic demo sheet · demo data", "Live app capture · demo data",
                "Live app capture · demo data", "Live app capture · demo data", "Live app capture · demo data", ""],
        screen=[
            [("app-padel", 0.45, None)],
            [("app-padel", PAD["tap-choose"] - 0.3, None)],
            [("app-padel", PAD["tray"] + 0.1, 1.0), ("app-padel", PAD["review"] + 0.05, None)],
            [("app-padel", PAD["checked"] - 0.8, None)],
            [("app-padel", PAD["table"] - 0.75, None, "freeze")],
            [("app-padel", PAD["publish-button"] - 1.0, None, "freeze")],
            [("app-padel", 0.45, 1.1, "freeze")],
        ],
        taps=[(1, "app-padel", "tap-choose"), (2, "app-padel", "tap-read")],
        focus={3: dict(rect=BADGE_TOP, zoom=1.55, at=0.7), 4: dict(rect=[35, 330, 355, 497], zoom=1.4, at=0.9),
               5: dict(rect=PUBLISH, zoom=1.45, at=1.0)},
        keywords=[["PADEL", "PAPER"], ["SNAP"], ["EVERY", "PAIR", "SET"], ["DOUBLE-CHECKS"],
                  ["STANDINGS"], ["UPDATES"], []],
        social=("Padel ladder on a paper sheet? Snap it. Snap to League reads every pair and every set, "
                "double-checks every result, and ranks the standings for you. Publish it with EasyChamp and "
                "next week's photo updates it.\n\n"
                "Free. Any sport. Try it: {LINK}\n\n#padel #pickleball #padellife #racketsports"),
    ),
    "4-esports-screenshot": dict(
        title="Screenshot to competition", sport="smash", music_at=30.0,
        hook=dict(kind="shot", src="synthetic/smash-screenshot.png", w=1170, h=2532),
        gaps=[0.3, 0.3, 0.3, 0.35, 0.4, 0.45],
        labels=["Synthetic demo screenshot · demo data", "Live app capture · demo data", "Live app capture · demo data",
                "Live app capture · demo data", "Live app capture · demo data", "Separate published demo league", ""],
        screen=[
            [("app-smash", 0.45, None)],
            [("app-smash", SMA["tap-choose"] - 0.35, None)],
            [("app-smash", SMA["tap-read"] + 0.2, 1.0), ("app-smash", SMA["review"] + 0.05, None)],
            [("app-smash", SMA["checked"] - 0.8, None)],
            [("app-smash", SMA["table"] - 0.4, 0.9), ("app-smash", SMA["bracket-final"] - 1.75, None, "freeze")],
            [("site-smash", SMS["Knockout"] - 0.9, 1.4), ("site-smash", SMS["click:F"] - 0.2, None, "freeze")],
            [("app-smash", 0.45, 1.1, "freeze")],
        ],
        taps=[(1, "app-smash", "tap-choose"), (2, "app-smash", "tap-read")],
        focus={3: dict(rect=BADGE_TOP, zoom=1.55, at=0.7), 4: dict(rect=FINAL_BOX, zoom=1.75, at=2.5)},
        keywords=[["SCREENSHOT"], ["SCREENSHOT"], ["EVERY", "MATCH", "SCORE"], ["DOUBLE-CHECKS"],
                  ["BRACKET", "GRAND", "FINAL"], ["REAL", "COMPETITION"], []],
        social=("Smash night bracket stuck in a screenshot? Drop the screenshot into Snap to League. It reads every "
                "match and every score, double-checks every result, and rebuilds the bracket right up to the grand "
                "final. Publish it as a real competition on EasyChamp.\n\n"
                "Free. Any sport. Try it: {LINK}\n\n#smashbros #esports #eafc #tournament"),
    ),
}


# ---------------------------------------------------------------- audio helpers
def pcm(path, sr=48000):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(sr), "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).reshape(-1, 2).astype(np.float64)


def write_wav(path, x, sr=48000):
    x = np.clip(x, -1, 1)
    with wave.open(str(path), "wb") as wf:
        wf.setparams((2, 2, sr, 0, "NONE", "not compressed"))
        wf.writeframes((x * 32767).astype("<i2").tobytes())


def speech_bounds(x, sr=48000, thr_db=-42):
    env = np.abs(x).max(1)
    win = int(sr * 0.01)
    e = np.convolve(env, np.ones(win) / win, mode="same")
    idx = np.nonzero(20 * np.log10(e + 1e-9) > thr_db)[0]
    return idx[0] / sr, idx[-1] / sr


def words_of(reel, i):
    d = json.loads((A / f"audio/vo/{reel}-{i}.json").read_text())
    a = d["alignment"]
    out, cur, st, en = [], "", 0, 0
    for c, b, e in zip(a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"]):
        if c.isspace():
            if cur:
                out.append([cur, st, en])
            cur = ""
        else:
            if not cur:
                st = b
            cur += c
            en = e
    if cur:
        out.append([cur, st, en])
    return out


# ---------------------------------------------------------------- per reel
def plan(reel, spec):
    lines = REELS[reel]
    clips, s, t = [], [], 0.2
    for i, text in enumerate(lines):
        x = pcm(A / f"audio/vo/{reel}-{i}.mp3")
        a, b = speech_bounds(x)
        x = x[max(0, int((a - 0.03) * 48000)): int((b + 0.08) * 48000)]
        clips.append(x)
        s.append(round(t, 3))
        t += len(x) / 48000 + (spec["gaps"][i] if i < len(spec["gaps"]) else 0)
        spec.setdefault("_trim", []).append(max(0, a - 0.03))
    total = round((s[-1] + len(clips[-1]) / 48000 + 0.9) * FPS) / FPS
    beats = [0.0] + [round(round((si - 0.12) * FPS) / FPS, 4) for si in s[1:]] + [total]
    return clips, s, beats, total


def build_screen(reel, spec, beats, total):
    """One continuous phone-screen picture track, frame-exact to the beat grid."""
    tmp = P / ".build" / reel
    tmp.mkdir(parents=True, exist_ok=True)
    parts = []
    for bi, segs in enumerate(spec["screen"]):
        f0, f1 = round(beats[bi] * FPS), round(beats[bi + 1] * FPS)
        n_beat = f1 - f0
        used = 0
        for si, seg in enumerate(segs):
            src, t_in, dur = seg[0], seg[1], seg[2]
            freeze = len(seg) > 3
            last = si == len(segs) - 1
            n = n_beat - used if last else round(dur * FPS)
            if n <= 0:
                continue
            take = n if not (freeze and dur) else min(n, round(dur * FPS))
            out = tmp / f"s{bi:02}-{si}.mp4"
            vf = f"trim=start={t_in:.4f},setpts=PTS-STARTPTS,fps={FPS},trim=end_frame={take},tpad=stop_mode=clone:stop={n},trim=end_frame={n},format=yuv420p"
            run(["ffmpeg", "-v", "error", "-y", "-i", A / f"footage/{src}.mp4", "-vf", vf, "-frames:v", n, "-an",
                 "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-g", "30", "-color_primaries", "bt709", "-color_trc", "bt709",
                 "-colorspace", "bt709", out])
            got = int(run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                           "stream=nb_read_frames", "-of", "csv=p=0", out]).strip())
            if got != n:
                raise RuntimeError(f"{out.name}: {got} frames, wanted {n}")
            parts.append(out)
            used += n
        spec.setdefault("_screen_map", []).append([beats[bi], beats[bi + 1], [list(map(str, s[:2])) for s in segs]])
    lst = tmp / "screen.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    dst = A / f"footage/screen-{reel[0]}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", dst])
    return dst


def screen_time(spec, beats, reel_t):
    """Map a reel time to (source, source_time) for the phone screen."""
    for bi, segs in enumerate(spec["screen"]):
        if beats[bi] <= reel_t < beats[bi + 1]:
            t = beats[bi]
            for si, seg in enumerate(segs):
                d = seg[2] if seg[2] and si < len(segs) - 1 else beats[bi + 1] - t
                if reel_t < t + d:
                    return seg[0], seg[1] + (reel_t - t)
                t += d
    return None, None


def build_audio(reel, spec, clips, starts, total):
    n = round(total * 48000)
    voice = np.zeros((n, 2))
    for x, s in zip(clips, starts):
        x = x.copy()
        fade = int(0.012 * 48000)
        x[:fade] *= np.linspace(0, 1, fade)[:, None]
        x[-fade:] *= np.linspace(1, 0, fade)[:, None]
        i = int(s * 48000)
        voice[i:i + len(x)] += x[: n - i]
    vpath = A / f"audio/{reel[0]}-voice-raw.wav"
    write_wav(vpath, voice)
    vout = A / f"audio/{reel[0]}-voice.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", vpath, "-af", "highpass=f=80,loudnorm=I=-16:TP=-2:LRA=7", "-ar", "48000", "-ac", "2", vout])
    # Bed: choose a strong downbeat near the planned section start.
    mus = pcm(A / "audio/deep-urban.mp3")
    at = spec["music_at"]
    m0 = np.abs(mus[:, 0]); m0 = m0[: len(m0) // 480 * 480]
    env = m0.reshape(-1, 480).max(1)            # 10 ms envelope
    lo, hi = int((at - 1.0) * 100), int((at + 1.0) * 100)
    onset = np.maximum(np.diff(env[lo:hi]), 0)
    at = (lo + int(np.argmax(onset)) + 1) / 100 - 0.02
    spec["_music_in"] = round(at, 2)
    mout = A / f"audio/{reel[0]}-music.wav"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.3f}", "-i", A / "audio/deep-urban.mp3", "-t", f"{total:.3f}", "-af",
         f"loudnorm=I=-26:TP=-6:LRA=8,afade=t=in:d=0.08,afade=t=out:st={total - 1.4:.3f}:d=1.4", "-ar", "48000", "-ac", "2", mout])
    mix = A / f"audio/{reel[0]}-mix.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", vout, "-i", mout, "-filter_complex",
         "[0:a]asplit=2[v][key];[1:a][key]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=350:makeup=1[bed];"
         "[v][bed]amix=inputs=2:normalize=0,alimiter=limit=0.89[m]", "-map", "[m]", "-ar", "48000", mix])
    return vout, mout, mix


# ---------------------------------------------------------------- captions
def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def caption_chunks(reel, spec, starts):
    """One caption per narration line (short lines), split at ~26 chars for the SRT."""
    caps = []
    for i, text in enumerate(REELS[reel]):
        ws = words_of(reel, i)
        off = starts[i] - spec["_trim"][i]
        ws = [[w, round(a + off, 3), round(b + off, 3)] for w, a, b in ws]
        merged, j = [], 0
        while j < len(ws):
            seq = [w[0].lower().strip(".") for w in ws[j:j + 5]]
            if seq == ["snap", "dot", "easychamp", "dot", "com"]:
                merged.append(["snap.easychamp.com" + ("." if ws[j + 4][0].endswith(".") else ""), ws[j][1], ws[j + 4][2]])
                j += 5
                continue
            w = ws[j]
            merged.append([w[0].replace("three-on-three", "3x3"), w[1], w[2]])
            j += 1
        ws = merged
        caps.append(dict(i=i, text=text, words=ws, start=ws[0][1], end=ws[-1][2]))
    return caps


def write_srt(path, caps):
    items = []
    for c in caps:
        group, chunks = [], []
        for w in c["words"]:
            if group and len(" ".join(x[0] for x in group) + " " + w[0]) > 32:
                chunks.append(group)
                group = []
            group.append(w)
        chunks.append(group)
        for g in chunks:
            items.append([g[0][1], g[-1][2] + 0.12, ' '.join(x[0] for x in g)])
    for j in range(len(items) - 1):
        items[j][1] = min(items[j][1], items[j + 1][0] - 0.01)
    items = [f"{j + 1}\n{srt_time(a)} --> {srt_time(b)}\n{t}\n" for j, (a, b, t) in enumerate(items)]
    path.write_text("\n".join(items))


# ---------------------------------------------------------------- HTML
CSS = """
@font-face{font-family:Archivo;src:url(assets/fonts/archivo-400.ttf)}
@font-face{font-family:Archivo;src:url(assets/fonts/archivo-700.ttf);font-weight:700}
@font-face{font-family:ArchivoBlack;src:url(assets/fonts/archivo-black-400.ttf);font-weight:900}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;background:#12152A}
#root{position:relative;width:100%;height:100%;overflow:hidden;font-family:Archivo,sans-serif;background:#12152A}
.clip{position:absolute;inset:0}
.bg{position:absolute;inset:0;background:radial-gradient(1100px 900px at 50% 58%,#2A2F6B 0%,#171A36 55%,#101326 100%)}
.grid{position:absolute;left:-120px;top:-120px;width:1320px;height:2160px;opacity:.55;
 background-image:linear-gradient(#ffffff0d 2px,transparent 2px),linear-gradient(90deg,#ffffff0d 2px,transparent 2px);background-size:120px 120px}
.glow{position:absolute;left:140px;top:560px;width:800px;height:1100px;border-radius:50%;
 background:radial-gradient(closest-side,#8186F1aa,#595ECC33 60%,transparent);filter:blur(30px)}
.cam{position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:13}
.topshade{position:absolute;left:0;top:0;width:1080px;height:700px;z-index:14;background:linear-gradient(180deg,#12152A 0%,#12152Af2 45%,#12152Ab3 72%,#12152A00 100%)}
.phone{position:absolute;left:@PX@px;top:@PY@px;width:@PW@px;height:@PH@px;border-radius:74px;background:#0B0D18;
 box-shadow:0 0 0 3px #3A3F6E,0 50px 120px #0009,0 20px 40px #0006;padding:@BEZ@px}
.screen-wrap{position:relative;width:@SW@px;height:@SH@px;border-radius:56px;overflow:hidden;background:#F6F6FA}
.screen{position:absolute;left:0;top:0;width:@SW@px;height:@SH@px;object-fit:cover}
.sheen{position:absolute;left:0;top:0;width:@SW@px;height:@SH@px;border-radius:56px;overflow:hidden;pointer-events:none}
.sheen i{position:absolute;top:-20%;left:-60%;width:40%;height:140%;background:linear-gradient(90deg,transparent,#ffffff55,transparent);transform-origin:center}
.island{position:absolute;left:50%;top:@IT@px;width:150px;height:40px;margin-left:-75px;border-radius:22px;background:#05060C}
.ring{position:absolute;overflow:visible;pointer-events:none}
.ripple{position:absolute;width:120px;height:120px;border-radius:50%;border:6px solid #8186F1;background:#8186F133}
.card{position:absolute;z-index:14;border-radius:18px;overflow:hidden;box-shadow:0 40px 90px #000a,0 0 0 4px #ffffff22;background:#222}
.card img{display:block;width:100%;height:100%;object-fit:cover}
.scan{position:absolute;left:0;right:0;height:180px;top:-200px;background:linear-gradient(180deg,transparent,#8186F155 70%,#C9CBFF 97%,transparent)}
.flash{position:absolute;inset:0;background:#fff}
.flashclip{z-index:25}
.real{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.shade{position:absolute;inset:0;background:linear-gradient(180deg,#0B0D1Ae6 0%,#0B0D1A99 26%,transparent 44%,transparent 70%,#0B0D1Acc 100%)}
.brand{position:absolute;left:62px;top:92px;display:flex;font-weight:700;font-size:25px;letter-spacing:2px;z-index:20}
.brand b{background:#595ECC;color:#fff;padding:11px 15px;font-weight:700}
.brand i{font-style:normal;background:#2A2F55;color:#fff;padding:11px 15px}
.cap{position:absolute;left:62px;right:62px;top:176px;z-index:15}
.cap .line{font-family:ArchivoBlack,sans-serif;font-weight:900;font-size:70px;line-height:1.02;letter-spacing:-1.5px;color:#FAFAFA;text-transform:uppercase;
 text-shadow:0 6px 30px #0008}
.cap.hook .line{font-size:94px;line-height:.98;letter-spacing:-2.5px}
.cap .w{display:inline-block;will-change:transform;margin-right:.22em}
.cap .w.k{color:#A4A7FF}
.mask{display:inline-block;overflow:hidden;vertical-align:top;padding-bottom:.08em;margin-bottom:-.08em}
.under{position:relative;display:block;width:520px;height:34px;margin-top:16px}
.label{position:absolute;left:62px;top:500px;font-size:22px;font-weight:700;letter-spacing:1.6px;text-transform:uppercase;color:#C9CBFF;
 background:#1C2046cc;border:2px solid #595ECC;padding:8px 14px;border-radius:6px;z-index:16}
.label.low{top:auto;bottom:250px}
.end{position:absolute;inset:0;z-index:12}
.endtext{z-index:20}
.end .panel{position:absolute;inset:0;background:radial-gradient(900px 900px at 50% 70%,#2A2F6B,#12152A 70%)}
.end .kick{position:absolute;left:62px;top:196px;font-size:26px;letter-spacing:5px;font-weight:700;color:#A4A7FF}
.end h2{position:absolute;left:58px;top:246px;font-family:ArchivoBlack,sans-serif;font-weight:900;font-size:150px;line-height:.9;letter-spacing:-4px;color:#FAFAFA}
.end h2 span{display:block}
.end .url{position:absolute;left:62px;top:560px;height:104px;width:956px;border-radius:14px;overflow:hidden}
.end .url .fill{position:absolute;inset:0;background:#8186F1;transform-origin:left center}
.end .url .t{position:absolute;left:34px;top:22px;font-family:ArchivoBlack,sans-serif;font-size:56px;color:#12152A;letter-spacing:-1px}
.end .sub{position:absolute;left:62px;top:696px;font-size:31px;line-height:1.3;color:#DADBF5;width:940px}
.wipe{overflow:hidden;z-index:30}
.curtain{position:absolute;top:-10%;bottom:-10%;left:-20%;width:140%;background:#595ECC;border-right:14px solid #A4A7FF}
.progress{position:absolute;left:0;bottom:0;width:100%;height:8px;background:#8186F1;transform-origin:left center;z-index:40}
.textless .txt{display:none}
"""


def esc(s):
    return html.escape(s, quote=True)


def compose(reel, spec, caps, beats, total, audio_rel, textless):
    n = reel[0]
    comp_id = f"reel{n}" + ("t" if textless else "")
    k = K
    pw, ph = SW + 2 * BEZ, SH + 2 * BEZ
    px, py = SX - BEZ, SY - BEZ
    style = CSS
    for k_, v_ in dict(PX=px, PY=py, PW=pw, PH=ph, BEZ=BEZ, SW=SW, SH=SH, IT=14).items():
        style = style.replace(f"@{k_}@", str(v_))
    el, tl, layers = [], [], []
    b = beats

    def layer(kind, text, start, end, box, **extra):
        layers.append(dict(kind=kind, text=text, start=round(start, 3), end=round(end, 3), box=[round(v) for v in box], **extra))

    # background (continuous drift)
    el.append('<div class="bg"></div><div id="grid" class="grid"></div>')
    tl.append(f'tl.fromTo("#grid",{{x:0,y:0}},{{x:-120,y:-240,duration:{total},ease:"none"}},0);')
    el.append('<div id="glow" class="glow"></div>')
    tl.append(f'tl.fromTo("#glow",{{opacity:0,scale:.8}},{{opacity:1,scale:1,duration:.8,ease:"power2.out"}},{b[1] - .2:.3f});')

    cam_slot = len(el)
    # hook media
    hook = spec["hook"]
    hook_end = b[1]
    if hook["kind"] == "video":
        el.append(f'<video id="real" class="clip real" src="assets/{hook["src"]}" data-start="0" data-duration="{hook_end + 0.3:.3f}" '
                  f'data-track-index="1" muted playsinline></video><div class="clip shade" data-start="0" data-duration="{hook_end + 0.3:.3f}" data-track-index="2"></div>')
    else:
        if hook["kind"] == "shot":
            cw = 540
            ch = round(cw * hook["h"] / hook["w"])
            cx, cy = (W - cw) // 2, 520
        else:
            cw = 1000
            ch = round(cw * hook["h"] / hook["w"])
            cx, cy = 40, 640
        el.append(f'<div id="hookcard" class="card" style="left:{cx}px;top:{cy}px;width:{cw}px;height:{ch}px">'
                  f'<img src="assets/{hook["src"]}" alt=""><div id="scan0" class="scan"></div></div>')
        tl.append(f'tl.fromTo("#hookcard",{{rotationX:16,rotationY:-14,rotation:-3,scale:.92,transformPerspective:1400}},'
                  f'{{rotationX:4,rotationY:6,rotation:1.5,scale:1.02,duration:{hook_end:.3f},ease:"sine.inOut"}},0);')
        tl.append(f'tl.fromTo("#scan0",{{y:0}},{{y:{ch + 260},duration:1.1,ease:"power1.inOut"}},{0.5:.3f});')
        # match-move: the photo shrinks into the phone as the phone rises
        tx, ty = SX + SW / 2 - (cx + cw / 2), SY + SH * 0.45 - (cy + ch / 2)
        tl.append(f'tl.to("#hookcard",{{x:{tx:.0f},y:{ty:.0f},scale:.22,rotationX:0,rotationY:0,rotation:0,duration:.55,ease:"power3.in"}},{hook_end - 0.2:.3f});')
        tl.append(f'tl.to("#hookcard",{{opacity:0,duration:.12,ease:"none"}},{hook_end + 0.3:.3f});')
    # second card (padel sheet) during beat 1
    if "card" in spec:
        c = spec["card"]
        cw = 860
        ch = round(cw * c["h"] / c["w"])
        cx, cy = (W - cw) // 2, 560
        el.append(f'<div id="card1" class="card" style="left:{cx}px;top:{cy}px;width:{cw}px;height:{ch}px;opacity:0">'
                  f'<img src="assets/{c["src"]}" alt=""><div id="scan1" class="scan"></div></div>')
        t0 = b[1]
        tl.append(f'tl.fromTo("#card1",{{opacity:0,scale:1.25,rotation:-6}},{{opacity:1,scale:1,rotation:-2,duration:.28,ease:"power4.out"}},{t0:.3f});')
        tl.append(f'tl.fromTo("#scan1",{{y:0}},{{y:{ch + 260},duration:.8,ease:"power1.inOut"}},{t0 + .2:.3f});')
        tx, ty = SX + SW / 2 - (cx + cw / 2), SY + SH * 0.45 - (cy + ch / 2)
        tl.append(f'tl.to("#card1",{{x:{tx:.0f},y:{ty:.0f},scale:.2,rotation:0,duration:.5,ease:"power3.in"}},{b[2] - .55:.3f});')
        tl.append(f'tl.to("#card1",{{opacity:0,duration:.1}},{b[2] - .08:.3f});')
        el.append(f'<div class="clip flashclip" id="flashwrap" data-start="{t0:.3f}" data-duration="0.4" data-track-index="8"><div id="flash1" class="flash"></div></div>')
        tl.append(f'tl.fromTo("#flash1",{{opacity:.95}},{{opacity:0,duration:.35,ease:"power2.out"}},{t0:.3f});')

    # phone + camera rig
    phone_in = b[1] + 0.2 if "card" in spec else b[1] - 0.3
    ring_html, ring_tl = [], []
    for bi, f in spec["focus"].items():
        x0, y0 = css(f["rect"][0] - 6, f["rect"][1] - 6)
        x1, y1 = css(f["rect"][2] + 6, f["rect"][3] + 6)
        w, h = x1 - x0, y1 - y0
        rid = f"ring{bi}"
        ring_html.append(f'<svg class="ring" style="left:{x0:.0f}px;top:{y0:.0f}px;width:{w:.0f}px;height:{h:.0f}px" viewBox="0 0 {w:.0f} {h:.0f}">'
                         f'<rect id="{rid}" x="3" y="3" width="{w - 6:.0f}" height="{h - 6:.0f}" rx="16" fill="none" stroke="#FFB547" stroke-width="6" pathLength="1"/></svg>')
        t_at = b[bi] + f["at"]
        t_out = b[bi + 1] - 0.3
        z = f["zoom"]
        fx, fy = (x0 + x1) / 2, (y0 + y1) / 2
        cx_, cy_ = 540 - fx * z, (1260 if z > 1.6 else 1180) - fy * z
        ring_tl.append(f'tl.fromTo("#{rid}",{{strokeDasharray:1,strokeDashoffset:1,opacity:1}},{{strokeDashoffset:0,duration:.45,ease:"power2.out"}},{t_at + .25:.3f});')
        ring_tl.append(f'tl.to("#{rid}",{{opacity:0,duration:.2}},{t_out:.3f});')
        ring_tl.append(f'tl.to("#cam",{{scale:{z},x:{cx_:.1f},y:{cy_:.1f},transformOrigin:"0 0",duration:.6,ease:"power3.inOut"}},{t_at:.3f});')
        ring_tl.append(f'tl.to("#cam",{{scale:1,x:0,y:0,transformOrigin:"0 0",duration:.5,ease:"power3.inOut"}},{t_out:.3f});')
    taps = []
    for bi, src, ev in spec["taps"]:
        e = events(src)[ev]
        vtimes = vt(src)
        # find the reel time where the screen shows this source moment
        for tt in np.arange(b[bi], b[bi + 1], 1 / FPS):
            s_, st = screen_time(spec, b, tt)
            if s_ == src and abs(st - vtimes[ev]) < 0.5 / FPS + 1e-6:
                r = e["rect_css"]
                x, y = css(r[0] + r[2] / 2, r[1] + r[3] / 2)
                rid = f"tap{bi}{ev.replace('-', '')}"
                taps.append(f'<div id="{rid}" class="ripple" style="left:{x - 60:.0f}px;top:{y - 60:.0f}px;opacity:0"></div>')
                ring_tl.append(f'tl.fromTo("#{rid}",{{scale:.3,opacity:1}},{{scale:1.6,opacity:0,duration:.55,ease:"power2.out",immediateRender:false}},{tt:.3f});')
                break
    el.insert(cam_slot, f'<div id="cam" class="cam"><div id="phone" class="phone"><div class="screen-wrap">'
              f'<video id="screen" class="screen" src="assets/footage/screen-{n}.mp4" data-start="0" data-duration="{total:.3f}" data-track-index="3" muted playsinline></video>'
              f'<div class="sheen"><i id="sheen"></i></div></div><div class="island"></div></div>{"".join(ring_html)}{"".join(taps)}</div>')
    tl.append(f'tl.fromTo("#phone",{{y:1500,rotationX:28,scale:.9,transformPerspective:1600}},{{y:0,rotationX:0,scale:1,duration:.75,ease:"power3.out"}},{phone_in:.3f});')
    tl.append(f'tl.fromTo("#sheen",{{x:0,rotation:18}},{{x:{SW * 2.6:.0f},rotation:18,duration:.9,ease:"power2.inOut"}},{phone_in + .55:.3f});')
    tl.extend(ring_tl)
    # gentle float while holding
    tl.append(f'tl.fromTo("#phone",{{rotation:0}},{{rotation:-1.2,duration:{(b[6] - phone_in - .8) / 2:.3f},ease:"sine.inOut",yoyo:true,repeat:1}},{phone_in + .8:.3f});')
    # end card: phone shrinks to the lower part
    te = b[6]
    tl.append(f'tl.to("#phone",{{y:70,scale:.68,duration:.7,ease:"power3.inOut"}},{te + .15:.3f});')

    # provenance labels (per beat, except end)
    for bi in range(6):
        text = spec["labels"][bi]
        if not text:
            continue
        low = bi == 0 and hook["kind"] != "video"
        el.append(f'<div class="clip txt" data-start="{b[bi]:.3f}" data-duration="{b[bi + 1] - b[bi]:.3f}" data-track-index="6">'
                  f'<div id="lab{bi}" class="label{" low" if low else ""}">{esc(text)}</div></div>')
        tl.append(f'tl.fromTo("#lab{bi}",{{opacity:0,x:-20}},{{opacity:1,x:0,duration:.3,ease:"power2.out"}},{b[bi] + .1:.3f});')
        layer("provenance_label", text, b[bi], b[bi + 1], [62, 1618 if low else 500, 1018, 1662 if low else 544])

    # captions: one big kinetic line per narration beat (end line is carried by the end card)
    for c in caps[:-1]:
        i = c["i"]
        st, en = (0.0 if i == 0 else b[i]), b[i + 1]
        kws = set(spec["keywords"][i])
        parts = []
        for wi, (w, a, _) in enumerate(c["words"]):
            key = re.sub(r"[^A-Z-]", "", w.upper()) in kws
            parts.append(f'<span class="mask"><span id="w{i}_{wi}" class="w{" k" if key else ""}">{esc(w.upper())}</span></span>')
            if i == 0:
                # hook words are on screen from frame 0 (cover + hook)
                continue
            tl.append(f'tl.fromTo("#w{i}_{wi}",{{yPercent:115}},{{yPercent:0,duration:.28,ease:"power3.out"}},{max(st, a - .06):.3f});')
        cls = "cap hook" if i == 0 else "cap"
        under = ('<svg class="under" viewBox="0 0 520 34"><path id="under0" d="M4 22 C120 8 300 26 514 12" fill="none" '
                 'stroke="#8186F1" stroke-width="12" stroke-linecap="round" pathLength="1"/></svg>') if i == 0 else ""
        el.append(f'<div class="clip txt" data-start="{st:.3f}" data-duration="{en - st:.3f}" data-track-index="7">'
                  f'<div id="cap{i}" class="{cls}"><div class="line">{" ".join(parts)}</div>{under}</div></div>')
        if i == 0:
            tl.append('tl.fromTo("#cap0",{scale:1.06,transformOrigin:"0 0"},{scale:1,duration:.9,ease:"power2.out"},0);')
            tl.append('tl.fromTo("#under0",{strokeDasharray:1,strokeDashoffset:1},{strokeDashoffset:0,duration:.6,ease:"power2.out",immediateRender:false},.35);')
        size = 94 if i == 0 else 70
        layer("caption" if i else "hook_caption", c["text"].upper(), st, en, [62, 176, 1018, 176 + size * 3.1],
              words=[dict(text=w.upper(), start=round(a, 3), end=round(e_, 3)) for w, a, e_ in c["words"]], font=f"Archivo Black {size}px")

    # end card
    te = b[6]
    endline = caps[-1]
    el.append(f'<div class="clip end" data-start="{te:.3f}" data-duration="{total - te:.3f}" data-track-index="4"><div id="endpanel" class="panel"></div></div>')
    tl.append(f'tl.fromTo("#endpanel",{{opacity:0}},{{opacity:1,duration:.35,ease:"power1.out"}},{te:.3f});')
    el.append(f'<div class="clip end endtext txt" data-start="{te:.3f}" data-duration="{total - te:.3f}" data-track-index="9">'
              f'<div id="ek" class="kick">SNAP TO LEAGUE · BY EASYCHAMP</div>'
              f'<h2><span class="mask"><span id="e1" style="display:block">FREE.</span></span><span class="mask"><span id="e2" style="display:block;color:#A4A7FF">ANY SPORT.</span></span></h2>'
              f'<div class="url"><div id="efill" class="fill"></div><div id="eurl" class="t">snap.easychamp.com</div></div>'
              f'<div id="esub" class="sub">Photo of the board. Live league in seconds.</div></div>')
    wt = {w.strip(".").upper(): a for w, a, _ in endline["words"]}
    t_free = wt.get("FREE", te + 1.2) - .05
    t_any = wt.get("ANY", te + 1.8) - .05
    t_url = wt.get("TRY", te + 2.6) - .1
    tl.append(f'tl.fromTo("#ek",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.35,ease:"power2.out"}},{te + .2:.3f});')
    tl.append(f'tl.fromTo("#e1",{{yPercent:110}},{{yPercent:0,duration:.35,ease:"power4.out"}},{t_free:.3f});')
    tl.append(f'tl.fromTo("#e2",{{yPercent:110}},{{yPercent:0,duration:.35,ease:"power4.out"}},{t_any:.3f});')
    tl.append(f'tl.fromTo("#efill",{{scaleX:0}},{{scaleX:1,duration:.45,ease:"power3.out"}},{t_url:.3f});')
    tl.append(f'tl.fromTo("#eurl",{{opacity:0,x:-24}},{{opacity:1,x:0,duration:.35,ease:"power2.out"}},{t_url + .2:.3f});')
    tl.append(f'tl.fromTo("#esub",{{opacity:0}},{{opacity:1,duration:.4}},{t_url + .5:.3f});')
    layer("end_kicker", "SNAP TO LEAGUE · BY EASYCHAMP", te + .2, total, [62, 196, 1018, 232])
    layer("end_headline", "FREE.", t_free, total, [58, 246, 1018, 381])
    layer("end_headline", "ANY SPORT.", t_any, total, [58, 381, 1018, 516])
    layer("end_url", "snap.easychamp.com", t_url + .2, total, [62, 560, 1018, 664])
    layer("end_subline", "Photo of the board. Live league in seconds.", t_url + .5, total, [62, 696, 1002, 740])

    # transitions
    for t_w in ([b[1] - 0.2] if hook["kind"] == "video" else []) + [te - 0.2]:
        wid = f"cur{int(t_w * 100)}"
        el.append(f'<div class="clip wipe" data-start="{t_w:.3f}" data-duration="0.42" data-track-index="10"><div id="{wid}" class="curtain"></div></div>')
        tl.append(f'tl.fromTo("#{wid}",{{xPercent:-105,skewX:-8}},{{xPercent:0,skewX:-8,duration:.2,ease:"power2.in",immediateRender:false}},{t_w:.3f});')
        tl.append(f'tl.to("#{wid}",{{xPercent:105,duration:.22,ease:"power2.out"}},{t_w + .2:.3f});')
    if hook["kind"] == "video":
        # hard-cut wipe from real footage into the sheet
        pass

    el.append('<div class="topshade"></div>')
    el.append('<div class="brand txt"><b>EASYCHAMP</b><i>SNAP TO LEAGUE</i></div>')
    layer("brand_chip", "EASYCHAMP | SNAP TO LEAGUE", 0, total, [62, 92, 470, 140])
    el.append('<div id="progress" class="progress"></div>')
    tl.append(f'tl.fromTo("#progress",{{scaleX:0}},{{scaleX:1,duration:{total:.3f},ease:"none"}},0);')
    el.append(f'<audio id="mix" src="assets/{audio_rel}" data-start="0" data-duration="{total:.3f}" data-track-index="11"></audio>')

    doc = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=1080,height=1920">'
           f'<title>{esc(spec["title"])}</title><script src="assets/vendor/gsap.min.js"></script><style>{style}</style></head>'
           f'<body><div id="root" class="{"textless" if textless else ""}" data-composition-id="{comp_id}" data-start="0" data-duration="{total:.3f}" '
           f'data-width="1080" data-height="1920" data-fps="30">{"".join(el)}</div>'
           f'<script>const tl=gsap.timeline({{paused:true}});{"".join(tl)}window.__timelines["{comp_id}"]=tl;</script></body></html>')
    cnt = iter(range(1000))
    doc = re.sub(r'<div class="clip', lambda m: f'<div id="c{next(cnt)}" class="clip', doc)
    doc = doc.replace('<span class="mask">', '<span class="mask" data-layout-allow-overflow>')
    d = P / (f"reel-{n}" + ("-textless" if textless else ""))
    d.mkdir(exist_ok=True)
    (d / "index.html").write_text(doc)
    (d / "hyperframes.json").write_text('{"media": {"autoProxy": true}}\n')
    if not (d / "assets").exists():
        (d / "assets").symlink_to("../assets", target_is_directory=True)
    return layers


def main(only=None):
    summary = {}
    for reel, spec in SPECS.items():
        if only and reel[0] not in only:
            continue
        clips, starts, beats, total = plan(reel, spec)
        build_screen(reel, spec, beats, total)
        vout, mout, mix = build_audio(reel, spec, clips, starts, total)
        caps = caption_chunks(reel, spec, starts)
        layers = compose(reel, spec, caps, beats, total, f"audio/{reel[0]}-mix.wav", False)
        compose(reel, spec, caps, beats, total, f"audio/{reel[0]}-music.wav", True)
        out = P / "deliver" / reel
        out.mkdir(parents=True, exist_ok=True)
        write_srt(out / "captions.srt", caps)
        (out / "script.txt").write_text("\n".join(REELS[reel]) + "\n")
        (out / "caption.txt").write_text(spec["social"] + "\n")
        (out / "text-layers.json").write_text(json.dumps({
            "reel": reel, "canvas": [W, H], "fps": FPS, "duration_s": total,
            "coordinates": "box = [left, top, right, bottom] in output pixels; times in seconds",
            "note": "textless.mp4 contains none of these layers; product UI text inside real captures is not an overlay",
            "layers": layers}, indent=1) + "\n")
        summary[reel] = dict(total=total, beats=beats, starts=starts, music_in=spec["_music_in"], screen_map=spec["_screen_map"])
        print(reel, "total", total, "beats", beats, flush=True)
    rep = P / "reports/build-plan.json"
    old = json.loads(rep.read_text()) if rep.exists() else {}
    old.update(summary)
    rep.write_text(json.dumps(old, indent=1) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
