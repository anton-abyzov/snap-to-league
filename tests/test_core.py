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


def test_same_name_reuses_league(tmp_path, monkeypatch):
    monkeypatch.setenv("SNAP_BACKEND", "fixture")
    monkeypatch.setenv("SNAP_DATA", str(tmp_path))
    import importlib
    from app import main, store
    importlib.reload(store)
    importlib.reload(main)
    c = TestClient(main.app)
    ms = [{"home": "A", "away": "B", "homeScore": 1, "awayScore": 0, "status": "played"}]
    a = c.post("/api/leagues", json={"name": "Night Cup", "matches": ms}).json()
    b = c.post("/api/leagues", json={"name": "night cup", "matches": ms}).json()
    assert a["id"] == b["id"]


def test_second_reader_disagreement():
    from app.extract import disagreements
    a = Extraction(matches=[Match(home="Lions", away="Sharks", homeScore=3, awayScore=1, status="played")])
    same = Extraction(matches=[Match(home="Sharks", away="Lions", homeScore=1, awayScore=3, status="played")])
    other = Extraction(matches=[Match(home="Lions", away="Sharks", homeScore=3, awayScore=4, status="played")])
    assert disagreements(a, same, "astra") == []
    assert disagreements(a, other, "astra") == ["astra read Lions v Sharks as 3-4; check the photo"]


def test_combine_two_sheets_merges_names_results_and_scorers():
    from app.merge import combine, review
    G = lambda p, side, c=1: {"player": p, "side": side, "count": c}
    one = [Match(home="Lions", away="Sharks", homeScore=3, awayScore=1, status="played", round="Week 3",
                 goals=[G("Diaz", "home", 2), G("Kim", "home"), G("Lee", "away")]),
           Match(home="Lions", away="Hawks", when="Sun 7pm", venue="Court 2")]
    two = [Match(home="Lions", away="Sharks", homeScore=3, awayScore=1, status="played", round="Week 4"),
           Match(home="Lions", away="Hawks", homeScore=0, awayScore=1, status="played", goals=[G("Ortega", "away")]),
           Match(home="SHARKS", away="Wolves", homeScore=4, awayScore=2, status="played")]
    c = combine([one, two])
    assert len(c["matches"]) == 3 and c["conflicts"] == []
    assert c["renamed"] == {"SHARKS": "Sharks"}
    # a one-letter typo is not merged silently; the organizer gets a card instead
    _, flags = checks(Extraction(matches=[Match(home="Sharks", away="Lions"), Match(home="Sharcs", away="Wolves")]), [])
    assert any("look like the same team" in f.message for f in flags)
    lh = next(m for m in c["matches"] if {m.home, m.away} == {"Lions", "Hawks"})
    assert (lh.homeScore, lh.awayScore, lh.venue) == (0, 1, "Court 2")
    ls = next(m for m in c["matches"] if {m.home, m.away} == {"Lions", "Sharks"})
    assert sum(g.count for g in ls.goals) == 4
    # a third photo disagreeing on a result is a conflict, not a silent overwrite
    bad = [Match(home="Lions", away="Sharks", homeScore=2, awayScore=1, status="played", round="Week 3")]
    assert combine([one, bad])["conflicts"][0]["second"] == "2-1"
    # review against a saved league reports what changed
    saved = [m.model_dump() for m in c["matches"]]
    r = review(saved, [Match(home="sharks", away="Wolves", homeScore=4, awayScore=3, status="played")])
    assert r["changes"] == [{"kind": "changed", "home": "Sharks", "away": "Wolves", "before": "4-2", "after": "4-3"}]
    assert r["renamed"] == {"sharks": "Sharks"}


def test_scorers_publish_as_roster_and_goal_events():
    lg = {"id": "g", "name": "x", "sport": "futsal", "teams": [], "matches": [
        {"home": "Lions", "away": "Sharks", "homeScore": 2, "awayScore": 0, "status": "played",
         "goals": [{"player": "Diaz", "side": "home", "count": 2}]}]}
    p = easychamp.build_payload(lg)
    champ = p["League"]["Champs"][0]
    lions = next(t for t in champ["Teams"] if t["Name"] == "Lions")
    assert [m["Player"]["FullName"] for m in lions["TeamMembers"]] == ["Diaz"]
    ev = champ["Stages"][0]["Groups"][0]["Fixtures"][0]["Events"]
    assert len(ev) == 2 and all(e["EventType"] == "scorer" and e["IsHomeEvent"] for e in ev)
    assert ev[0]["Player"]["Id"] == lions["TeamMembers"][0]["Player"]["Id"]


def _client(tmp_path, monkeypatch):
    monkeypatch.setenv("SNAP_BACKEND", "fixture")
    monkeypatch.setenv("SNAP_DATA", str(tmp_path))
    import importlib
    from app import jobs, main, safety, store
    importlib.reload(store)
    importlib.reload(jobs)
    importlib.reload(main)
    safety.reset()
    return TestClient(main.app), main


def _wait(c, job_id):
    import time
    for _ in range(100):
        job = c.get(f"/api/jobs/{job_id}").json()
        if job["status"] != "reading":
            return job
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_job_reads_several_photos_with_progress(tmp_path, monkeypatch):
    c, _ = _client(tmp_path, monkeypatch)
    files = [("images", ("a.jpg", (FIX / "board.jpg").read_bytes(), "image/jpeg")),
             ("images", ("b.jpg", (FIX / "board.jpg").read_bytes(), "image/jpeg"))]
    job = c.post("/api/jobs", files=files).json()
    assert len(job["photos"]) == 2
    job = _wait(c, job["id"])
    assert job["status"] == "done" and all(p["status"] == "done" for p in job["photos"])
    # the same board twice gives one set of matches, not two
    assert len(job["extraction"]["matches"]) == 7
    assert "owner" not in job


def test_job_update_reviews_against_saved_league(tmp_path, monkeypatch):
    c, _ = _client(tmp_path, monkeypatch)
    job = _wait(c, c.post("/api/jobs", data={"samples": "bracket"}).json()["id"])
    ms = job["extraction"]["matches"]
    final = next(m for m in ms if m["stage"] == "final")
    final.update(homeScore=None, awayScore=None, status="scheduled")
    lg = c.post("/api/leagues", json={"name": "Night", "matches": ms, "jobId": job["id"]}).json()
    upd = _wait(c, c.post("/api/jobs", data={"samples": "bracket", "leagueId": lg["id"]}).json()["id"])
    assert upd["review"]["changes"] == []  # nothing new on the same photo
    assert c.get("/api/stats").json()["photosRead"] == 2


def test_refuses_non_images_and_needs_pin_to_publish(tmp_path, monkeypatch):
    c, _ = _client(tmp_path, monkeypatch)
    bad = c.post("/api/jobs", files=[("images", ("x.jpg", b"not an image", "image/jpeg"))])
    assert bad.status_code == 415
    monkeypatch.setenv("SNAP_PUBLISH_PIN", "4821")
    monkeypatch.setenv("EC_PUBLISH", "1")
    monkeypatch.setenv("EC_TOKEN", "should-not-be-used")
    lg = c.post("/api/leagues", json={"name": "Pin Cup", "matches": [
        {"home": "A", "away": "B", "homeScore": 1, "awayScore": 0, "status": "played"}]}).json()
    r = c.post(f"/api/leagues/{lg['id']}/publish", headers={"x-publish-pin": "0000"}).json()
    assert r["mode"] == "dry-run" and r["reason"] == "pin"


def test_rate_limit(tmp_path, monkeypatch):
    c, _ = _client(tmp_path, monkeypatch)
    monkeypatch.setenv("SNAP_PHOTOS_PER_HOUR", "2")
    assert c.post("/api/jobs", data={"samples": "board,bracket"}).status_code == 200
    assert c.post("/api/jobs", data={"samples": "board"}).status_code == 429


def test_null_competition_and_table_only_reads():
    ex, _ = _parse('{"extracted": {"competition": null, "sport": null, "teams": [], "matches": [], '
                   '"table": [{"team": "Hawks", "P": 3, "W": 2, "D": 1, "L": 0, "Pts": 7}]}}')
    assert ex.competition == "Untitled cup" and ex.table[0].team == "Hawks"
    with pytest.raises(ExtractError):
        _parse('{"extracted": {"competition": "x", "matches": []}}')
    p = easychamp.build_payload({"id": "t", "name": "x", "sport": "soccer", "teams": [], "matches": [],
                                 "table": [{"team": "Hawks"}, {"team": "Lions"}]})
    group = p["League"]["Champs"][0]["Stages"][0]["Groups"][0]
    assert len(group["TeamIds"]) == 2 and group["Fixtures"] == []


def test_numbered_team_names_are_not_flagged():
    ex = Extraction(matches=[Match(home=f"Team Name{i}", away=f"Team Name{i + 4}") for i in range(1, 5)])
    _, flags = checks(ex, [])
    assert not any("look like the same team" in f.message for f in flags)


def test_numbered_names_never_merge():
    from app.merge import canonical_names, combine
    m = canonical_names(["Team Name1", "Team Name2", "Lions U12", "Lions U14", "Hawks", "hawks"])
    assert m["Team Name1"] != m["Team Name2"] and m["Lions U12"] != m["Lions U14"] and m["hawks"] == m["Hawks"]
    c = combine([[Match(home=f"Team Name{i}", away=f"Team Name{i + 4}", homeScore=1, awayScore=0, status="played",
                        stage="quarterfinal", round="Round 1") for i in range(1, 5)]])
    assert len(c["matches"]) == 4
