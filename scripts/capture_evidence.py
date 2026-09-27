"""Headless screenshots of the real app for the evidence report. Never enters the publish PIN,
so nothing is written to EasyChamp.

python scripts/capture_evidence.py [base_url] [out_dir]
"""
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8077"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "data/evidence")
OUT.mkdir(parents=True, exist_ok=True)
FIX = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
PHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True}
log = {}


async def wait_review(pg):
    await pg.wait_for_selector("#review:not([hidden])", timeout=180000)
    await pg.wait_for_timeout(600)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        desk = await b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        pg = await desk.new_page()
        await pg.goto(BASE)
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=OUT / "01-home-desktop.png")

        ph = await b.new_context(**PHONE)
        pg = await ph.new_page()
        await pg.goto(BASE)
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=OUT / "02-home-phone.png")

        # two scoresheets chosen from the library: carousel, upload, reading
        await pg.set_input_files("#library", [str(FIX / "sheet1.jpg"), str(FIX / "sheet2.jpg")])
        await pg.wait_for_timeout(500)
        await pg.screenshot(path=OUT / "03-tray-phone.png")
        await pg.click("#read")
        await pg.wait_for_timeout(2500)
        await pg.evaluate("window.scrollTo(0,0)")
        await pg.screenshot(path=OUT / "04-reading-phone.png")
        await wait_review(pg)
        log["sheets"] = await pg.evaluate("({meta: document.getElementById('meta').textContent, flags: [...document.querySelectorAll('.flag')].map(f => f.innerText.replace(/\\n/g, ' ')), matches: document.querySelectorAll('.match').length})")
        await pg.evaluate("document.getElementById('review').scrollIntoView()")
        await pg.screenshot(path=OUT / "05-review-sheets-phone.png", full_page=True)

        # update flow: save week 3 only, then add week 4 as an update to that league
        pg = await ph.new_page()
        await pg.goto(BASE)
        await pg.set_input_files("#library", [str(FIX / "sheet1.jpg")])
        await pg.click("#read")
        await wait_review(pg)
        await pg.fill("#name", "Evidence Futsal League")
        await pg.click("#publish")  # no PIN: saves a board, EasyChamp publish stays a dry run
        await pg.wait_for_selector("#done:not([hidden])", timeout=60000)
        await pg.screenshot(path=OUT / "06-saved-board-phone.png")
        await pg.click("#again")
        await pg.set_input_files("#library", [str(FIX / "sheet2.jpg")])
        await pg.click("#read")
        await wait_review(pg)
        log["update"] = await pg.evaluate("[...document.querySelectorAll('.change')].map(c => c.innerText.replace(/\\n/g, ' '))")
        await pg.evaluate("window.scrollTo(0, document.getElementById('changes-box').getBoundingClientRect().top + window.scrollY - 190)")
        await pg.screenshot(path=OUT / "07-update-changes-phone.png")

        # bracket on desktop: table and bracket view
        pg = await desk.new_page()
        await pg.goto(BASE)
        await pg.click("[data-sample='bracket']")
        await wait_review(pg)
        await pg.evaluate("document.getElementById('review').scrollIntoView()")
        await pg.screenshot(path=OUT / "08-review-bracket-desktop.png")

        # competitor screenshot read in the app
        pg = await desk.new_page()
        await pg.goto(BASE)
        await pg.set_input_files("#library", [str(FIX / "external" / "challonge-1.png")])
        await pg.click("#read")
        await wait_review(pg)
        log["challonge"] = await pg.evaluate("document.getElementById('meta').textContent")
        await pg.evaluate("document.getElementById('review').scrollIntoView()")
        await pg.screenshot(path=OUT / "09-review-challonge-desktop.png")

        # stats page
        pg = await desk.new_page()
        await pg.goto(f"{BASE}/stats")
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=OUT / "10-stats-desktop.png")
        await b.close()
    (OUT / "capture-log.json").write_text(json.dumps(log, indent=1))
    print(json.dumps(log, indent=1))


asyncio.run(main())
