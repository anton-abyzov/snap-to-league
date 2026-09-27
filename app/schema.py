"""Data shapes shared by the extractor, the checks and the EasyChamp publisher."""
from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Goal(BaseModel):
    """A scorer written on a scoresheet ("Goals: Smith 2, Lee")."""
    player: str
    side: Literal["home", "away"]
    count: int = 1
    minute: Optional[str] = None

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


class Extraction(BaseModel):
    competition: str = "Untitled cup"
    sport: str = "soccer"
    table: list["Row"] = Field(default_factory=list)  # a standings table read as-is (screenshot of a league site)

    @field_validator("competition", "sport", mode="before")
    @classmethod
    def _text(cls, v, info):
        if v is None or not str(v).strip():
            return "Untitled cup" if info.field_name == "competition" else "other"
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
    source: Literal["astra", "check", "second", "merge", "match"]


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
