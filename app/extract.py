"""Turn a photo into an Extraction.

Backends, picked with SNAP_BACKEND:
  astra   GPT-6 Astra through the Codex CLI (`codex exec -i photo`). Uses the ChatGPT sign-in
          already on this machine, so no API key is needed.
  gemini  Gemini API over REST. Needs GEMINI_API_KEY.
  fixture Returns tests/fixtures/board_extract.json. For tests and offline demos.
With SNAP_BACKEND unset, astra runs first and gemini is the fallback when a key is set.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import httpx
from pydantic import ValidationError
from PIL import Image, ImageOps

from .schema import Extraction, Row

ROOT = Path(__file__).resolve().parent.parent
PROMPT = (Path(__file__).parent / "prompt.txt").read_text()
FIXTURES = {"board.jpg": ROOT / "tests" / "fixtures" / "board_extract.json",
            "bracket.jpg": ROOT / "tests" / "fixtures" / "bracket_extract.json"}


class ExtractError(RuntimeError):
    pass


def prepare(image: Path, out_dir: Path, long_side: int = 1600) -> Path:
    """Upright (phone EXIF rotation), capped at 1600 px, JPEG. Smaller input, faster read."""
    with Image.open(image) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((long_side, long_side))
        out = out_dir / "photo.jpg"
        im.save(out, quality=85)
    return out


def _parse(text: str) -> tuple[Extraction, list[Row]]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ExtractError(f"model answered without JSON: {text[:200]!r}")
    data = json.loads(text[start:end + 1])
    if "error" in data and "extracted" not in data:
        raise ExtractError(f"model declined: {data['error']}")
    try:
        ex = Extraction.model_validate(data.get("extracted", data))
        rows = [Row.model_validate(r) for r in data.get("standings", []) if isinstance(r, dict)]
    except ValidationError as e:
        raise ExtractError(f"the read did not fit the league format: {str(e)[:200]}")
    if not ex.matches and not ex.table:
        raise ExtractError("no matches or table found on the photo: " + "; ".join(ex.uncertain)[:200])
    return ex, rows


def astra(image: Path) -> str:
    codex = shutil.which("codex")
    if not codex:
        raise ExtractError("codex CLI not found on PATH")
    effort = os.environ.get("ASTRA_EFFORT", "low")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        image = prepare(image, Path(tmp))
        cmd = [codex, "exec", "--ignore-user-config", "--ephemeral",
               "-m", os.environ.get("ASTRA_MODEL", "gpt-6-astra"),
               "-c", f'model_reasoning_effort="{effort}"', "-s", "read-only",
               "--skip-git-repo-check", "-o", str(out), f"--image={image.resolve()}", "-"]
        proc = subprocess.run(cmd, input=PROMPT, text=True, capture_output=True, cwd=tmp,
                              timeout=int(os.environ.get("ASTRA_TIMEOUT", "240")))
        if proc.returncode != 0 or not out.exists():
            raise ExtractError(f"codex exec failed ({proc.returncode}): {proc.stderr[-400:]}")
        return out.read_text()


def gemini(image: Path, model: str | None = None) -> str:
    """Google's Gemini API directly (what the MLH Gemini prize asks for). Needs GEMINI_API_KEY."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ExtractError("GEMINI_API_KEY is not set")
    model = model or os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    with tempfile.TemporaryDirectory() as tmp:
        image = prepare(image, Path(tmp))
        data = image.read_bytes()
    mime = "image/jpeg"
    body = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}},
            {"text": PROMPT},
        ]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                   headers={"x-goog-api-key": key}, json=body, timeout=120)
    if r.status_code != 200:
        raise ExtractError(f"gemini {r.status_code}: {r.text[:300]}")
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


LAST_USAGE: dict = {}


def openrouter(image: Path, model: str | None = None) -> str:
    """Any vision model on OpenRouter (model, else OPENROUTER_MODEL, else Gemini 3.8 Flash). Needs OPENROUTER_API_KEY."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ExtractError("OPENROUTER_API_KEY is not set")
    with tempfile.TemporaryDirectory() as tmp:
        data = base64.b64encode(prepare(image, Path(tmp)).read_bytes()).decode()
    body = {
        "model": model or os.environ.get("OPENROUTER_MODEL", "google/gemini-3.8-flash"),
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data}"}},
            {"type": "text", "text": PROMPT},
        ]}],
        "response_format": {"type": "json_object"},
        "usage": {"include": True},
        "max_tokens": int(os.environ.get("OPENROUTER_MAX_TOKENS", "4000")),
    }
    effort = os.environ.get("OPENROUTER_EFFORT")
    if effort:
        body["reasoning"] = {"effort": effort}
    r = httpx.post("https://openrouter.ai/api/v1/chat/completions", json=body, timeout=180,
                   headers={"Authorization": f"Bearer {key}", "X-Title": "Snap to League"})
    if r.status_code != 200:
        raise ExtractError(f"openrouter {r.status_code}: {r.text[:300]}")
    out = r.json()
    if model is None:  # benchmark calls read the last cost
        LAST_USAGE.clear()
        LAST_USAGE.update(out.get("usage") or {})
    return out["choices"][0]["message"]["content"]


def fixture(image: Path) -> str:
    """Offline stand-in: the bracket answer for bracket photos, the board answer otherwise."""
    raw = image.read_bytes()
    for name, answer in FIXTURES.items():
        if (ROOT / "tests" / "fixtures" / name).read_bytes() == raw:
            return answer.read_text()
    return FIXTURES["board.jpg"].read_text()


BACKENDS = {"astra": astra, "openrouter": openrouter, "gemini": gemini, "fixture": fixture}


PRIMARY = os.environ.get("SNAP_PRIMARY_MODEL", "google/gemini-3.8-flash")
# Readers an organizer can pick. Open-weight models are marked; costs are per photo from scripts/bench.py.
READERS = {
    "google/gemini-3.8-flash": {"label": "Gemini 3.8 Flash", "open": False, "cost": 0.005},
    "z-ai/glm-5.3-flash": {"label": "GLM 5.3 Flash", "open": True, "cost": 0.001},
    "anthropic/claude-sonnet-5": {"label": "Claude Sonnet 5", "open": False, "cost": 0.018},
    "openai/gpt-6-astra": {"label": "GPT-6 Astra", "open": False, "cost": 0.032},
    "qwen/qwen3.8-flash": {"label": "Qwen 3.8 Flash", "open": True, "cost": 0.0013},
}
SECOND = os.environ.get("SNAP_SECOND_MODEL", "openai/gpt-6-astra")


def result_key(m) -> tuple:
    """One result, independent of which side was written first. Group games carry no winner."""
    sides = frozenset({(m.home.casefold(), m.homeScore), (m.away.casefold(), m.awayScore)})
    return sides, m.status, (m.winner.casefold() if m.winner and m.stage != "group" else None)


def disagreements(first: Extraction, second: Extraction, second_name: str) -> list[str]:
    a = {result_key(m): m for m in first.matches}
    b = {result_key(m): m for m in second.matches}
    notes = []
    for k, m in b.items():
        if k not in a:
            score = f"{m.homeScore}-{m.awayScore}" if m.homeScore is not None else (f"won by {m.winner}" if m.winner else "not played")
            notes.append(f"{second_name} read {m.home} v {m.away} as {score}; check the photo")
    if len(first.matches) != len(second.matches):
        notes.append(f"{second_name} counted {len(second.matches)} matches, the main reader {len(first.matches)}")
    return notes[:6]


def _read(name: str, image: Path, model: str | None = None) -> tuple[Extraction, list[Row]]:
    if name == "openrouter" and model and model.startswith("google/") and os.environ.get("GEMINI_API_KEY"):
        return _parse(gemini(image, model.split("/", 1)[1]))  # Gemini through Google's own API
    if name == "openrouter" and model:
        return _parse(openrouter(image, model))
    return _parse(BACKENDS[name](image))


def extract(image: Path, reader: str | None = None) -> tuple[Extraction, list[Row], str, float, list[str]]:
    """Read the photo. Returns extraction, model table, reader name, seconds and second-reader notes.

    With SNAP_BACKEND unset and an OpenRouter key, the main reader and a second reader run side by side;
    wherever they disagree on a result the organizer gets a card to check. Without a key it falls back to
    Astra through the Codex CLI.
    """
    t0 = time.monotonic()
    chosen = os.environ.get("SNAP_BACKEND")
    primary = reader if reader in READERS else PRIMARY
    if not chosen and os.environ.get("OPENROUTER_API_KEY"):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(2) as pool:
            main_job = pool.submit(_read, "openrouter", image, primary)
            second_job = pool.submit(_read, "openrouter", image, SECOND) if SECOND and SECOND != primary else None
            try:
                ex, rows = main_job.result()
                name = primary.split("/")[-1]
            except (ExtractError, ValueError, KeyError, httpx.HTTPError) as e:
                if not second_job:
                    raise ExtractError(f"{primary}: {e}")
                ex, rows = second_job.result()
                note = f"{primary.split('/')[-1]} could not read this photo ({str(e)[:120]}); showing {SECOND.split('/')[-1]}'s read"
                return ex, rows, SECOND.split("/")[-1], round(time.monotonic() - t0, 1), [note]
            notes: list[str] = []
            if second_job:
                try:
                    other, _ = second_job.result(timeout=max(5.0, 45 - (time.monotonic() - t0)))
                    notes = disagreements(ex, other, SECOND.split("/")[-1])
                    name = f"{name} + {SECOND.split('/')[-1]}"
                except Exception:  # the second opinion is optional; never block the organizer on it
                    notes = []
            return ex, rows, name, round(time.monotonic() - t0, 1), notes
    order = [chosen] if chosen else ["astra"] + (["gemini"] if os.environ.get("GEMINI_API_KEY") else [])
    errors = []
    for name in order:
        try:
            ex, rows = _read(name, image)
            return ex, rows, name, round(time.monotonic() - t0, 1), []
        except (ExtractError, subprocess.TimeoutExpired, ValueError, KeyError) as e:
            errors.append(f"{name}: {e}")
    raise ExtractError("; ".join(errors))
