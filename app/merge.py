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
import unicodedata
from collections import Counter

from .schema import Match

SAME_NAME = 0.86

# Words that do not tell two teams apart: "Hawks FC" is "Hawks", "Segfault Utd" is "Segfault United".
FILLER = {"fc", "sc", "cf", "afc", "ac", "cd", "club", "the", "team", "squad"}
SHORT = {"utd": "united", "st": "saint", "intl": "international", "univ": "university", "&": "and"}


def norm(name: str) -> str:
    """Lower case, accents dropped, letters and digits of any script kept ("Luís" == "Luis", "Заяц" kept)."""
    s = unicodedata.normalize("NFKD", name or "").casefold()
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[\W_]", "", s)


def _words(name: str) -> list[str]:
    s = unicodedata.normalize("NFKD", name or "").casefold()
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).replace("'", "")
    return [SHORT.get(w, w) for w in re.findall(r"\w+|&", s)]


def team_key(name: str) -> str:
    words = [w for w in _words(name) if w not in FILLER]
    return "".join(words) or norm(name)


def _edits(a: str, b: str, cap: int = 3) -> int:
    """Edit distance where swapping two neighbouring letters ("Kenij", "Pryia") counts as one slip."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    d = [[i + j if i * j == 0 else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[-1][-1]


def similar(a: str, b: str) -> float:
    """How likely two spellings name the same team or player, 0..1.

    Typos, a dropped apostrophe, accents, "FC" or "Utd" and word order do not matter; a different
    number always does ("Team 1" and "Team 2", "U12" and "U14" are never the same)."""
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if re.sub(r"\d+", "#", na) == re.sub(r"\d+", "#", nb) or re.sub(r"\D", "", na) != re.sub(r"\D", "", nb):
        return 0.0
    ka, kb = team_key(a), team_key(b)
    if ka == kb or sorted(_words(a)) == sorted(_words(b)):
        return 0.99
    ratio = max(difflib.SequenceMatcher(None, na, nb).ratio(), difflib.SequenceMatcher(None, ka, kb).ratio())
    # one slip in a short name ("Mya"/"Maya", "Jon"/"John") or two in a long one is still a typo
    n, d = min(len(ka), len(kb)), _edits(ka, kb)
    if ka[:1] == kb[:1] and ((n >= 3 and d <= 1) or (n >= 8 and d <= 2)):  # "Rays" and "Jays" stay apart
        ratio = max(ratio, 0.9)
    return ratio


def _abbreviates(short: str, full: str) -> bool:
    """"M. Rivera" or "Rivera" for "Maya Rivera": every word of the short form starts a word of the full one."""
    ws, wf = _words(short), _words(full)
    if not ws or len(ws) > len(wf) or ws == wf:
        return False
    return ws[-1] == wf[-1] and all(any(f.startswith(w) for f in wf) for w in ws)


def canonical_names(spellings: list[str], known: list[str] = (), apart: set = frozenset(),
                    people: bool = False) -> dict[str, str]:
    """Map every spelling to one canonical name. Known names (already in the league) win, then the
    most common spelling, then the fuller one. Two names in `apart` (they played each other) are never
    merged. For people, "Rivera" or "M. Rivera" joins "Maya Rivera" when that is the only match."""
    counts = Counter(spellings)
    first = {n: i for i, n in reversed(list(enumerate(spellings)))}
    canon: list[str] = list(dict.fromkeys(known))
    mapping: dict[str, str] = {k: k for k in canon}
    order = sorted(counts, key=lambda n: (-counts[n], first[n]))  # most games, then first written
    for name in order:
        if name in mapping:
            continue
        options = [c for c in canon if frozenset((norm(name), norm(c))) not in apart]
        best = max(options, key=lambda c: similar(name, c), default=None)
        if best is not None and similar(name, best) >= SAME_NAME:
            mapping[name] = best
            continue
        if people:
            fuller = [c for c in options if _abbreviates(name, c)]
            if len(fuller) == 1:
                mapping[name] = fuller[0]
                continue
        canon.append(name)
        mapping[name] = name
    if people:  # an initial read before the full name: point it at the only full name that fits
        for name in list(mapping):
            if mapping[name] == name and name not in known:
                fuller = [c for c in set(mapping.values()) if c != name and _abbreviates(name, c)]
                if len(fuller) == 1:
                    mapping[name] = fuller[0]
    return mapping


def apart_pairs(matches) -> set:
    """Pairs of teams that played each other: whatever their names look like, they are two teams."""
    out = set()
    for m in matches:
        h, a = (m.home, m.away) if hasattr(m, "home") else (m["home"], m["away"])
        out.add(frozenset((norm(h), norm(a))))
    return out


def player_names(games: list[Match], teams: dict[str, str], known: list[tuple[str, str]] = ()) -> dict[tuple[str, str], str]:
    """Canonical scorer names per team: (team, spelling) -> name. A player is matched only against
    team-mates, so "Luis" on one team never becomes "Louis" on another."""
    by_team: dict[str, list[str]] = {}
    for m in games:  # a brace is one sighting of the name, not two
        for g in dict.fromkeys((g.side, g.player) for g in m.goals):
            side = teams.get(m.home, m.home) if g[0] == "home" else teams.get(m.away, m.away)
            by_team.setdefault(norm(side), []).append(g[1])
    known_by_team: dict[str, list[str]] = {}
    for team, player in known:
        known_by_team.setdefault(norm(team), []).append(player)
    out = {}
    for team in set(by_team) | set(known_by_team):
        mapping = canonical_names(by_team.get(team, []), known_by_team.get(team, []), people=True)
        out.update({(team, k): v for k, v in mapping.items()})
    return out


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


def rename(m: Match, teams: dict[str, str], players: dict) -> Match:
    home, away = teams.get(m.home, m.home), teams.get(m.away, m.away)
    goals = [g.model_copy(update={"player": players.get((norm(home if g.side == "home" else away), g.player), g.player)})
             for g in m.goals]
    winner = teams.get(m.winner, m.winner) if m.winner else None
    return m.model_copy(update={"home": home, "away": away, "winner": winner, "goals": goals})


def _renamed(teams: dict[str, str], players: dict) -> dict[str, str]:
    out = {k: v for k, v in teams.items() if k != v}
    out.update({k: v for (_, k), v in players.items() if k != v})
    return out


def combine(photos: list[list[Match]], known_teams: list[str] = (), known_players: list[tuple[str, str]] = (),
            known_matches: list = ()) -> dict:
    """Merge the matches read from several photos of the same competition.

    Returns matches, the name mapping applied, and conflicts where two photos disagree on a result.
    """
    games = [m for ms in photos for m in ms]
    teams = canonical_names([t for m in games for t in (m.home, m.away)], known_teams,
                            apart=apart_pairs(games) | apart_pairs(known_matches))
    players = player_names(games, teams, known_players)
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
    return {"matches": list(merged.values()), "renamed": _renamed(teams, players), "conflicts": conflicts,
            "teams": sorted(set(teams.values()), key=str.casefold)}


def review(existing: list[dict], incoming: list[Match]) -> dict:
    """Compare a new read with the league as saved: what a photo adds or changes."""
    known_teams = list(dict.fromkeys(t for m in existing for t in (m["home"], m["away"])))
    known_players = known_scorers(existing)
    teams = canonical_names([t for m in incoming for t in (m.home, m.away)], known_teams,
                            apart=apart_pairs(incoming) | apart_pairs(existing))
    players = player_names(incoming, teams, known_players)
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
    return {"matches": [v.model_dump() for v in out.values()], "changes": changes, "renamed": _renamed(teams, players)}


def known_scorers(matches: list[dict]) -> list[tuple[str, str]]:
    """(team, player) for every scorer already saved in a league."""
    return list(dict.fromkeys((m["home"] if g.get("side") == "home" else m["away"], g["player"])
                              for m in matches for g in m.get("goals", [])))


def _score(m: Match) -> str:
    if m.status != "played":
        return "not played"
    if m.homeScore is not None and m.awayScore is not None:
        return f"{m.homeScore}-{m.awayScore}"
    return f"won by {m.winner}" if m.winner else "played"
