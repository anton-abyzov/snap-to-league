"""Guards for a public URL: photo checks, per-visitor limits, a daily AI budget and a publish PIN.

- Photos: at most MAX_PHOTOS per import, MAX_BYTES each, and they must open as images.
- Limits: PHOTOS_PER_HOUR per visitor and PHOTOS_PER_DAY for the whole app, so nobody can run up
  the AI bill.
- Publishing to EasyChamp needs SNAP_PUBLISH_PIN; without the PIN a publish is a dry run that
  only shows the payload. Guests can read, review and share a board without it.
"""
from __future__ import annotations

import hmac
import io
import os
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from PIL import Image

MAX_PHOTOS = int(os.environ.get("SNAP_MAX_PHOTOS", "10"))
MAX_BYTES = 12 * 1024 * 1024
_hits: dict[str, deque] = defaultdict(deque)
_day: deque = deque()
_lock = threading.Lock()


def visitor(request: Request) -> str:
    # behind Cloudflare the real address arrives in CF-Connecting-IP
    return request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "unknown")


def check_image(data: bytes) -> str:
    """Return a safe file suffix, or refuse data that is not a readable image."""
    if not data:
        raise HTTPException(400, "The photo is empty")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "A photo is over 12 MB; take it again at a lower resolution")
    try:
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
            fmt = (im.format or "").lower()
    except Exception:  # noqa: BLE001
        raise HTTPException(415, "That file is not a photo this app can read (use JPEG, PNG or WebP)")
    return {"jpeg": ".jpg", "png": ".png", "webp": ".webp", "mpo": ".jpg"}.get(fmt, ".jpg")


def spend(request: Request, photos: int) -> None:
    """Count photos against the visitor's hourly limit and the app's daily budget."""
    per_hour = int(os.environ.get("SNAP_PHOTOS_PER_HOUR", "60"))
    per_day = int(os.environ.get("SNAP_PHOTOS_PER_DAY", "1500"))
    now, who = time.time(), visitor(request)
    with _lock:
        mine = _hits[who]
        while mine and now - mine[0] > 3600:
            mine.popleft()
        while _day and now - _day[0] > 86400:
            _day.popleft()
        if len(mine) + photos > per_hour:
            raise HTTPException(429, f"That is more than {per_hour} photos in an hour from one device; try again later")
        if len(_day) + photos > per_day:
            raise HTTPException(429, "Today's photo reading budget is used up; try again tomorrow")
        mine.extend([now] * photos)
        _day.extend([now] * photos)


_buckets: dict[tuple[str, str], deque] = defaultdict(deque)


def limit(request: Request, bucket: str, per_hour: int) -> None:
    """A simple per-visitor hourly limit for cheap endpoints (voice, saves)."""
    now, key = time.time(), (bucket, visitor(request))
    with _lock:
        q = _buckets[key]
        while q and now - q[0] > 3600:
            q.popleft()
        if len(q) >= per_hour:
            raise HTTPException(429, "Too many requests from this device; try again in a while")
        q.append(now)


def publish_allowed(pin: str | None) -> bool:
    want = os.environ.get("SNAP_PUBLISH_PIN")
    if not want:
        return True  # local use on the organizer's own machine
    return bool(pin) and hmac.compare_digest(pin, want)


def reset() -> None:
    with _lock:
        _hits.clear()
        _day.clear()
        _buckets.clear()
