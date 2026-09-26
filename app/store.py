"""Snaps and leagues live in MongoDB Atlas when MONGODB_URI is set, otherwise in ./data as JSON."""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("SNAP_DATA", ROOT / "data"))


class _Files:
    def __init__(self, kind: str):
        self.dir = DATA / kind
        self.dir.mkdir(parents=True, exist_ok=True)

    def put(self, doc: dict) -> None:
        (self.dir / f"{doc['id']}.json").write_text(json.dumps(doc, indent=1, default=str))

    def get(self, id_: str) -> dict | None:
        p = self.dir / f"{id_}.json"
        return json.loads(p.read_text()) if p.exists() else None


class _Mongo:
    def __init__(self, kind: str):
        from pymongo import MongoClient
        self.col = MongoClient(os.environ["MONGODB_URI"])[os.environ.get("MONGODB_DB", "snap_to_league")][kind]

    def put(self, doc: dict) -> None:
        self.col.replace_one({"_id": doc["id"]}, {**doc, "_id": doc["id"]}, upsert=True)

    def get(self, id_: str) -> dict | None:
        doc = self.col.find_one({"_id": id_})
        if doc:
            doc.pop("_id", None)
        return doc


def collection(kind: str):
    return _Mongo(kind) if os.environ.get("MONGODB_URI") else _Files(kind)


def images_dir() -> Path:
    d = DATA / "images"
    d.mkdir(parents=True, exist_ok=True)
    return d
