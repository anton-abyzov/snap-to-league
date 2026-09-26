import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import easychamp
from app.extract import ExtractError, _parse
from app.schema import Extraction, Match, Row
from app.standings import checks, compute

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def board():
    return _parse((FIX / "board_extract.json").read_text())


def test_parse_board(board):
    ex, rows = board
    assert ex.competition == "Sat 7v7 Cup - Group A"
    assert len(ex.matches) == 7
    assert [m.stage for m in ex.matches].count("final") == 1
    assert len(rows) == 4


def test_parse_refusal():
    with pytest.raises(ExtractError, match="declined"):
        _parse('{"error": "I can not do that"}')


def test_standings_match_hand_count(board):
    ex, _ = board
    table = compute(ex.matches, ex.teams)
    assert [(r.team, r.Pts, r.GD) for r in table] == [("Hawks", 7, 3), ("Lions", 6, 3), ("Sharks", 3, -2), ("Wolves", 1, -4)]
    hawks = table[0]
    assert (hawks.P, hawks.W, hawks.D, hawks.L, hawks.GF, hawks.GA) == (3, 2, 1, 0, 6, 3)


def test_tiebreak_goal_difference_then_goals():
    ms = [Match(home="A", away="B", homeScore=1, awayScore=0, status="played"),
          Match(home="C", away="D", homeScore=3, awayScore=2, status="played")]
    assert [r.team for r in compute(ms)] == ["C", "A", "D", "B"]


def test_checks_flag_final_and_model_table(board):
    ex, rows = board
    _, flags = checks(ex, rows)
    msgs = " | ".join(f.message for f in flags)
    # Astra already raised the final contradiction, so the check does not repeat it
    assert "table's top two" not in msgs and "Written final is Hawks v Sharks" in msgs
    _, flags = checks(ex.model_copy(update={"uncertain": []}), rows)
    msgs = " | ".join(f.message for f in flags)
    assert "The final is Hawks v Sharks, but the table's top two are Hawks and Lions" in msgs
    assert not any("Astra's table gives" in f.message for f in flags)
    wrong = [r.model_copy(update={"Pts": 9}) if r.team == "Hawks" else r for r in rows]
    _, flags = checks(ex, wrong)
    assert any("Astra's table gives Hawks 9 pts, the results give 7" in f.message for f in flags)


def test_checks_catch_twins_and_missing_scores():
    ex = Extraction(matches=[Match(home="Lions", away="Lion", homeScore=1, awayScore=None, status="played"),
                             Match(home="Hawks", away="Hawks", status="scheduled")])
    _, flags = checks(ex, [])
    msgs = [f.message for f in flags]
    assert any("look like the same team" in m for m in msgs)
    assert any("without a full score" in m for m in msgs)
    assert any("against itself" in m for m in msgs)


def test_payload_shape(board):
    ex, _ = board
    league = {"id": "abc", "name": ex.competition, "sport": "soccer", "teams": ex.teams,
              "matches": [m.model_dump() for m in ex.matches]}
    p = easychamp.build_payload(league)
    champ = p["League"]["Champs"][0]
    assert p["ImportSource"] == 99 and p["League"]["Id"] == "snap:abc:league"
    assert {s["Type"] for s in champ["Stages"]} == {"league", "playoff"}
    group = champ["Stages"][0]["Groups"][0]
    team_ids = {t["Id"] for t in champ["Teams"]}
    for f in group["Fixtures"]:
        assert f["HomeTeam"]["Id"] in team_ids and f["AwayTeam"]["Id"] in team_ids
        assert f["Status"] == 2 and f["HomeTeamScore"].isdigit()
    final = champ["Stages"][1]["Groups"][0]["Fixtures"][0]
    assert final["Status"] == 0 and "HomeTeamScore" not in final and final["Venue"]["Name"] == "Field 2"
    assert easychamp.publish(league)["mode"] == "dry-run"


def test_api_sample_then_update(tmp_path, monkeypatch):
    monkeypatch.setenv("SNAP_BACKEND", "fixture")
    monkeypatch.setenv("SNAP_DATA", str(tmp_path))
    import importlib
    from app import main, store
    importlib.reload(store)
    importlib.reload(main)
    c = TestClient(main.app)
    snap = c.post("/api/sample").json()
    assert snap["backend"] == "fixture" and len(snap["extraction"]["matches"]) == 7
    ms = snap["extraction"]["matches"]
    lg = c.post("/api/leagues", json={"name": "Sat 7v7 Cup", "matches": ms, "snapIds": [snap["id"]]}).json()
    assert lg["standings"][0]["team"] == "Hawks"
    pub = c.post(f"/api/leagues/{lg['id']}/publish").json()
    assert pub["mode"] == "dry-run"
    # a second photo with the final played merges into the same league
    final = next(m for m in ms if m["stage"] == "final")
    changed = [dict(final, homeScore=2, awayScore=1, status="played")]
    merged, changes = main.merge(lg["matches"], [Match.model_validate(m) for m in changed])
    assert len(merged) == 7 and changes == ["Hawks 2-1 Sharks"]
    assert c.get(f"/l/{lg['id']}").status_code == 200
    assert c.get("/api/leagues/nope").status_code == 404


def test_bracket_extract_and_payload():
    ex, _ = _parse((FIX / "bracket_extract.json").read_text())
    assert [m.stage for m in ex.matches].count("quarterfinal") == 4
    final = next(m for m in ex.matches if m.stage == "final")
    assert final.status == "scheduled" and final.winner is None
    assert all(m.winner for m in ex.matches if m.stage in {"quarterfinal", "semifinal"})
    assert compute(ex.matches, []) == []  # no group stage, no table
    _, flags = checks(ex, [])
    assert not [f for f in flags if f.level == "error"]
    p = easychamp.build_payload({"id": "b", "name": ex.competition, "sport": ex.sport, "teams": ex.teams,
                                 "matches": [m.model_dump() for m in ex.matches]})
    champ = p["League"]["Champs"][0]
    assert champ["SportKindName"] == easychamp.sport_kind(ex.sport)
    assert easychamp.sport_kind("Super Smash Bros. Ultimate") == "Smash"
    assert easychamp.sport_kind("esports") == "OtherEsports"
    assert easychamp.sport_kind("soccer") == "Soccer" and easychamp.sport_kind("Ice hockey") == "IceHockey"
    assert [s["Type"] for s in champ["Stages"]] == ["playoff"]
    keys = {f["Id"] for f in champ["Stages"][0]["Groups"][0]["Fixtures"]}
    assert len(keys) == 7


def test_winner_from_score_in_knockout():
    m = Match(home="A", away="B", homeScore=1, awayScore=2, stage="semi-final")
    assert m.stage == "semifinal" and m.winner == "B" and m.status == "played"


def test_bracket_rounds_named_and_ordered():
    ex, _ = _parse((FIX / "bracket_extract.json").read_text())
    rounds = easychamp.knockout_rounds([m for m in ex.matches if m.stage != "group"])
    assert [len(r) for r in rounds] == [4, 2, 1]
    # quarterfinals sit under the semifinal they fed: Kirbo and Marth4 first, Shellby and Ganonz after
    assert [m.winner for m in rounds[0]] == ["Kirbo", "Marth4", "Shellby", "Ganonz"]
    p = easychamp.build_payload({"id": "b", "name": "x", "sport": "smash", "teams": ex.teams,
                                 "matches": [m.model_dump() for m in ex.matches]})
    fx = p["League"]["Champs"][0]["Stages"][0]["Groups"][0]["Fixtures"]
    assert [f["MatchDayName"] for f in fx] == ["quarterfinal"] * 4 + ["semifinal"] * 2 + ["final"]
    assert [f["Order"] for f in fx] == list(range(9, 16))
