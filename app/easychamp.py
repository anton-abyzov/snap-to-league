"""Map a reviewed league to EasyChamp's ImportLeague payload and send it to POST /import/league.

External ids are namespaced `snap:<leagueId>:...` so a second photo of the same board converges
on the same teams and fixtures instead of creating twins.

Publishing is a dry run unless EC_PUBLISH=1 and EC_TOKEN are set; the dry run still returns
the exact payload so the review screen can show it.
"""
from __future__ import annotations

import os
import re
import shlex
import subprocess
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx

from .schema import Match

SPORTS = {"soccer": "Soccer", "futsal": "Futsal", "basketball": "Basketball",
          "volleyball": "Volleyball", "padel": "Padel", "esports": "Esports"}
API = os.environ.get("EC_API_URL", "https://easychamp.com/ec-standings-api")


TZ = ZoneInfo(os.environ.get("SNAP_TZ", "America/New_York"))
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def kickoff(when: str | None, fallback: datetime) -> datetime:
    """Best-effort reading of board times like "Sun 10am", "1:30am", "7pm"; otherwise the fallback."""
    if not when:
        return fallback
    t = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", when.casefold())
    if not t:
        return fallback
    hour, minute = int(t.group(1)) % 24, int(t.group(2) or 0)
    if t.group(3) == "pm" and hour < 12:
        hour += 12
    if t.group(3) == "am" and hour == 12:
        hour = 0
    now = datetime.now(TZ)
    day = now
    for i, d in enumerate(DAYS):
        if d in when.casefold():
            day = now + timedelta(days=(i - now.weekday()) % 7)
            break
    at = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if at < now - timedelta(hours=6):
        at += timedelta(days=1)
    return at


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.casefold()).strip("-") or "x"


def fixture_key(m: Match) -> str:
    return f"{slug(m.home)}-v-{slug(m.away)}-{m.stage}" + (f"-{slug(m.round)}" if m.round else "")


def build_payload(league: dict) -> dict:
    lid = league["id"]
    sport = SPORTS.get(league.get("sport", "soccer"), "Soccer")
    matches = [Match.model_validate(m) for m in league["matches"]]
    names = list(dict.fromkeys(league.get("teams", []) + [t for m in matches for t in (m.home, m.away)]))
    team_id = {n: f"snap:{lid}:team:{slug(n)}" for n in names}

    start = datetime.now(TZ).replace(second=0, microsecond=0) - timedelta(hours=3)

    def fixture(m: Match, order: int) -> dict:
        played = m.status == "played" and m.homeScore is not None and m.awayScore is not None
        at = kickoff(m.when, start + timedelta(minutes=15 * order) if m.status == "played" else datetime.now(TZ) + timedelta(hours=1))
        f = {
            "Id": f"snap:{lid}:fix:{fixture_key(m)}",
            "Date": at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Status": 2 if played else 0,
            "Order": order,
            "Location": m.venue,
            "MatchDayName": m.round or m.when,
            "HomeTeam": {"Id": team_id[m.home], "Name": m.home, "SportKindName": sport},
            "AwayTeam": {"Id": team_id[m.away], "Name": m.away, "SportKindName": sport},
        }
        if played:
            f["HomeTeamScore"], f["AwayTeamScore"] = str(m.homeScore), str(m.awayScore)
        if m.venue:
            f["Venue"] = {"Id": f"snap:{lid}:venue:{slug(m.venue)}", "Name": m.venue}
        return f

    groups: dict[str, list[Match]] = {}
    knockout: list[Match] = []
    for m in matches:
        if m.stage == "group":
            groups.setdefault(m.group or "A", []).append(m)
        else:
            knockout.append(m)

    stages = []
    if groups:
        stages.append({
            "Id": f"snap:{lid}:stage:groups", "Name": "Group stage", "Type": "league", "Order": 1,
            "RoundCount": 1, "TeamCount": len({t for ms in groups.values() for m in ms for t in (m.home, m.away)}),
            "GroupCount": len(groups),
            "Groups": [{
                "Id": f"snap:{lid}:group:{slug(g)}", "Name": f"Group {g}",
                "TeamIds": list(dict.fromkeys(team_id[t] for m in ms for t in (m.home, m.away))),
                "FixturesCount": len(ms),
                "Fixtures": [fixture(m, i + 1) for i, m in enumerate(ms)],
            } for g, ms in groups.items()],
        })
    if knockout:
        stages.append({
            "Id": f"snap:{lid}:stage:knockout", "Name": "Knockout", "Type": "playoff", "Order": 2,
            "RoundCount": 1, "TeamCount": len({t for m in knockout for t in (m.home, m.away)}), "GroupCount": 1,
            "Groups": [{
                "Id": f"snap:{lid}:group:knockout", "Name": "Knockout",
                "TeamIds": list(dict.fromkeys(team_id[t] for m in knockout for t in (m.home, m.away))),
                "FixturesCount": len(knockout),
                "Fixtures": [fixture(m, i + 1) for i, m in enumerate(knockout)],
            }],
        })

    today = datetime.now(TZ).date()
    return {
        "ImportSource": 99,
        "ImportMode": 1,
        "League": {
            "Id": f"snap:{lid}:league", "Name": league["name"], "SportKindName": sport, "ChampsCount": 1,
            "Champs": [{
                "Id": f"snap:{lid}:champ", "Name": league["name"], "LeagueName": league["name"],
                "SportKindName": sport, "StartDate": (today - timedelta(days=1)).isoformat(), "EndDate": (today + timedelta(days=7)).isoformat(),
                "FixturesCount": len(matches),
                "Teams": [{"Id": team_id[n], "Name": n, "SportKindName": sport} for n in names],
                "Stages": stages,
            }],
        },
    }


def token() -> str | None:
    """EC_TOKEN, or the output of EC_TOKEN_CMD (a command that prints a fresh bearer token)."""
    if os.environ.get("EC_TOKEN"):
        return os.environ["EC_TOKEN"]
    cmd = os.environ.get("EC_TOKEN_CMD")
    if not cmd:
        return None
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=60)
    return proc.stdout.strip() or None if proc.returncode == 0 else None


def publish(league: dict) -> dict:
    payload = build_payload(league)
    token_ = token() if os.environ.get("EC_PUBLISH") == "1" else None
    if not token_:
        return {"mode": "dry-run", "payload": payload}
    owner = os.environ.get("EC_OWNER_ID")
    headers = {"Authorization": f"Bearer {token_}", "User-Agent": "snap-to-league/0.1"}
    r = httpx.post(f"{API}/import/league", params={"ownerId": owner} if owner else None, json=payload,
                   headers=headers, timeout=300)
    result = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:500]
    out = {"mode": "live", "status": r.status_code, "result": result, "payload": payload}
    if r.status_code == 200:
        out["links"] = find_links(league, headers)
    return out


def find_links(league: dict, headers: dict) -> dict:
    """Where the imported league lives: the league website and the competition page."""
    try:
        lg = httpx.get(f"{API}/champ-leagues/search", params={"name": league["name"]}, headers=headers, timeout=30).json()
        if not lg or not lg.get("id"):
            return {}
        champs = httpx.get(f"{API}/champ-leagues/{lg['id']}/champs", headers=headers, timeout=30).json().get("items", [])
        champ = next((c for c in champs if str(c.get("externalId", "")).endswith(f"snap:{league['id']}:champ")), champs[0] if champs else None)
        links = {"leagueSite": lg.get("leagueWebsiteUrl")}
        if champ:
            cid = champ["fullUrl"].split("/champ/")[1].split("?")[0] if champ.get("fullUrl") else None
            links["competition"] = champ.get("fullUrl", "").replace("tabs=teams", "tabs=standings") or None
            if cid:
                links["watch"] = f"https://watch.easychamp.com/competition/{cid}"
        return links
    except (httpx.HTTPError, ValueError, KeyError, IndexError):
        return {}
