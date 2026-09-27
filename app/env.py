"""Load KEY=VALUE lines from ./.env into the environment. The app's own .env wins over the shell."""
import os
from pathlib import Path


def load_env(path: Path = Path(__file__).resolve().parent.parent / ".env") -> None:
    if os.environ.get("SNAP_NO_DOTENV") or not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if value.strip():
            os.environ[key.strip()] = value.strip()
