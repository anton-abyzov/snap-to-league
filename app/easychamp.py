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

KINDS = ["Soccer", "Basketball", "IceHockey", "Futsal", "Tennis", "Volleyball", "AmericanFootball", "Baseball",
         "Softball", "Wrestling", "Pickleball", "Padel", "Rugby", "FIFA", "eFootball", "NBA2K", "RocketLeague",
         "Dota2", "CounterStrike", "Valorant", "ApexLegends", "LeagueOfLegends", "MobileLegends", "RainbowSix",
         "Overwatch", "PUBGMobile", "Smash", "PUBG", "BrawlStars", "Hearthstone", "CallOfDuty", "Fortnite",
         "Tekken", "Other", "OtherEsports"]
ALIASES = {"hockey": "IceHockey", "football": "Soccer", "fc": "FIFA", "eafc": "FIFA", "ea fc": "FIFA",
           "super smash bros": "Smash", "smash bros": "Smash", "cs2": "CounterStrike", "lol": "LeagueOfLegends",
           "esports": "OtherEsports", "other": "Other"}


def sport_kind(sport: str | None) -> str:
    """EasyChamp SportKind name for the board's sport or game."""
    key = re.sub(r"[^a-z0-9 ]", "", (sport or "").casefold()).strip()
    for k in KINDS:
        if key.replace(" ", "") == k.casefold():
            return k
    for alias, k in ALIASES.items():
        if alias in key:
            return k
    return "Soccer" if not key else "Other"
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


STAGE_RANK = {"knockout": 0, "quarterfinal": 1, "semifinal": 2, "final": 3}
ROUND_NAMES = {1: "final", 2: "semifinal", 3: "quarterfinal", 4: "round_of_16", 5: "round_of_32", 6: "round_of_64"}


def knockout_rounds(matches: list[Match]) -> list[list[Match]]:
    """Knockout matches grouped by round, first round first, each round ordered by bracket position.

    Positions come from the winners: the two matches feeding a later match sit next to each other,
    so EasyChamp's sequential bracket fill draws the tree the way the board shows it.
    """
    rounds: dict[str, tuple[int, int, list[Match]]] = {}
    for i, m in enumerate(matches):
        # a named stage is one round even when the board numbers its games ("SEMI 1", "SEMI 2")
        label = m.stage if m.stage in ("quarterfinal", "semifinal", "final") else (m.round or m.stage)
        rank, first, ms = rounds.get(label, (STAGE_RANK.get(m.stage, 0), i, []))
        ms.append(m)
        rounds[label] = (rank, first, ms)
    ordered = [ms for _, _, ms in sorted(rounds.values(), key=lambda r: (r[0], r[1]))]
    for r in range(len(ordered) - 2, -1, -1):
        feeders, placed = ordered[r], []
        for parent in ordered[r + 1]:
            for side in (parent.home, parent.away):
                child = next((c for c in feeders if c.winner == side and c not in placed), None)
                if child:
                    placed.append(child)
        ordered[r] = placed + [c for c in feeders if c not in placed]
    return ordered


def build_payload(league: dict) -> dict:
    lid = league["id"]
    sport = sport_kind(league.get("sport"))
    matches = [Match.model_validate(m) for m in league["matches"]]
    names = list(dict.fromkeys(league.get("teams", []) + [t for m in matches for t in (m.home, m.away)]
                               + [r["team"] for r in league.get("table", [])]))
    team_id = {n: f"snap:{lid}:team:{slug(n)}" for n in names}

    def player(team: str, name: str) -> dict:
        return {"Id": f"snap:{lid}:player:{slug(team)}:{slug(name)}", "FullName": name, "SportKindName": sport}

    roster: dict[str, dict[str, dict]] = {n: {} for n in names}
    for m in matches:
        for g in m.goals:
            team = m.home if g.side == "home" else m.away
            member = {"Player": player(team, g.player)}
            if g.number and g.number.isdigit():
                member["JerseyNumber"] = int(g.number)
            roster.setdefault(team, {})[slug(g.player)] = member

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
            events, n = [], 0
            for g in m.goals:
                team = m.home if g.side == "home" else m.away
                for _ in range(g.count):
                    n += 1
                    events.append({"Id": f"snap:{lid}:evt:{fixture_key(m)}:{n}", "IsHomeEvent": g.side == "home",
                                   "Minute": (g.minute or "0").strip("'"), "EventType": "scorer", "Points": 1,
                                   "Player": player(team, g.player)})
            if events:
                f["Events"] = events
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
    if not matches and names:  # a standings photo: the teams arrive now, results as games are played
        groups = {}
        stages.append({"Id": f"snap:{lid}:stage:groups", "Name": "Group stage", "Type": "league", "Order": 1,
                       "RoundCount": 1, "TeamCount": len(names), "GroupCount": 1,
                       "Groups": [{"Id": f"snap:{lid}:group:a", "Name": "Group A", "TeamIds": [team_id[n] for n in names],
                                   "FixturesCount": 0, "Fixtures": []}]})
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
    third = [m for m in knockout if re.search(r"3rd|third", f"{m.round or ''} {m.stage}".casefold())]
    knockout = [m for m in knockout if m not in third]
    if knockout or third:
        rounds = knockout_rounds(knockout) if knockout else [[]]
        double = any(re.search(r"loser", (m.round or "").casefold()) for m in knockout)  # a losers bracket
        ko_fixtures, base, seq = [], 2 * len(rounds[0]), 0
        for ri, rms in enumerate(rounds):
            depth = len(rounds) - ri
            for m in rms:
                seq += 1
                f = fixture(m, base + seq)
                f["MatchDay"] = ri + 1
                f["RoundNumber"] = ri + 1
                f["MatchDayName"] = m.round if double else ROUND_NAMES.get(depth, m.round or "knockout")
                ko_fixtures.append(f)
        for m in third:  # EasyChamp draws the 3rd-place game beside the final, outside the tree
            seq += 1
            f = fixture(m, base + seq)
            f["MatchDay"] = f["RoundNumber"] = len(rounds)
            f["MatchDayName"] = "3rd_place_playoff"
            ko_fixtures.append(f)
        stages.append({
            "Id": f"snap:{lid}:stage:knockout", "Name": "Knockout", "Type": "playoff", "Order": 2,
            "RoundCount": 1, "TeamCount": len({t for m in knockout + third for t in (m.home, m.away)}), "GroupCount": 1,
            "Groups": [{
                "Id": f"snap:{lid}:group:knockout", "Name": "Knockout",
                "TeamIds": list(dict.fromkeys(team_id[t] for m in knockout + third for t in (m.home, m.away))),
                "FixturesCount": len(ko_fixtures),
                "Fixtures": ko_fixtures,
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
                "Teams": [{"Id": team_id[n], "Name": n, "SportKindName": sport,
                           "TeamMembers": list(roster.get(n, {}).values())} for n in names],
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
            has_table = any(m.get("stage", "group") == "group" for m in league.get("matches", []))
            tab = "standings" if has_table else "knockout"
            # the league site caches pages; a fresh query string shows the new result immediately
            links["competition"] = (champ.get("fullUrl", "").replace("tabs=teams", f"tabs={tab}") + f"&v={int(datetime.now().timestamp())}") if champ.get("fullUrl") else None
            if cid:
                links["watch"] = f"https://watch.easychamp.com/competition/{cid}"
        return links
    except (httpx.HTTPError, ValueError, KeyError, IndexError):
        return {}
