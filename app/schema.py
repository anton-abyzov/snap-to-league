"""Data shapes shared by the extractor, the checks and the EasyChamp publisher."""
from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator



UNKNOWN_SPORT = {"", "unknown", "unclear", "none", "null", "n/a", "na", "?", "-", "sport", "sports", "game", "games",
                 "tournament", "competition", "league", "cup", "mixed", "various"}


def sport_name(v) -> str:
    """The board's sport or game, lower case; "other" whenever the reader could not tell."""
    s = " ".join(str(v or "").split()).casefold().strip(" .")
    return "other" if s in UNKNOWN_SPORT else s[:40]

class Goal(BaseModel):
    """A scorer written on a scoresheet ("Goals: Smith 2, Lee")."""
    player: str
    side: Literal["home", "away"]
    count: int = 1
    minute: Optional[str] = None
    number: Optional[str] = None

    @field_validator("minute", "number", mode="before")
    @classmethod
    def _str(cls, v):
        return None if v in (None, "") else str(v).strip().lstrip("#")

    @field_validator("player")
    @classmethod
    def _strip(cls, v: str) -> str:
        return " ".join(v.split())

    @field_validator("count", mode="before")
    @classmethod
    def _count(cls, v):
        return max(1, int(v or 1))


class Match(BaseModel):
    home: str
    away: str
    homeScore: Optional[int] = None
    awayScore: Optional[int] = None
    status: Literal["played", "scheduled"] = "scheduled"
    when: Optional[str] = None
    venue: Optional[str] = None
    stage: Literal["group", "final", "semifinal", "quarterfinal", "knockout"] = "group"
    group: Optional[str] = None
    round: Optional[str] = None
    winner: Optional[str] = None
    goals: list[Goal] = Field(default_factory=list)

    @field_validator("home", "away")
    @classmethod
    def _strip(cls, v: str) -> str:
        return " ".join(v.split())

    @field_validator("stage", mode="before")
    @classmethod
    def _stage(cls, v):
        v = (v or "group").strip().casefold()
        if v in {"group", "final", "semifinal", "quarterfinal", "knockout"}:
            return v
        if "semi" in v:
            return "semifinal"
        if "quarter" in v:
            return "quarterfinal"
        if "final" in v:
            return "final"
        return "knockout" if v not in {"league", "round robin", "pool"} else "group"

    @model_validator(mode="after")
    def _winner(self):
        if self.winner is None and self.homeScore is not None and self.awayScore is not None and self.stage != "group":
            if self.homeScore != self.awayScore:
                self.winner = self.home if self.homeScore > self.awayScore else self.away
        if self.winner and self.status == "scheduled":
            self.status = "played"
        return self

    @field_validator("homeScore", "awayScore", mode="before")
    @classmethod
    def _score(cls, v):
        if v in (None, "", "-"):
            return None
        return int(str(v).strip())


class Row(BaseModel):
    team: str

    @field_validator("P", "W", "D", "L", "GF", "GA", "GD", "Pts", mode="before", check_fields=False)
    @classmethod
    def _int(cls, v):
        """Tables from other sites leave columns blank or add signs ("+3", "90%"); blanks count as 0."""
        if v is None or v == "":
            return 0
        if isinstance(v, (int, float)):
            return int(v)
        digits = re.sub(r"[^0-9-]", "", str(v))
        return int(digits) if digits not in ("", "-") else 0

    P: int = 0
    W: int = 0
    D: int = 0
    L: int = 0
    GF: int = 0
    GA: int = 0
    GD: int = 0
    Pts: int = 0


class Entry(BaseModel):
    """One entrant on a leaderboard: a team or player with a value per round and a total."""
    name: str
    values: list[Optional[str]] = Field(default_factory=list)
    total: Optional[str] = None
    place: Optional[int] = None
    note: Optional[str] = None

    @field_validator("values", mode="before")
    @classmethod
    def _vals(cls, v):
        return [None if x in (None, "") else str(x).strip() for x in (v or [])]

    @field_validator("total", "note", mode="before")
    @classmethod
    def _txt(cls, v):
        return None if v in (None, "") else str(v).strip()

    @field_validator("place", mode="before")
    @classmethod
    def _place(cls, v):
        digits = re.sub(r"\D", "", str(v or ""))
        return int(digits) if digits else None


class Leaderboard(BaseModel):
    """Races, heats, quizzes, cup stacking: entrants ranked by a number instead of playing games."""
    metric: str = "points"
    lower_is_better: bool = False
    rounds: list[str] = Field(default_factory=list)
    entries: list[Entry] = Field(default_factory=list)


class Extraction(BaseModel):
    competition: str = "Untitled cup"
    sport: str = "other"
    table: list["Row"] = Field(default_factory=list)  # a standings table read as-is (screenshot of a league site)
    leaderboard: Optional[Leaderboard] = None

    @field_validator("competition", "sport", mode="before")
    @classmethod
    def _text(cls, v, info):
        if info.field_name == "sport":
            return sport_name(v)
        if v is None or not str(v).strip():
            return "Untitled cup"
        return str(v).strip()

    @field_validator("teams", "rules_notes", "uncertain", mode="before")
    @classmethod
    def _list(cls, v):
        return [x for x in (v or []) if x]
    teams: list[str] = Field(default_factory=list)
    matches: list[Match] = Field(default_factory=list)
    rules_notes: list[str] = Field(default_factory=list)
    uncertain: list[str] = Field(default_factory=list)


class Flag(BaseModel):
    level: Literal["info", "warn", "error"]
    message: str
    source: Literal["astra", "check", "second", "merge", "match", "same"]


class Snap(BaseModel):
    id: str
    leagueId: Optional[str] = None
    image: str
    backend: str
    seconds: float
    extraction: Extraction
    modelStandings: list[Row] = Field(default_factory=list)
    standings: list[Row] = Field(default_factory=list)
    flags: list[Flag] = Field(default_factory=list)


Extraction.model_rebuild()
