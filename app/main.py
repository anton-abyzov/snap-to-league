from __future__ import annotations

import os
import uuid
from pathlib import Path

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .env import load_env

load_env()

from . import easychamp, store  # noqa: E402
from .extract import ExtractError, extract
from .schema import Extraction, Match, Snap
from .standings import checks, compute

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
SAMPLES = {"board": ROOT / "tests" / "fixtures" / "board.jpg", "bracket": ROOT / "tests" / "fixtures" / "bracket.jpg"}
MAX_BYTES = 12 * 1024 * 1024

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


async def _run(path: Path, league_id: str | None) -> dict:
    try:
        ex, model_rows, backend, secs = await run_in_threadpool(extract, path)
    except ExtractError as e:
        raise HTTPException(502, f"Could not read the photo: {e}")
    table, flags = checks(ex, model_rows)
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
    return {"ok": True, "backend": os.environ.get("SNAP_BACKEND", "astra"),
            "publish": "live" if os.environ.get("EC_PUBLISH") == "1" and (os.environ.get("EC_TOKEN") or os.environ.get("EC_TOKEN_CMD")) else "dry-run",
            "voice": bool(os.environ.get("ELEVENLABS_API_KEY"))}


@app.post("/api/snap")
async def snap(image: UploadFile = File(...), leagueId: str | None = Form(None)):
    data = await image.read()
    if not data:
        raise HTTPException(400, "The photo is empty")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "The photo is over 12 MB; take it again at a lower resolution")
    suffix = Path(image.filename or "photo.jpg").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".heic"}:
        suffix = ".jpg"
    path = store.images_dir() / f"{uuid.uuid4().hex[:12]}{suffix}"
    path.write_bytes(data)
    return await _run(path, leagueId)


@app.post("/api/sample")
async def sample(leagueId: str | None = Form(None), kind: str = Form("board")):
    src = SAMPLES.get(kind)
    if src is None:
        raise HTTPException(400, f"No sample called {kind}")
    path = store.images_dir() / f"sample-{uuid.uuid4().hex[:8]}.jpg"
    path.write_bytes(src.read_bytes())
    return await _run(path, leagueId)


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


@app.post("/api/leagues")
def save_league(body: LeagueIn):
    lid = body.id or uuid.uuid4().hex[:10]
    prev = leagues.get(lid) or {}
    ex = Extraction(competition=body.name, sport=body.sport, teams=body.teams, matches=body.matches)
    table, flags = checks(ex, [])
    doc = {"id": lid, "name": body.name, "sport": body.sport, "teams": body.teams,
           "matches": [m.model_dump() for m in body.matches],
           "snapIds": list(dict.fromkeys(prev.get("snapIds", []) + body.snapIds)),
           "standings": [r.model_dump() for r in table], "flags": [f.model_dump() for f in flags],
           "published": prev.get("published")}
    leagues.put(doc)
    return doc


@app.get("/api/leagues/{league_id}")
def get_league(league_id: str):
    doc = leagues.get(league_id)
    if not doc:
        raise HTTPException(404, "No such league")
    return doc


@app.post("/api/leagues/{league_id}/publish")
def publish(league_id: str):
    doc = leagues.get(league_id)
    if not doc:
        raise HTTPException(404, "No such league")
    try:
        result = easychamp.publish(doc)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"EasyChamp did not answer: {e}")
    doc["published"] = {"mode": result["mode"], "status": result.get("status")}
    leagues.put(doc)
    return result


class SpeakIn(BaseModel):
    text: str


@app.post("/api/speak")
def speak(body: SpeakIn):
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        return Response(status_code=204)
    voice = os.environ.get("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
    r = httpx.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
                   headers={"xi-api-key": key, "accept": "audio/mpeg"},
                   json={"text": body.text[:1500], "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_turbo_v2_5")},
                   timeout=60)
    if r.status_code != 200:
        raise HTTPException(502, f"ElevenLabs {r.status_code}: {r.text[:200]}")
    return Response(r.content, media_type="audio/mpeg")
