"""Standings and the consistency checks that run on every extraction.

The model also returns a standings table. We never trust it: the table is recomputed here
from the played group matches and any difference becomes a flag on the review screen.
"""
from __future__ import annotations

import difflib
from collections import Counter

from .schema import Extraction, Flag, Match, Row

WIN, DRAW = 3, 1


def compute(matches: list[Match], teams: list[str] | None = None) -> list[Row]:
    rows: dict[str, Row] = {t: Row(team=t) for t in (teams or [])}
    for m in matches:
        if m.stage != "group":
            continue
        for t in (m.home, m.away):
            rows.setdefault(t, Row(team=t))
        if m.status != "played" or m.homeScore is None or m.awayScore is None:
            continue
        h, a = rows[m.home], rows[m.away]
        for row, gf, ga in ((h, m.homeScore, m.awayScore), (a, m.awayScore, m.homeScore)):
            row.P += 1
            row.GF += gf
            row.GA += ga
            if gf > ga:
                row.W += 1
                row.Pts += WIN
            elif gf == ga:
                row.D += 1
                row.Pts += DRAW
            else:
                row.L += 1
    for r in rows.values():
        r.GD = r.GF - r.GA
    return sorted(rows.values(), key=lambda r: (-r.Pts, -r.GD, -r.GF, r.team.casefold()))


def checks(ex: Extraction, model_rows: list[Row]) -> tuple[list[Row], list[Flag]]:
    flags: list[Flag] = [Flag(level="warn", message=u, source="astra") for u in ex.uncertain]
    table = compute(ex.matches, ex.teams)

    names = sorted({t for m in ex.matches for t in (m.home, m.away)} | set(ex.teams))
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if a.casefold() == b.casefold() or difflib.SequenceMatcher(None, a.casefold(), b.casefold()).ratio() >= 0.85:
                flags.append(Flag(level="warn", message=f'"{a}" and "{b}" look like the same team', source="check"))

    pairs = Counter(frozenset((m.home, m.away)) for m in ex.matches if m.stage == "group" and m.status == "played")
    for pair, n in pairs.items():
        if n > 1:
            flags.append(Flag(level="warn", message=f"{' v '.join(sorted(pair))} is recorded {n} times", source="check"))

    for m in ex.matches:
        if m.home == m.away:
            flags.append(Flag(level="error", message=f"{m.home} is listed against itself", source="check"))
        if m.status == "played" and (m.homeScore is None or m.awayScore is None):
            flags.append(Flag(level="error", message=f"{m.home} v {m.away} is marked played without a full score", source="check"))

    if model_rows:
        mine = {r.team.casefold(): r for r in table}
        for r in model_rows:
            ours = mine.get(r.team.casefold())
            if ours is None:
                flags.append(Flag(level="warn", message=f"Astra's table lists {r.team}, who has no group match", source="check"))
            elif (ours.Pts, ours.GD, ours.P) != (r.Pts, r.GD, r.P):
                flags.append(Flag(level="warn", message=f"Astra's table gives {r.team} {r.Pts} pts, the results give {ours.Pts}", source="check"))

    finals = [m for m in ex.matches if m.stage == "final"]
    played_group = [m for m in ex.matches if m.stage == "group" and m.status == "played"]
    astra_saw_final = any("final" in u.casefold() for u in ex.uncertain)
    if finals and played_group and len(table) >= 2 and not astra_saw_final:
        top2 = {table[0].team, table[1].team}
        for f in finals:
            if {f.home, f.away} != top2 and not ({f.home, f.away} - set(names)):
                flags.append(Flag(level="info", message=f"The final is {f.home} v {f.away}, but the table's top two are {table[0].team} and {table[1].team}", source="check"))
    return table, flags
