"""Headless phone screencasts of EXISTING published demo leagues (nothing new is published).

  PWDEBUG=0 python3 scripts/capture_sites.py pit board smash
Same screencast method as capture_app.py (1170x2532 device pixels). A cache-busting query string is
added to every URL. The owner-operated edge answers default HeadlessChrome with a 'busy' page, so an
identifying capture User-Agent is sent (see ../snap-to-league/reports/PRODUCT-PROOF.md).
"""
import asyncio
import base64
import json
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

from capture_app import EASE, UA

P = Path(__file__).resolve().parent.parent
RAW = P / "capture/raw"
SITES = {
    "pit": ("https://shellhacks-panther-pit-break-c.at.easychamp.com/champ/3b4dfb25-4fa3-4124-8e73-5afc6f4abd75",
            [("Knockout", 2600), ("Standings", 3200)]),
    "board": ("https://snap.easychamp.com/l/b766d1be06", [("BRACKET", 2600), ("TOP SCORERS", 3000)]),
    "smash": ("https://shellhacks-midnight-smash--dem.at.easychamp.com/champ/b04bac02-216e-4492-bcdf-0ac2a4ef0881",
              [("Knockout", 1600), ("click:SF", 1800), ("click:F", 3000)]),
}
FIND = """(txt) => { const els = [...document.querySelectorAll('h1,h2,h3,h4,div,span,section > *')]
  .filter(e => e.children.length === 0 && e.textContent.trim().toLowerCase() === txt.toLowerCase() && e.getBoundingClientRect().height > 0);
  const el = els.sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top)
    .find(e => e.getBoundingClientRect().top + scrollY > 300) || els[0];
  if (!el) return null; const b = el.getBoundingClientRect(); return [b.top + scrollY, b.x, b.width, b.height]; }"""


async def run(name, url, stops):
    events, frames = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, user_agent=UA,
                                  is_mobile=True, has_touch=True)
        pg = await ctx.new_page()
        cdp = await ctx.new_cdp_session(pg)

        def on_frame(ev):
            frames.append((ev["metadata"]["timestamp"], ev["data"]))
            asyncio.ensure_future(cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]}))
        cdp.on("Page.screencastFrame", on_frame)
        resp = await pg.goto(f"{url}?v={int(time.time())}", wait_until="networkidle", timeout=90000)
        await pg.wait_for_timeout(1500)
        await cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 90, "maxWidth": 1170, "maxHeight": 2532})
        await pg.wait_for_timeout(300)
        events.append({"t": round(time.time(), 3), "event": "top"})
        await pg.wait_for_timeout(1800)
        for label, hold in stops:
            if label.startswith("click:"):
                chip = pg.locator("button", has_text=label[6:]).filter(has_text=label[6:])
                chip = [c for c in await chip.all() if (await c.inner_text()).strip() == label[6:]]
                if chip:
                    await chip[0].click()
                    events.append({"t": round(time.time(), 3), "event": label})
                    await pg.wait_for_timeout(hold)
                continue
            pos = await pg.evaluate(FIND, label)
            if not pos:
                print(name, "missing", label)
                continue
            await pg.evaluate(EASE, [max(0, pos[0] - 70), 1100])
            events.append({"t": round(time.time(), 3), "event": label, "doc_y": pos[0]})
            await pg.wait_for_timeout(hold)
        events.append({"t": round(time.time(), 3), "event": "end"})
        await cdp.send("Page.stopScreencast")
        await pg.wait_for_timeout(200)
        try:
            await pg.screenshot(path=str(RAW / f"site-{name}-view.png"), timeout=15000)
        except Exception as exc:  # stills are optional; the screencast is the deliverable source
            print(name, "still skipped", exc.__class__.__name__)
        text = await pg.inner_text("body")
        status, final_url = resp.status, pg.url
        await ctx.close()
        await b.close()
    fdir = RAW / f"site-{name}"
    fdir.mkdir(parents=True, exist_ok=True)
    index = []
    for i, (ts, b64) in enumerate(frames):
        (fdir / f"{i:05}.jpg").write_bytes(base64.b64decode(b64))
        index.append([round(ts, 4), f"{i:05}.jpg"])
    meta = {"name": name, "url": final_url, "http_status": status, "events": events, "frames": index,
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "user_agent": UA, "text_excerpt": text[:1500]}
    (RAW / f"site-{name}.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(name, status, len(index), "frames", [(e["event"], round(e["t"] - index[0][0], 2)) for e in events])


async def main(names):
    for n in names:
        await run(n, *SITES[n])


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or list(SITES)))
