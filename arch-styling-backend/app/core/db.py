"""Small SQLite store (stdlib only). Each table keeps a JSON document per row,
so the schema can grow without migrations while the product is moving.
Swap for Postgres in M0 production work; the functions below are the seam."""
import json
import sqlite3
import threading
import time
import uuid

from app.config import DB_PATH

_lock = threading.Lock()
_conn = None

TABLES = ["users", "profiles", "consents", "scans", "looks"]


def conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        for t in TABLES:
            _conn.execute(f"CREATE TABLE IF NOT EXISTS {t} (id TEXT PRIMARY KEY, "
                          f"user_id TEXT, created REAL, doc TEXT)")
            _conn.execute(f"CREATE INDEX IF NOT EXISTS ix_{t}_user ON {t}(user_id)")
        _conn.commit()
    return _conn


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def put(table: str, id: str, user_id: str, doc: dict, created: float = None):
    with _lock:
        c = conn()
        row = c.execute(f"SELECT created FROM {table} WHERE id=?", (id,)).fetchone()
        created = created or (row["created"] if row else time.time())
        c.execute(f"INSERT OR REPLACE INTO {table} (id, user_id, created, doc) VALUES (?,?,?,?)",
                  (id, user_id, created, json.dumps(doc)))
        c.commit()
    return doc


def get(table: str, id: str):
    row = conn().execute(f"SELECT doc FROM {table} WHERE id=?", (id,)).fetchone()
    return json.loads(row["doc"]) if row else None


def list_for_user(table: str, user_id: str, newest_first=True, limit=200):
    order = "DESC" if newest_first else "ASC"
    rows = conn().execute(f"SELECT doc FROM {table} WHERE user_id=? ORDER BY created {order} LIMIT ?",
                          (user_id, limit)).fetchall()
    return [json.loads(r["doc"]) for r in rows]


def delete(table: str, id: str):
    with _lock:
        conn().execute(f"DELETE FROM {table} WHERE id=?", (id,))
        conn().commit()
