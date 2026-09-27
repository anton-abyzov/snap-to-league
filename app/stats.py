"""Import statistics for the stats page and the evidence report."""
from __future__ import annotations

from collections import Counter

from . import store


def totals() -> dict:
    jobs = [j for j in store.collection("jobs").all() if j.get("status") == "done"]
    photos = [p for j in jobs for p in j.get("photos", [])]
    read = [p for p in photos if p.get("status") == "done"]
    leagues = store.collection("leagues").all()
    matches_read = sum(p.get("matches") or 0 for p in read)
    fixed = sum(lg.get("corrections", 0) for lg in leagues)
    kept = sum(len(lg.get("matches", [])) for lg in leagues if lg.get("jobIds"))
    readers = Counter((p.get("reader") or "unknown").split(" + ")[0] for p in read)
    secs = sorted(p["seconds"] for p in read if p.get("seconds"))
    return {
        "imports": len(jobs),
        "photos": len(photos),
        "photosRead": len(read),
        "photosFailed": len(photos) - len(read),
        "matchesRead": matches_read,
        "leagues": len(leagues),
        "published": sum(1 for lg in leagues if (lg.get("published") or {}).get("mode") == "live"),
        "corrections": fixed,
        "matchesSaved": kept,
        "untouchedShare": round(1 - fixed / kept, 3) if kept else None,
        "medianSeconds": secs[len(secs) // 2] if secs else None,
        "readers": dict(readers.most_common()),
        "sports": dict(Counter(lg.get("sport", "other") for lg in leagues).most_common()),
    }
