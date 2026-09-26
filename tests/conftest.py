import os

# Tests must never publish to a real EasyChamp: ignore .env and force the dry run.
os.environ["SNAP_NO_DOTENV"] = "1"
os.environ["EC_PUBLISH"] = "0"
for key in ("EC_TOKEN", "EC_TOKEN_CMD"):
    os.environ.pop(key, None)
