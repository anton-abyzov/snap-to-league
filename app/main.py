from __future__ import annotations

import os
import uuid
from pathlib import Path

import httpx
from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .env import load_env

load_env()

from . import easychamp, jobs, safety, store  # noqa: E402
from .merge import fixture_key as merge_key, review as merge_review  # noqa: E402
from .extract import ExtractError, extract
from .schema import Extraction, Flag, Match, Snap
from .standings import checks, compute

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
SAMPLES = {k: ROOT / "tests" / "fixtures" / f"{k}.jpg" for k in ("board", "bracket", "sheet1", "sheet2")}

app = FastAPI(title="Snap to League")


@app.middleware("http")
async def no_stale_assets(request, call_next):
    resp = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith(("/static", "/l/")):
        resp.headers["Cache-Control"] = "no-cache"
    return resp


app.mount("/static", StaticFiles(directory=STATIC), name="static")
snaps, leagues = store.collection("snaps"), store.collection("leagues")


def merge(old: list[dict], new: list[Match]) -> tuple[list[dict], list[str]]:
    """A later photo updates results by fixture key and appends matches it adds."""
    by_key = {easychamp.fixture_key(Match.model_validate(m)): m for m in old}
    changes = []
    for m in new:
        k = easychamp.fixture_key(m)
        cur = by_key.get(k)
        if cur is None:
            by_key[k] = m.model_dump()
            changes.append(f"Added {m.home} v {m.away}")
        elif (cur.get("homeScore"), cur.get("awayScore"), cur.get("status")) != (m.homeScore, m.awayScore, m.status):
            by_key[k] = {**cur, **{f: v for f, v in m.model_dump().items() if v is not None}}
            if m.status == "played":
                changes.append(f"{m.home} {m.homeScore}-{m.awayScore} {m.away}")
    return list(by_key.values()), changes


async def _run(path: Path, league_id: str | None, reader: str | None = None) -> dict:
    try:
        ex, model_rows, backend, secs, notes = await run_in_threadpool(extract, path, reader)
    except ExtractError as e:
        raise HTTPException(502, f"Could not read the photo: {e}")
    table, flags = checks(ex, model_rows)
    flags += [Flag(level="warn", message=n, source="second") for n in notes]
    snap = Snap(id=uuid.uuid4().hex[:12], leagueId=league_id, image=path.name, backend=backend, seconds=secs,
                extraction=ex, modelStandings=model_rows, standings=table, flags=flags)
    doc = snap.model_dump()
    if league_id and (lg := leagues.get(league_id)):
        merged, changes = merge(lg["matches"], ex.matches)
        doc["merged"] = {"matches": merged, "changes": changes, "standings": [r.model_dump() for r in compute([Match.model_validate(m) for m in merged], lg.get("teams"))]}
    snaps.put(doc)
    return doc


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/l/{league_id}")
def league_page(league_id: str):
    return FileResponse(STATIC / "league.html")


@app.get("/api/health")
def health():
    from .extract import PRIMARY, READERS, SECOND
    dual = not os.environ.get("SNAP_BACKEND") and os.environ.get("OPENROUTER_API_KEY")
    readers = f"{PRIMARY.split('/')[-1]} + {SECOND.split('/')[-1]}" if dual else os.environ.get("SNAP_BACKEND", "GPT-6 Astra")
    return {"ok": True, "backend": os.environ.get("SNAP_BACKEND", "openrouter" if dual else "astra"), "readers": readers,
            "choices": [{"id": k, **v} for k, v in READERS.items()] if dual else [], "primary": PRIMARY,
            "second": SECOND.split("/")[-1] if dual else None,
            "publish": "live" if os.environ.get("EC_PUBLISH") == "1" and (os.environ.get("EC_TOKEN") or os.environ.get("EC_TOKEN_CMD")) else "dry-run",
            "pin": bool(os.environ.get("SNAP_PUBLISH_PIN")), "maxPhotos": safety.MAX_PHOTOS,
            "gemini": "google" if os.environ.get("GEMINI_API_KEY") else ("openrouter" if dual else None),
            "voice": bool(os.environ.get("ELEVENLABS_API_KEY"))}


@app.get("/api/stats")
def stats():
    """Totals for the stats page: photos, matches, time, corrections, readers."""
    from .stats import totals
    return totals()


@app.get("/stats")
def stats_page():
    return FileResponse(STATIC / "stats.html")


@app.post("/api/snap")
async def snap(request: Request, image: UploadFile = File(...), leagueId: str | None = Form(None),
               reader: str | None = Form(None)):
    """One photo, answered in the same request (kept for scripts; the app uses /api/jobs)."""
    data = await image.read()
    suffix = safety.check_image(data)
    safety.spend(request, 1)
    path = store.images_dir() / f"{uuid.uuid4().hex[:12]}{suffix}"
    path.write_bytes(data)
    return await _run(path, leagueId, reader)


@app.post("/api/sample")
async def sample(request: Request, leagueId: str | None = Form(None), kind: str = Form("board"),
                 reader: str | None = Form(None)):
    src = SAMPLES.get(kind)
    if src is None:
        raise HTTPException(400, f"No sample called {kind}")
    safety.spend(request, 1)
    path = store.images_dir() / f"sample-{uuid.uuid4().hex[:8]}.jpg"
    path.write_bytes(src.read_bytes())
    return await _run(path, leagueId, reader)


@app.post("/api/jobs")
async def create_job(request: Request, images: list[UploadFile] = File(default=[]), samples: str = Form(""),
                     leagueId: str | None = Form(None), reader: str | None = Form(None)):
    """Start reading one or more photos. Poll GET /api/jobs/{id} for progress."""
    kinds = [k for k in samples.split(",") if k]
    if not images and not kinds:
        raise HTTPException(400, "Add at least one photo")
    if len(images) + len(kinds) > safety.MAX_PHOTOS:
        raise HTTPException(413, f"Up to {safety.MAX_PHOTOS} photos per import")
    paths = []
    for up in images:
        data = await up.read()
        suffix = safety.check_image(data)
        paths.append((data, suffix))
    for k in kinds:
        if k not in SAMPLES:
            raise HTTPException(400, f"No sample called {k}")
    league = leagues.get(leagueId) if leagueId else None
    if leagueId and not league:
        raise HTTPException(404, "No such league")
    safety.spend(request, len(paths) + len(kinds))
    files = []
    for data, suffix in paths:
        p = store.images_dir() / f"{uuid.uuid4().hex[:12]}{suffix}"
        p.write_bytes(data)
        files.append(p)
    for k in kinds:
        p = store.images_dir() / f"sample-{k}-{uuid.uuid4().hex[:6]}.jpg"
        p.write_bytes(SAMPLES[k].read_bytes())
        files.append(p)
    return jobs.create(files, league, reader, safety.visitor(request))


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "No such import")
    return {k: v for k, v in job.items() if k != "owner"}


@app.get("/api/images/{name}")
def image(name: str):
    path = store.images_dir() / Path(name).name
    if not path.exists():
        raise HTTPException(404, "No such photo")
    return FileResponse(path)


class LeagueIn(BaseModel):
    id: str | None = None
    name: str
    sport: str = "soccer"
    teams: list[str] = []
    matches: list[Match]
    snapIds: list[str] = []
    jobId: str | None = None
    table: list[dict] = []


def corrections(job: dict | None, final: list[Match]) -> int:
    """How many results the organizer changed from what the readers produced."""
    if not job or not job.get("extraction"):
        return 0
    read = {merge_key(m): (m.homeScore, m.awayScore, m.winner)
            for m in (Match.model_validate(x) for x in job["extraction"]["matches"])}
    fixed = sum(1 for m in final if read.get(merge_key(m), "new") != (m.homeScore, m.awayScore, m.winner))
    return fixed + max(0, len(read) - len(final))


@app.post("/api/leagues")
def save_league(body: LeagueIn, request: Request):
    safety.limit(request, "save", int(os.environ.get("SNAP_SAVES_PER_HOUR", "120")))
    # same competition name means the same league, so a fresh session never publishes a twin
    same = None if body.id else leagues.find_by_name(body.name)
    lid = body.id or (same or {}).get("id") or uuid.uuid4().hex[:10]
    prev = leagues.get(lid) or {}
    ex = Extraction(competition=body.name, sport=body.sport, teams=body.teams, matches=body.matches)
    table, flags = checks(ex, [])
    job = jobs.get(body.jobId) if body.jobId else None
    doc = {"id": lid, "name": body.name, "sport": body.sport, "teams": body.teams, "table": body.table,
           "matches": [m.model_dump() for m in body.matches],
           "snapIds": list(dict.fromkeys(prev.get("snapIds", []) + body.snapIds)),
           "jobIds": list(dict.fromkeys(prev.get("jobIds", []) + ([body.jobId] if body.jobId else []))),
           "corrections": prev.get("corrections", 0) + corrections(job, body.matches),
           "standings": [r.model_dump() for r in table], "flags": [f.model_dump() for f in flags],
           "published": prev.get("published"), "updated": __import__("time").time()}
    leagues.put(doc)
    return doc


@app.get("/api/leagues/{league_id}")
def get_league(league_id: str):
    doc = leagues.get(league_id)
    if not doc:
        raise HTTPException(404, "No such league")
    return doc


@app.post("/api/leagues/{league_id}/publish")
def publish(league_id: str, request: Request, x_publish_pin: str | None = Header(None)):
    safety.limit(request, "publish", 30)
    doc = leagues.get(league_id)
    if not doc:
        raise HTTPException(404, "No such league")
    if not safety.publish_allowed(x_publish_pin):
        return {"mode": "dry-run", "reason": "pin", "payload": easychamp.build_payload(doc)}
    try:
        result = easychamp.publish(doc)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"EasyChamp did not answer: {e}")
    doc["published"] = {"mode": result["mode"], "status": result.get("status"), "links": result.get("links")}
    leagues.put(doc)
    return result


class SpeakIn(BaseModel):
    text: str


@app.post("/api/speak")
def speak(body: SpeakIn, request: Request):
    safety.limit(request, "speak", int(os.environ.get("SNAP_SPEAKS_PER_HOUR", "40")))
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        return Response(status_code=204)
    voice = os.environ.get("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
    r = httpx.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
                   headers={"xi-api-key": key, "accept": "audio/mpeg"},
                   json={"text": body.text[:700], "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_turbo_v2_5")},
                   timeout=60)
    if r.status_code != 200:
        raise HTTPException(502, f"ElevenLabs {r.status_code}: {r.text[:200]}")
    return Response(r.content, media_type="audio/mpeg")
