"""Headless phone recordings of the live Snap to League app (https://snap.easychamp.com).

One real import per reel: a built-in sample (soccer) or an uploaded synthetic demo photo (hoops,
padel, smash). Nothing is published: the flow stops at the review screen. The header model chip
and the photo-reader picker are hidden with CSS (no model or vendor names on screen); everything
else is the untouched live product.

  PWDEBUG=0 python3 scripts/capture_app.py soccer hoops padel smash
Recording uses the Chrome DevTools screencast at device pixels (390x844 CSS at 3x = 1170x2532),
because Playwright's recordVideo delivers 1x frames. Frames + wall-clock timestamps are written to
capture/raw/app-<name>/ and assembled at 30 fps by scripts/assemble_screencast.py.
capture/raw/app-<name>.json holds event times (same clock) and element rects;
capture/raw/app-<name>-*.png are element stills taken after the recorded window.
"""
import asyncio
import base64
import json
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

P = Path(__file__).resolve().parent.parent
RAW = P / "capture/raw"
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
      "Version/18.0 Mobile/15E148 Safari/604.1 EasyChampReelCapture/2026 (authorized product recording)")
HIDE = "#chips,#reader-box{display:none!important}"
JOBS = {
    "soccer": {"sample": "shellhacks-groups", "sport": "soccer"},
    "hoops": {"file": "assets/synthetic/hoops-bracket.jpg", "sport": "basketball"},
    "padel": {"file": "assets/synthetic/padel-ladder.jpg", "sport": "padel"},
    "smash": {"file": "assets/synthetic/smash-screenshot.png", "sport": "smash"},
}
EASE = """async ([y, ms]) => { const y0 = scrollY, t0 = performance.now();
  await new Promise(done => { const step = (t) => { const k = Math.min(1, (t - t0) / ms);
    const e = k < .5 ? 4*k*k*k : 1 - Math.pow(-2*k + 2, 3) / 2; scrollTo(0, y0 + (y - y0) * e);
    k < 1 ? requestAnimationFrame(step) : done(); }; requestAnimationFrame(step); }); }"""


async def run(name, job):
    RAW.mkdir(parents=True, exist_ok=True)
    events = []
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, user_agent=UA,
                                  is_mobile=True, has_touch=True)
        pg = await ctx.new_page()
        t0 = 0.0
        frames = []
        cdp = await ctx.new_cdp_session(pg)

        def on_frame(ev):
            frames.append((ev["metadata"]["timestamp"], ev["data"]))
            asyncio.ensure_future(cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]}))
        cdp.on("Page.screencastFrame", on_frame)

        async def mark(label, sel=None):
            e = {"t": round(time.time(), 3), "event": label}
            if sel:
                r = await pg.evaluate("s => { const el = document.querySelector(s); if (!el) return null;"
                                      " const b = el.getBoundingClientRect(); return [b.x, b.y, b.width, b.height]; }", sel)
                e["rect_css"] = r
            events.append(e)
            print(name, e, flush=True)

        async def scroll_to(sel, top=90, ms=900):
            y = await pg.evaluate("([s, top]) => { const el = document.querySelector(s);"
                                  " return el ? el.getBoundingClientRect().top + scrollY - top : scrollY; }", [sel, top])
            await pg.evaluate(EASE, [max(0, y), ms])

        await pg.goto(f"https://snap.easychamp.com/?v={int(time.time())}", wait_until="networkidle")
        await pg.add_style_tag(content=HIDE)
        await cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 90, "maxWidth": 1170, "maxHeight": 2532,
                                                 "everyNthFrame": 1})
        await pg.wait_for_timeout(400)
        await mark("home")
        await pg.wait_for_timeout(1200)
        if "sample" in job:
            btn = f'[data-sample="{job["sample"]}"]'
            await scroll_to(".actions.small", top=330, ms=800)
            await pg.wait_for_timeout(500)
            await mark("tap-sample", btn)
            await pg.click(btn)
        else:
            await scroll_to(".hero-copy .actions", top=360, ms=800)
            await pg.wait_for_timeout(500)
            await mark("tap-choose", 'label[for="library"]')
            await pg.set_input_files("#library", str(P / job["file"]))
        await pg.wait_for_timeout(1300)
        await mark("tray", "#tray")
        if "file" in job:
            target = "#read" if await pg.locator("#read").is_visible() else "#read-now"
            await mark("tap-read", target)
            await pg.click(target)
        for _ in range(240):
            await pg.wait_for_timeout(250)
            if await pg.locator("#review").is_visible():
                break
        await mark("review", "#review")
        for _ in range(60):
            if not await pg.locator("#checking:not(.finished)").is_visible():
                break
            await pg.wait_for_timeout(250)
        await mark("checked", "#checking")
        await pg.wait_for_timeout(600)
        await scroll_to("#review", top=70, ms=700)
        await pg.wait_for_timeout(300)
        await mark("sport", "#sport")
        await pg.select_option("#sport", job["sport"])
        await pg.wait_for_timeout(1500)
        await mark("matches", "#matches")
        await pg.wait_for_timeout(1400)
        await scroll_to("#table-title", top=70, ms=1000)
        await pg.wait_for_timeout(200)
        await mark("table", "#table")
        await pg.wait_for_timeout(2800)
        if await pg.locator("#table .bracket").count():
            await pg.evaluate("""async (ms) => { const el = [document.querySelector('#table .bracket'), document.querySelector('#table')].find(e => e && e.scrollWidth > e.clientWidth + 4) || document.querySelector('#table');
              const x1 = el.scrollWidth - el.clientWidth, t0 = performance.now();
              await new Promise(done => { const step = (t) => { const k = Math.min(1, (t - t0) / ms);
                const e = k < .5 ? 4*k*k*k : 1 - Math.pow(-2*k + 2, 3) / 2; el.scrollLeft = x1 * e;
                k < 1 ? requestAnimationFrame(step) : done(); }; requestAnimationFrame(step); }); }""", 1600)
            await mark("bracket-final", "#table .bracket")
            await pg.wait_for_timeout(2600)
        if await pg.locator("#scorers-box").is_visible():
            await scroll_to("#scorers-box", top=70, ms=900)
            await pg.wait_for_timeout(200)
            await mark("scorers", "#scorers-box")
            await pg.wait_for_timeout(2600)
        await scroll_to("#publish", top=520, ms=800)
        await pg.wait_for_timeout(200)
        await mark("publish-button", "#publish")
        await pg.wait_for_timeout(1600)
        await mark("end")
        await cdp.send("Page.stopScreencast")
        await pg.wait_for_timeout(300)
        # Stills after the recorded window (the tail of the video is trimmed away).
        for sel, tag in [("#review", "review"), ("#table", "table"), ("#matches", "matches"),
                         ("#scorers-box", "scorers"), ("#flags", "flags")]:
            loc = pg.locator(sel)
            if await loc.is_visible() and (await loc.bounding_box() or {}).get("height", 0) > 10:
                await loc.screenshot(path=str(RAW / f"app-{name}-{tag}.png"))
        data = {"name": name, "job": job, "events": events, "viewport": [390, 844], "dsf": 2,
                "sport_value": await pg.eval_on_selector("#sport", "e => e.value"),
                "competition": await pg.eval_on_selector("#name", "e => e.value"),
                "table_text": await pg.inner_text("#table"), "matches_text": await pg.inner_text("#matches"),
                "flags_text": await pg.inner_text("#flags"), "checking_text": await pg.inner_text("#checking"),
                "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "url": pg.url, "user_agent": UA,
                "css_hidden": HIDE}
        await ctx.close()
        await b.close()
        fdir = RAW / f"app-{name}"
        fdir.mkdir(exist_ok=True)
        index = []
        for i, (ts, b64) in enumerate(frames):
            fp = fdir / f"{i:05}.jpg"
            fp.write_bytes(base64.b64decode(b64))
            index.append([round(ts, 4), fp.name])
        data["frames"] = index
        (RAW / f"app-{name}.json").write_text(json.dumps(data, indent=2) + "\n")
        print(name, len(index), "frames over", round(index[-1][0] - index[0][0], 2), "s", flush=True)


async def main(names):
    for n in names:
        await run(n, JOBS[n])


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or list(JOBS)))
