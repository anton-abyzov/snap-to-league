"""Import jobs: several photos read in parallel, with progress the phone can poll.

A job goes queued -> reading -> done (or error). Each photo has its own status, reader and time, so
the review screen can show a live carousel while the readers work. As soon as the main reader has
read every photo, the matches are combined (merge.combine), checked (standings.checks) and, for an
existing league, compared with what is saved (merge.review). The second reader keeps checking in the
background and adds a card wherever it reads a result differently.
"""
from __future__ import annotations

import hashlib
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import store
from . import extract as extract_mod
from .merge import combine, known_scorers, review
from .schema import Extraction, Flag, Match
from .standings import checks
from .ranking import rank

POOL = ThreadPoolExecutor(max_workers=3)      # jobs
PHOTOS = ThreadPoolExecutor(max_workers=4)    # photos across all jobs
JOBS: dict[str, dict] = {}
READS = store.collection("reads")            # photo sha256 -> its read, so a re-upload costs nothing
LOCK = threading.Lock()


def create(paths: list[Path], league: dict | None, reader: str | None, owner: str) -> dict:
    """league is a saved league, or the unsaved draft on screen ({"id": None, name, sport, matches}):
    either way the new photos are compared with it and the review shows only what they change."""
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


def _plan(reader: str | None) -> tuple[str | None, str | None]:
    """Main reader and background checker for this import, or (None, None) for the single-reader modes."""
    if os.environ.get("SNAP_BACKEND") or not os.environ.get("OPENROUTER_API_KEY"):
        return None, None
    main = reader if reader in extract_mod.READERS else extract_mod.PRIMARY
    second = extract_mod.SECOND if extract_mod.SECOND and extract_mod.SECOND != main else None
    return main, second


def _run(job: dict, paths: list[Path], league: dict | None) -> None:
    """Show the main reader's result as soon as it is in; the second reader checks in the background."""
    t0 = time.monotonic()
    main, second = _plan(job["reader"])
    results: list[tuple[int, Extraction, list[str]] | None] = [None] * len(paths)
    checks_pending: list = []

    def read_main(i: int, path: Path):
        photo = job["photos"][i]
        photo["status"] = "reading"
        t = time.monotonic()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        photo["hash"] = digest[:16]
        seen = None if path.name.startswith("sample-") else READS.get(digest)
        if seen:  # the same photo again: reuse its read, no model call, nothing to double-check
            ex = Extraction.model_validate(seen["ex"])
            photo.update(status="done", seconds=round(time.monotonic() - t, 1), matches=len(ex.matches),
                         reader=seen["reader"], same=True, competition=ex.competition, sport=ex.sport)
            results[i] = (i, ex, [])
            return
        try:
            if main:
                ex, _rows = extract_mod._read("openrouter", path, main)
                name, notes = main.split("/")[-1], []
            else:
                ex, _rows, name, _secs, notes = extract_mod.extract(path, job["reader"])
            photo.update(status="done", seconds=round(time.monotonic() - t, 1), matches=len(ex.matches),
                         reader=name, competition=ex.competition, sport=ex.sport)
            results[i] = (i, ex, notes)
            if not path.name.startswith("sample-"):
                READS.put({"id": digest, "ex": ex.model_dump(), "reader": name, "at": time.time()})
        except Exception as e:  # noqa: BLE001  one unreadable photo must not sink the others
            photo.update(status="error", error=str(e)[:200])

    def read_second(i: int, path: Path):
        try:
            return extract_mod._read("openrouter", path, second)[0]
        except Exception:  # noqa: BLE001  the check is optional
            return None

    second_jobs = {i: PHOTOS.submit(read_second, i, p) for i, p in enumerate(paths)
                   if p.name.startswith("sample-") or READS.get(hashlib.sha256(p.read_bytes()).hexdigest()) is None} if second else {}
    for future in [PHOTOS.submit(read_main, i, p) for i, p in enumerate(paths)]:
        future.result()

    # a photo the main reader could not read falls back to the checker's read
    for i, photo in enumerate(job["photos"]):
        if results[i] is None and i in second_jobs:
            other = second_jobs[i].result()
            if other is not None and (other.matches or other.table):
                name = second.split("/")[-1]
                photo.update(status="done", matches=len(other.matches), reader=name, error=None,
                             seconds=round(time.monotonic() - t0, 1))
                results[i] = (i, other, ["The first read failed, so this is the backup read; check it"])
                second_jobs.pop(i)

    read = [r for r in results if r]
    if not read:
        job.update(status="error", seconds=round(time.monotonic() - t0, 1))
        _save(job)
        return
    _finish(job, read, paths, league, t0)
    if not second_jobs:
        _save(job)
        return

    # background check: add cards as each second opinion arrives
    job["checking"] = {"model": second.split("/")[-1], "done": 0, "total": len(second_jobs), "differences": 0}
    for photo in job["photos"]:
        photo["check"] = "pending" if photo["status"] == "done" else None
    _save(job)
    for i, fut in second_jobs.items():
        other = fut.result()
        photo = job["photos"][i]
        if other is None:
            photo["check"] = "failed"
        else:
            base = next(ex for j, ex, _ in read if j == i) if any(j == i for j, _, _ in read) else None
            notes = extract_mod.disagreements(base, other, second.split("/")[-1]) if base else []
            tag = f"Photo {i + 1}: " if len(paths) > 1 else ""
            job["flags"] += [Flag(level="warn", message=tag + n, source="second").model_dump() for n in notes]
            photo["check"] = "differs" if notes else "agrees"
            job["checking"]["differences"] += len(notes)
        job["checking"]["done"] += 1
    job["checking"]["finished"] = True
    job["seconds_checked"] = round(time.monotonic() - t0, 1)
    _save(job)


def _finish(job: dict, read: list, paths: list[Path], league: dict | None, t0: float) -> None:
    known_teams = [t for m in (league or {}).get("matches", []) for t in (m["home"], m["away"])]
    known_players = known_scorers((league or {}).get("matches", []))
    combined = combine([ex.matches for _, ex, _ in read], known_teams, known_players,
                       [Match.model_validate(m) for m in (league or {}).get("matches", [])])
    first = read[0][1]
    extraction = Extraction(
        competition=(league or {}).get("name") or next((ex.competition for _, ex, _ in read if ex.competition), "Untitled cup"),
        sport=(league or {}).get("sport") or first.sport,
        teams=combined["teams"], matches=combined["matches"],
        rules_notes=[n for _, ex, _ in read for n in ex.rules_notes],
        uncertain=list(dict.fromkeys(u for _, ex, _ in read for u in ex.uncertain)),
        table=next((ex.table for _, ex, _ in read if ex.table), []),
        leaderboard=max((ex.leaderboard for _, ex, _ in read if ex.leaderboard), key=lambda lb: len(lb.entries), default=None),
    )
    if not extraction.teams and extraction.table:
        extraction.teams = [r.team for r in extraction.table]
    table, flags = checks(extraction, [])
    if extraction.leaderboard:
        ranked, rank_flags = rank(extraction.leaderboard)
        flags += rank_flags
        job["ranking"] = ranked
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
    same = [i + 1 for i, p in enumerate(job["photos"]) if p.get("same")]
    if same and league:
        which = "This is" if len(paths) == 1 else f"Photo {', '.join(map(str, same))} is"
        job["flags"].insert(0, Flag(level="info", source="same",
                                    message=f"{which} the same photo as before, so it was not read again").model_dump())


def _save(job: dict) -> None:
    store.collection("jobs").put({k: v for k, v in job.items()})
