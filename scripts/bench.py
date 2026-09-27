"""Compare vision models on the sample photos: accuracy, seconds and dollars per photo.

python scripts/bench.py openai/gpt-6-astra google/gemini-3.8-flash ...
Needs OPENROUTER_API_KEY. Truth = tests/fixtures/*_extract.json (checked by hand).
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import extract  # noqa: E402

FIX = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
PHOTOS = {"board": FIX / "board.jpg", "bracket": FIX / "bracket.jpg"}


def key(m):
    """Same result regardless of which side was written first."""
    sides = frozenset({(m.home.casefold(), m.homeScore), (m.away.casefold(), m.awayScore)})
    winner = m.winner.casefold() if m.winner and m.stage != "group" else None  # a group game has no "winner" field
    return (sides, m.status, winner)


def truth(name):
    ex, _ = extract._parse((FIX / f"{name}_extract.json").read_text())
    return {key(m) for m in ex.matches}


rows = []
TRIALS = int(os.environ.get("TRIALS", "3"))
for model in sys.argv[1:]:
    os.environ["OPENROUTER_MODEL"] = model
    for name, photo in [p for p in PHOTOS.items() for _ in range(TRIALS)]:
        t0 = time.monotonic()
        try:
            ex, _ = extract._parse(extract.openrouter(photo))
            got = {key(m) for m in ex.matches}
            want = truth(name)
            right = len(got & want)
            res = f"{right}/{len(want)}" + ("" if got == want else f" (+{len(got - want)} wrong)")
            if got != want:
                print("   wrong:", sorted(str(k) for k in got - want)[:3], flush=True)
        except Exception as e:  # report and keep going
            res = f"error: {str(e)[:80]}"
        secs = time.monotonic() - t0
        cost = extract.LAST_USAGE.get("cost")
        rows.append((model, name, res, round(secs, 1), cost))
        print(model, name, res, f"{secs:.1f}s", f"${cost:.4f}" if cost is not None else "$?", flush=True)
json.dump(rows, open(FIX.parent.parent / "data" / "bench.json", "w"), indent=1)
