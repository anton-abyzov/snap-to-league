"""Data shapes shared by the extractor, the checks and the EasyChamp publisher."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("home", "away")
    @classmethod
    def _strip(cls, v: str) -> str:
        return " ".join(v.split())

    @field_validator("homeScore", "awayScore", mode="before")
    @classmethod
    def _score(cls, v):
        if v in (None, "", "-"):
            return None
        return int(str(v).strip())


class Row(BaseModel):
    team: str
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
    teams: list[str] = Field(default_factory=list)
    matches: list[Match] = Field(default_factory=list)
    rules_notes: list[str] = Field(default_factory=list)
    uncertain: list[str] = Field(default_factory=list)


class Flag(BaseModel):
    level: Literal["info", "warn", "error"]
    message: str
    source: Literal["astra", "check"]


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
