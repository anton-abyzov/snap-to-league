# Snap to League

Take a phone photo of a tournament whiteboard, a paper scoresheet or a bracket. A frontier vision model reads every match, the app checks the numbers, and you get an editable standings table and a shareable league board that can be published to [EasyChamp](https://easychamp.com).

Built at ShellHacks 2026.

## Why

Most small tournaments still run on whiteboards, paper and group chats. Moving them onto a league platform means retyping every team and result, so organizers never switch. Snap to League turns that setup into one photo.

## How it works

```
phone photo
  -> GPT-6 Astra (via Codex CLI) or Gemini: teams, matches, scores, times, fields, doubts
  -> schema validation (Pydantic)
  -> checks: recompute the table, compare with the model's own table,
             near-duplicate team names, played games without a score,
             a final that contradicts the group table
  -> review screen on the phone: yellow cards for anything uncertain, every cell editable
  -> league board page + EasyChamp POST /import/league payload
```

A second photo of the same board merges into the same league: results update by fixture, new matches are appended, and the table re-ranks.

The model's standings are never trusted. The table is recomputed from the results (3 points for a win, 1 for a draw; ties by goal difference, then goals for), and any disagreement is shown to the organizer.

## Results so far

| Input | Model | Matches read | Table | Time |
|---|---|---|---|---|
| Sample board (`tests/fixtures/board.jpg`, rotated, blurred, handwritten) | GPT-6 Astra, medium effort | 7 / 7 | correct, and it flagged that the written final contradicts the table | 29.5 s |

## Run it

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -e '.[dev,mongo]'
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8077
```

Open `http://<laptop-ip>:8077` on a phone on the same network. "Snap the board" opens the rear camera; "Try the sample board" runs the bundled photo.

The default backend is GPT-6 Astra through the Codex CLI (`codex exec -i photo`), which uses the Codex sign-in on the machine. Set `SNAP_BACKEND=gemini` with `GEMINI_API_KEY` to use Gemini instead, or `SNAP_BACKEND=fixture` to run offline. See `.env.example` for MongoDB Atlas, ElevenLabs and EasyChamp settings.

## Tests

```bash
.venv/bin/python -m pytest -q
```

## Layout

- `app/extract.py` model backends and JSON parsing
- `app/standings.py` standings and consistency checks
- `app/easychamp.py` EasyChamp ImportLeague payload and publishing (dry run unless `EC_PUBLISH=1`)
- `app/store.py` MongoDB Atlas or local JSON storage
- `static/` phone review screen and league board
- `scripts/make_board.py` generates synthetic handwritten boards for testing
