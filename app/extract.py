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
import mimetypes
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import httpx

from .schema import Extraction, Row

ROOT = Path(__file__).resolve().parent.parent
PROMPT = (Path(__file__).parent / "prompt.txt").read_text()
FIXTURE = ROOT / "tests" / "fixtures" / "board_extract.json"


class ExtractError(RuntimeError):
    pass


def _parse(text: str) -> tuple[Extraction, list[Row]]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ExtractError(f"model answered without JSON: {text[:200]!r}")
    data = json.loads(text[start:end + 1])
    if "error" in data and "extracted" not in data:
        raise ExtractError(f"model declined: {data['error']}")
    ex = Extraction.model_validate(data.get("extracted", data))
    rows = [Row.model_validate(r) for r in data.get("standings", [])]
    return ex, rows


def astra(image: Path) -> str:
    codex = shutil.which("codex")
    if not codex:
        raise ExtractError("codex CLI not found on PATH")
    effort = os.environ.get("ASTRA_EFFORT", "medium")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        cmd = [codex, "exec", "-m", os.environ.get("ASTRA_MODEL", "gpt-6-astra"),
               "-c", f'model_reasoning_effort="{effort}"', "-s", "read-only",
               "--skip-git-repo-check", "-o", str(out), "-i", str(image), "-"]
        proc = subprocess.run(cmd, input=PROMPT, text=True, capture_output=True, cwd=tmp,
                              timeout=int(os.environ.get("ASTRA_TIMEOUT", "240")))
        if proc.returncode != 0 or not out.exists():
            raise ExtractError(f"codex exec failed ({proc.returncode}): {proc.stderr[-400:]}")
        return out.read_text()


def gemini(image: Path) -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ExtractError("GEMINI_API_KEY is not set")
    model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
    mime = mimetypes.guess_type(image.name)[0] or "image/jpeg"
    body = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": mime, "data": base64.b64encode(image.read_bytes()).decode()}},
            {"text": PROMPT},
        ]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                   headers={"x-goog-api-key": key}, json=body, timeout=120)
    if r.status_code != 200:
        raise ExtractError(f"gemini {r.status_code}: {r.text[:300]}")
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def fixture(image: Path) -> str:
    return FIXTURE.read_text()


BACKENDS = {"astra": astra, "gemini": gemini, "fixture": fixture}


def extract(image: Path) -> tuple[Extraction, list[Row], str, float]:
    chosen = os.environ.get("SNAP_BACKEND")
    order = [chosen] if chosen else ["astra"] + (["gemini"] if os.environ.get("GEMINI_API_KEY") else [])
    errors = []
    for name in order:
        t0 = time.monotonic()
        try:
            ex, rows = _parse(BACKENDS[name](image))
            return ex, rows, name, round(time.monotonic() - t0, 1)
        except (ExtractError, subprocess.TimeoutExpired, ValueError, KeyError) as e:
            errors.append(f"{name}: {e}")
    raise ExtractError("; ".join(errors))
