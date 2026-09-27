# JSON format and validation

## What a reader returns

Every reader answers the same prompt (`app/prompt.txt`) with one JSON object:

```json
{"extracted": {
  "competition": "Sunday Futsal League - Week 3",
  "sport": "futsal",
  "teams": ["Lions", "Sharks", "Hawks", "Wolves"],
  "matches": [
    {"home": "Lions", "away": "Sharks", "homeScore": 3, "awayScore": 1, "status": "played",
     "when": null, "venue": null, "stage": "group", "group": null, "round": null, "winner": null,
     "goals": [{"player": "Diaz", "side": "home", "count": 2, "minute": null},
               {"player": "Lee", "side": "away", "count": 1, "minute": null}]},
    {"home": "Lions", "away": "Hawks", "homeScore": null, "awayScore": null, "status": "scheduled",
     "when": "Sun 7pm", "venue": "Court 2", "stage": "group", "goals": []}
  ],
  "table": [],
  "rules_notes": [],
  "uncertain": ["Team name in match 3 looks like 'Sharcs'; read as 'Sharks'"]
}}
```

- `stage`: `group`, `quarterfinal`, `semifinal`, `final` or `knockout`. Bracket rounds go in `round` ("Round 1", "Winners R2", "Grand Final").
- `winner`: the name written in the next round of a bracket; filled from the score when both scores are known.
- `goals`: scorers written on a scoresheet, with the side they scored for.
- `table`: a standings table read as-is, used when a photo shows standings but no games.
- `uncertain`: short sentences for the organizer about anything unreadable or contradictory.

## Validation (`app/schema.py`, `app/extract.py`)

- Parsed with Pydantic. A read that does not fit becomes a readable error, never a crash.
- Names are trimmed and whitespace-collapsed. Scores must be whole numbers; blank becomes null.
- Stage names are normalised ("semi-final" becomes `semifinal`). A knockout game with a score gets its winner.
- A missing competition becomes "Untitled cup"; blank table cells become 0; "+3" and "90%" are read as numbers.
- A read with no games and no table is refused ("no matches or table found").

## Checks (`app/standings.py`)

The model's own table is never trusted. The app recomputes standings (3 points a win, 1 a draw; ties by goal difference, then goals for) and flags:

| Card | When |
|---|---|
| Yellow, "look like the same team" | Two names are nearly the same ("Sharks" and "Sharcs"); numbered names like "Team 1", "Team 2" are ignored |
| Red, "listed against itself" | A team plays itself |
| Red, "played without a full score" | A played game with no score and no winner |
| Yellow, "recorded N times" | The same group game appears twice |
| Info, final contradicts the table | The written final is not the table's top two |
| Yellow, "second reader disagrees" | The two readers read a result differently |
| Red, "photos disagree" | Two photos show different results for the same game; the first is kept |
| Info, "name matched" | A spelling was matched to an existing team or player |

## Merging and updates (`app/merge.py`)

- A game is identified by its two sides (either order), its stage and, for knockouts, its round.
- The same result on two photos is one game. A scheduled game that later has a result is updated and keeps its time and field.
- Two differently labelled group rounds between the same sides with different results are a rematch, not a conflict.
- Names: exact matches after lower-casing and removing punctuation are merged automatically; the league's existing spelling wins, then the most common spelling. Near misses are flagged, never merged silently.
- Updating a saved league returns `changes`: `added`, `result` (was not played), `changed` (before and after) and `scorers`.

## Import job (`POST /api/jobs`, `GET /api/jobs/{id}`)

```json
{"id": "0a8b2e5cfb8c", "status": "done", "seconds": 12.3,
 "photos": [{"image": "e1c2.jpg", "status": "done", "seconds": 9.1, "matches": 7, "reader": "gemini-3.8-flash + gpt-6-astra"}],
 "extraction": {"...": "combined read"}, "flags": [], "standings": [],
 "review": {"changes": [{"kind": "changed", "home": "Sharks", "away": "Wolves", "before": "4-2", "after": "4-3"}]}}
```

Photos move `queued` to `reading` to `done` or `error`; one unreadable photo never sinks the others.

## EasyChamp payload (`app/easychamp.py`)

`POST /import/league` with `ImportSource` 99 (external JSON) and `ImportMode` 1 (smart). Every id is `snap:<league>:...` so a second publish converges on the same league, teams, fixtures and players.

- Group games: one "Group stage" (type `league`), one group per board group.
- Knockouts: one "Knockout" stage (type `playoff`), rounds named `quarterfinal`, `semifinal`, `final` by depth and ordered by bracket position (the matches that fed a later match sit together).
- Scorers: team rosters (`TeamMembers`) and goal events (`EventType: scorer`, one per goal).
- Standings-only photos: the teams are created now; results arrive as games are played.
- Fixture dates come from board times ("Sun 10am", "1:30am") in the league's time zone.
