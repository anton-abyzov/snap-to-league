"""Places and totals for leaderboards (races, heats, quizzes, cup stacking).

Values are read as written ("23", "1:02.34", "DNF"). Totals are summed from the rounds when the
board has none; places are recomputed from the totals, ties share a place, and a DNF/DQ note or a
missing value always ranks last. The board's own places are kept only to flag disagreements.
"""
from __future__ import annotations

import re

from .schema import Flag, Leaderboard


def number(v: str | None) -> float | None:
    """'23' -> 23, '1:02.34' -> 62.34, '12.5 s' -> 12.5, 'DNF' -> None."""
    if v is None:
        return None
    s = v.strip().casefold().replace(",", ".")
    m = re.fullmatch(r"(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)", s)
    if m:
        h, mnt, sec = m.groups()
        return (int(h or 0) * 3600) + int(mnt) * 60 + float(sec)
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None


def rank(lb: Leaderboard) -> tuple[list[dict], list[Flag]]:
    rows, flags = [], []
    for e in lb.entries:
        total = number(e.total)
        vals = [number(v) for v in e.values]
        if total is None and any(v is not None for v in vals):
            total = sum(v for v in vals if v is not None)
            if lb.lower_is_better and any(v is None for v in vals):
                total = None  # a missed heat cannot be summed as a fast time
        out = bool(e.note and re.search(r"dnf|dns|dq|dsq|out", e.note.casefold()))
        rows.append({"name": e.name, "values": e.values, "total": e.total, "score": None if out else total,
                     "boardPlace": e.place, "note": e.note})
    ranked = sorted(rows, key=lambda r: (r["score"] is None, (r["score"] if lb.lower_is_better else -(r["score"] or 0))
                                           if r["score"] is not None else 0, r["name"].casefold()))
    place, prev = 0, object()
    for i, r in enumerate(ranked):
        if r["score"] is None:
            r["place"] = None
            continue
        if r["score"] != prev:
            place, prev = i + 1, r["score"]
        r["place"] = place
        if r["boardPlace"] and r["boardPlace"] != place:
            flags.append(Flag(level="warn", source="check",
                              message=f"The board puts {r['name']} {ordinal(r['boardPlace'])}, the numbers say {ordinal(place)}"))
    return ranked, flags


def ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
