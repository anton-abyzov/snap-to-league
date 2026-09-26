"""Map a reviewed league to EasyChamp's ImportLeague payload and send it to POST /import/league.

External ids are namespaced `snap:<leagueId>:...` so a second photo of the same board converges
on the same teams and fixtures instead of creating twins.

Publishing is a dry run unless EC_PUBLISH=1 and EC_TOKEN are set; the dry run still returns
the exact payload so the review screen can show it.
"""
from __future__ import annotations

import os
import re
from datetime import date

import httpx

from .schema import Match

SPORTS = {"soccer": "Soccer", "futsal": "Futsal", "basketball": "Basketball",
          "volleyball": "Volleyball", "padel": "Padel"}
API = os.environ.get("EC_API_URL", "https://easychamp.com/ec-standings-api")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.casefold()).strip("-") or "x"


def fixture_key(m: Match) -> str:
    return f"{slug(m.home)}-v-{slug(m.away)}-{m.stage}"


def build_payload(league: dict) -> dict:
    lid = league["id"]
    sport = SPORTS.get(league.get("sport", "soccer"), "Soccer")
    matches = [Match.model_validate(m) for m in league["matches"]]
    names = list(dict.fromkeys(league.get("teams", []) + [t for m in matches for t in (m.home, m.away)]))
    team_id = {n: f"snap:{lid}:team:{slug(n)}" for n in names}

    def fixture(m: Match, order: int) -> dict:
        played = m.status == "played" and m.homeScore is not None and m.awayScore is not None
        f = {
            "Id": f"snap:{lid}:fix:{fixture_key(m)}",
            "Status": 2 if played else 0,
            "Order": order,
            "Location": m.venue,
            "MatchDayName": m.when,
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

    today = date.today().isoformat()
    return {
        "ImportSource": 99,
        "ImportMode": 1,
        "League": {
            "Id": f"snap:{lid}:league", "Name": league["name"], "SportKindName": sport, "ChampsCount": 1,
            "Champs": [{
                "Id": f"snap:{lid}:champ", "Name": league["name"], "LeagueName": league["name"],
                "SportKindName": sport, "StartDate": today, "EndDate": today,
                "FixturesCount": len(matches),
                "Teams": [{"Id": team_id[n], "Name": n, "SportKindName": sport} for n in names],
                "Stages": stages,
            }],
        },
    }


def publish(league: dict) -> dict:
    payload = build_payload(league)
    token = os.environ.get("EC_TOKEN")
    if os.environ.get("EC_PUBLISH") != "1" or not token:
        return {"mode": "dry-run", "payload": payload}
    owner = os.environ.get("EC_OWNER_ID")
    r = httpx.post(f"{API}/import/league", params={"ownerId": owner} if owner else None, json=payload,
                   headers={"Authorization": f"Bearer {token}", "User-Agent": "snap-to-league/0.1"}, timeout=300)
    return {"mode": "live", "status": r.status_code, "result": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:500], "payload": payload}
