"""Score the app on real screenshots from other platforms (Challonge, start.gg, Score7, LeagueRepublic).

Truth for each screenshot was read from the page's HTML, not the image (tests/fixtures/external/*.truth.json).
python scripts/eval_external.py [http://localhost:8077]  ->  prints a table, writes data/external_eval.json
"""
import json
import re
import sys
import time
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8077"
DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "external"


def n(s):
    return re.sub(r"[^a-z0-9]", "", str(s or "").casefold())


def match_key(m):
    sides = frozenset({(n(m.get("home")), m.get("homeScore")), (n(m.get("away")), m.get("awayScore"))})
    return sides, n(m.get("winner"))


def same_name(a, b):
    a, b = n(a), n(b)  # sponsor tags ("CL The Bloodless") count as the same player
    return a == b or (min(len(a), len(b)) > 3 and (a.endswith(b) or b.endswith(a)))


def same_result(truth, read):
    for h, a, hs, as_ in ((read["home"], read["away"], read["homeScore"], read["awayScore"]),
                          (read["away"], read["home"], read["awayScore"], read["homeScore"])):
        if same_name(truth["home"], h) and same_name(truth["away"], a) and truth.get("homeScore") == hs and truth.get("awayScore") == as_:
            return not truth.get("winner") or not read.get("winner") or same_name(truth["winner"], read["winner"])
    return False


def team_in(name, names):
    return any(n(name) == x or (len(n(name)) > 4 and (n(name) in x or x in n(name))) for x in names)


rows = []
for truth_file in sorted(DIR.glob("*.truth.json")):
    name = truth_file.name.replace(".truth.json", "")
    truth = json.loads(truth_file.read_text())
    t0 = time.monotonic()
    try:
        r = httpx.post(f"{BASE}/api/snap", files={"image": (f"{name}.png", (DIR / f"{name}.png").read_bytes(), "image/png")}, timeout=240)
    except httpx.HTTPError as e:
        rows.append({"shot": name, "kind": "error", "detail": str(e)[:160]})
        print(rows[-1], flush=True)
        continue
    secs = round(time.monotonic() - t0, 1)
    if r.status_code != 200:
        rows.append({"shot": name, "kind": "error", "status": r.status_code, "detail": r.text[:160], "seconds": secs})
        print(rows[-1], flush=True)
        continue
    ex = r.json()["extraction"]
    if truth.get("matches"):
        pool = list(ex["matches"])
        correct = 0
        for w in truth["matches"]:
            hit = next((m for m in pool if same_result(w, m)), None)
            if hit:
                correct += 1
                pool.remove(hit)
        rows.append({"shot": name, "kind": "matches", "truth": len(truth["matches"]), "correct": correct,
                     "missing": len(truth["matches"]) - correct, "extra": len(pool), "seconds": secs,
                     "reader": r.json()["backend"]})
    else:
        names = [n(x.get("name") or x.get("team")) for x in truth.get("standings", [])]
        read = [n(x["team"]) for x in ex.get("table", [])] or [n(t) for t in ex.get("teams", [])]
        found = sum(1 for x in names if team_in(x, read))
        in_order = sum(1 for i, x in enumerate(names) if i < len(read) and team_in(x, [read[i]]))
        rows.append({"shot": name, "kind": "table", "truth": len(names), "correct": found, "inOrder": in_order,
                     "seconds": secs, "reader": r.json()["backend"]})
    print(rows[-1], flush=True)

out = Path(__file__).resolve().parent.parent / "data" / "external_eval.json"
out.write_text(json.dumps(rows, indent=1))
