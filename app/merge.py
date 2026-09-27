"""Putting several photos, and later photos, together into one league.

Three jobs:
  1. names: the same team or player written differently ("Marth 4", "marth4") becomes one name,
     preferring the spelling of the existing league, then the most common spelling;
  2. merge: matches from every photo are combined by fixture (the two sides, stage and round);
  3. review: every difference from what was known is reported as added, updated, same or conflict,
     so the organizer sees exactly what a photo changed before anything is saved.
"""
from __future__ import annotations

import difflib
import re
from collections import Counter

from .schema import Match

SAME_NAME = 0.86


def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def similar(a: str, b: str) -> float:
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if re.sub(r"\d+", "#", na) == re.sub(r"\d+", "#", nb) or re.sub(r"\D", "", na) != re.sub(r"\D", "", nb):
        return 0.0  # "Team 1" and "Team 2", or "U12" and "U14", are different teams
    return difflib.SequenceMatcher(None, na, nb).ratio()


def canonical_names(spellings: list[str], known: list[str] = ()) -> dict[str, str]:
    """Map every spelling to one canonical name. Known names (already in the league) win."""
    counts = Counter(spellings)
    canon: list[str] = list(dict.fromkeys(known))
    mapping: dict[str, str] = {k: k for k in canon}
    for name, _ in counts.most_common():
        if name in mapping:
            continue
        best = max(canon, key=lambda c: similar(name, c), default=None)
        if best is not None and similar(name, best) >= SAME_NAME:
            mapping[name] = best
        else:
            canon.append(name)
            mapping[name] = name
    return mapping


def fixture_key(m: Match) -> tuple:
    """Group games are identified by the two sides; knockout games also by their round."""
    sides = tuple(sorted((norm(m.home), norm(m.away))))
    return sides, m.stage, norm(m.round or "") if m.stage != "group" else ""


def _rematch(a: Match, b: Match) -> bool:
    """Two played group games between the same sides in differently labelled rounds are a rematch."""
    return (a.stage == "group" and a.status == b.status == "played" and bool(a.round) and bool(b.round)
            and norm(a.round) != norm(b.round))


def _result(m: Match | dict) -> tuple:
    d = m if isinstance(m, dict) else m.model_dump()
    if d.get("status") != "played":
        return ("scheduled",)
    sides = {norm(d["home"]): d.get("homeScore"), norm(d["away"]): d.get("awayScore")}
    return ("played", tuple(sorted(sides.items())), norm(d.get("winner") or ""))


def rename(m: Match, teams: dict[str, str], players: dict[str, str]) -> Match:
    goals = [g.model_copy(update={"player": players.get(g.player, g.player)}) for g in m.goals]
    winner = teams.get(m.winner, m.winner) if m.winner else None
    return m.model_copy(update={"home": teams.get(m.home, m.home), "away": teams.get(m.away, m.away),
                                "winner": winner, "goals": goals})


def combine(photos: list[list[Match]], known_teams: list[str] = (), known_players: list[str] = ()) -> dict:
    """Merge the matches read from several photos of the same competition.

    Returns matches, the name mapping applied, and conflicts where two photos disagree on a result.
    """
    teams = canonical_names([t for ms in photos for m in ms for t in (m.home, m.away)], known_teams)
    players = canonical_names([g.player for ms in photos for m in ms for g in m.goals], known_players)
    merged: dict[tuple, Match] = {}
    seen_in: dict[tuple, int] = {}
    conflicts = []
    for i, ms in enumerate(photos):
        for raw in ms:
            m = rename(raw, teams, players)
            k = fixture_key(m)
            cur = merged.get(k)
            if cur is None:
                merged[k], seen_in[k] = m, i
                continue
            if _result(cur) == _result(m):
                if m.goals and not cur.goals:
                    merged[k] = cur.model_copy(update={"goals": m.goals})
                continue
            if cur.status != "played" and m.status == "played":
                merged[k], seen_in[k] = m.model_copy(update={"when": cur.when, "venue": cur.venue}), i
                continue
            if cur.status == "played" and m.status != "played":
                continue
            if _rematch(cur, m):
                merged[k + (norm(m.round),)], seen_in[k + (norm(m.round),)] = m, i
                continue
            conflicts.append({"home": cur.home, "away": cur.away, "photos": [seen_in[k] + 1, i + 1],
                              "first": _score(cur), "second": _score(m)})
    renamed = {k: v for k, v in {**teams, **players}.items() if k != v}
    return {"matches": list(merged.values()), "renamed": renamed, "conflicts": conflicts,
            "teams": sorted(set(teams.values()), key=str.casefold)}


def review(existing: list[dict], incoming: list[Match]) -> dict:
    """Compare a new read with the league as saved: what a photo adds or changes."""
    known_teams = list(dict.fromkeys(t for m in existing for t in (m["home"], m["away"])))
    known_players = list(dict.fromkeys(g["player"] for m in existing for g in m.get("goals", [])))
    teams = canonical_names([t for m in incoming for t in (m.home, m.away)], known_teams)
    players = canonical_names([g.player for m in incoming for g in m.goals], known_players)
    by_key = {fixture_key(Match.model_validate(m)): Match.model_validate(m) for m in existing}
    changes, out = [], dict(by_key)
    for raw in incoming:
        m = rename(raw, teams, players)
        k = fixture_key(m)
        cur = by_key.get(k)
        if cur is None:
            out[k] = m
            changes.append({"kind": "added", "home": m.home, "away": m.away, "after": _score(m)})
        elif _result(cur) == _result(m):
            if m.goals and not cur.goals:
                out[k] = cur.model_copy(update={"goals": m.goals})
                changes.append({"kind": "scorers", "home": m.home, "away": m.away, "after": _score(m)})
        elif cur.status != "played" and m.status == "played":
            out[k] = m.model_copy(update={"when": m.when or cur.when, "venue": m.venue or cur.venue})
            changes.append({"kind": "result", "home": m.home, "away": m.away, "before": "not played", "after": _score(m)})
        elif _rematch(cur, m):
            out[k + (norm(m.round),)] = m
            changes.append({"kind": "added", "home": m.home, "away": m.away, "after": _score(m)})
        elif m.status == "played":
            out[k] = m
            changes.append({"kind": "changed", "home": m.home, "away": m.away, "before": _score(cur), "after": _score(m)})
    renamed = {k: v for k, v in {**teams, **players}.items() if k != v}
    return {"matches": [v.model_dump() for v in out.values()], "changes": changes, "renamed": renamed}


def _score(m: Match) -> str:
    if m.status != "played":
        return "not played"
    if m.homeScore is not None and m.awayScore is not None:
        return f"{m.homeScore}-{m.awayScore}"
    return f"won by {m.winner}" if m.winner else "played"
