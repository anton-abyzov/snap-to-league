"""Import jobs: several photos read in parallel, with progress the phone can poll.

A job goes queued -> reading -> done (or error). Each photo has its own status, reader and time, so
the review screen can show a live carousel while the readers work. When every photo is read, the
matches are combined (merge.combine), checked (standings.checks) and, for an existing league,
compared with what is saved (merge.review).
"""
from __future__ import annotations

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import store
from .extract import extract
from .merge import combine, review
from .schema import Extraction, Flag, Match
from .standings import checks

POOL = ThreadPoolExecutor(max_workers=3)      # jobs
PHOTOS = ThreadPoolExecutor(max_workers=4)    # photos across all jobs
JOBS: dict[str, dict] = {}
LOCK = threading.Lock()


def create(paths: list[Path], league: dict | None, reader: str | None, owner: str) -> dict:
    job = {
        "id": uuid.uuid4().hex[:12], "status": "reading", "created": time.time(), "owner": owner,
        "leagueId": league["id"] if league else None, "reader": reader,
        "photos": [{"image": p.name, "status": "queued", "seconds": None, "matches": 0, "reader": None,
                    "error": None} for p in paths],
        "extraction": None, "flags": [], "standings": [], "review": None, "seconds": None,
    }
    with LOCK:
        JOBS[job["id"]] = job
    POOL.submit(_run, job, paths, league)
    return job


def get(job_id: str) -> dict | None:
    with LOCK:
        job = JOBS.get(job_id)
    return job or store.collection("jobs").get(job_id)


def _run(job: dict, paths: list[Path], league: dict | None) -> None:
    t0 = time.monotonic()
    results: list[tuple[int, Extraction, list[str]] | None] = [None] * len(paths)

    def one(i: int, path: Path):
        photo = job["photos"][i]
        photo["status"] = "reading"
        try:
            ex, _rows, backend, secs, notes = extract(path, job["reader"])
            photo.update(status="done", seconds=secs, matches=len(ex.matches), reader=backend,
                         competition=ex.competition, sport=ex.sport)
            results[i] = (i, ex, notes)
        except Exception as e:  # one unreadable photo must not sink the others  # noqa: BLE001
            photo.update(status="error", error=str(e)[:200])

    for future in [PHOTOS.submit(one, i, p) for i, p in enumerate(paths)]:
        future.result()
    read = [r for r in results if r]
    if not read:
        job.update(status="error", seconds=round(time.monotonic() - t0, 1))
        _save(job)
        return

    known_teams = [t for m in (league or {}).get("matches", []) for t in (m["home"], m["away"])]
    known_players = [g["player"] for m in (league or {}).get("matches", []) for g in m.get("goals", [])]
    combined = combine([ex.matches for _, ex, _ in read], known_teams, known_players)
    first = read[0][1]
    extraction = Extraction(
        competition=(league or {}).get("name") or next((ex.competition for _, ex, _ in read if ex.competition), "Untitled cup"),
        sport=(league or {}).get("sport") or first.sport,
        teams=combined["teams"], matches=combined["matches"],
        rules_notes=[n for _, ex, _ in read for n in ex.rules_notes],
        uncertain=list(dict.fromkeys(u for _, ex, _ in read for u in ex.uncertain)),
        table=next((ex.table for _, ex, _ in read if ex.table), []),
    )
    if not extraction.teams and extraction.table:
        extraction.teams = [r.team for r in extraction.table]
    table, flags = checks(extraction, [])
    for i, _, notes in read:
        tag = f"Photo {i + 1}: " if len(paths) > 1 else ""
        flags += [Flag(level="warn", message=tag + n, source="second") for n in notes]
    for c in combined["conflicts"]:
        flags.append(Flag(level="error", source="merge",
                          message=f"Photos {c['photos'][0]} and {c['photos'][1]} disagree on {c['home']} v {c['away']}: "
                                  f"{c['first']} or {c['second']}; the first is kept"))
    for before, after in combined["renamed"].items():
        flags.append(Flag(level="info", source="match", message=f'Read "{before}" as {after}'))
    job.update(extraction=extraction.model_dump(), standings=[r.model_dump() for r in table],
               flags=[f.model_dump() for f in flags], seconds=round(time.monotonic() - t0, 1), status="done")
    if league:
        job["review"] = review(league["matches"], [Match.model_validate(m) for m in job["extraction"]["matches"]])
        for before, after in job["review"]["renamed"].items():
            job["flags"].append(Flag(level="info", source="match",
                                     message=f'Matched "{before}" to {after} in {league["name"]}').model_dump())
    _save(job)



def _save(job: dict) -> None:
    store.collection("jobs").put({k: v for k, v in job.items()})
