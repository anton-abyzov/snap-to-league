import os
import tempfile

# Tests must never publish to a real EasyChamp: ignore .env and force the dry run.
os.environ["SNAP_NO_DOTENV"] = "1"
os.environ["EC_PUBLISH"] = "0"
for key in ("EC_TOKEN", "EC_TOKEN_CMD", "OPENROUTER_API_KEY"):
    os.environ.pop(key, None)
# and never share the app data folder (leagues, the photo read cache) with a running server
os.environ.setdefault("SNAP_DATA", tempfile.mkdtemp(prefix="snap-test-"))
