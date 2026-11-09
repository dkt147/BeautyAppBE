"""Small SQLite store (stdlib only). Each table keeps a JSON document per row,
so the schema can grow without migrations while the product is moving.
Swap for Postgres in M0 production work; the functions below are the seam.

Concurrency (QA report item 1): one connection per thread, because FastAPI
runs sync routes in a thread pool. The old single shared connection let one
thread's read run inside another thread's open write, which gave intermittent
500s when the app loaded several things at once. WAL lets reads run while a
write commits, and busy_timeout makes a writer wait for the lock instead of
failing with "database is locked"."""
import json
import sqlite3
import threading
import time
import uuid

from app.config import DB_BUSY_TIMEOUT_MS, DB_PATH

_local = threading.local()
_schema_lock = threading.Lock()
_schema_ready = False
_write_lock = threading.Lock()      # one writer at a time inside this process

TABLES = ["users", "profiles", "consents", "scans", "looks",
          "auth_sessions", "otp_codes", "outbox",
          "tracing_sessions", "guides", "deletion_audit",
          "subscriptions", "billing_events", "devices", "support_messages"]


def _open() -> sqlite3.Connection:
    # isolation_level=None: autocommit; put() opens its own short transaction.
    c = sqlite3.connect(DB_PATH, timeout=DB_BUSY_TIMEOUT_MS / 1000, isolation_level=None,
                        check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute(f"PRAGMA busy_timeout={int(DB_BUSY_TIMEOUT_MS)}")
    # WAL is stored in the database file, so it is switched on once. Setting
    # it needs an exclusive lock, which would fail while other threads are
    # busy, so a connection only asks when the file is not in WAL yet.
    if c.execute("PRAGMA journal_mode").fetchone()[0].lower() != "wal":
        with _schema_lock:
            c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")
    return c


def _ensure_schema(c: sqlite3.Connection):
    global _schema_ready
    if _schema_ready:
        return
    with _schema_lock:
        if _schema_ready:
            return
        for t in TABLES:
            c.execute(f"CREATE TABLE IF NOT EXISTS {t} (id TEXT PRIMARY KEY, "
                      f"user_id TEXT, created REAL, doc TEXT)")
            c.execute(f"CREATE INDEX IF NOT EXISTS ix_{t}_user ON {t}(user_id)")
        _schema_ready = True


def conn() -> sqlite3.Connection:
    """This thread's connection."""
    c = getattr(_local, "conn", None)
    if c is None:
        c = _local.conn = _open()
    _ensure_schema(c)
    return c


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def put(table: str, id: str, user_id: str, doc: dict, created: float = None):
    c = conn()
    with _write_lock:
        c.execute("BEGIN IMMEDIATE")
        try:
            row = c.execute(f"SELECT created FROM {table} WHERE id=?", (id,)).fetchone()
            created = created or (row["created"] if row else time.time())
            c.execute(f"INSERT OR REPLACE INTO {table} (id, user_id, created, doc) VALUES (?,?,?,?)",
                      (id, user_id, created, json.dumps(doc)))
            c.execute("COMMIT")
        except BaseException:
            c.execute("ROLLBACK")
            raise
    return doc


def set_fields(table: str, id: str, fields: dict) -> bool:
    """Set a few fields inside one stored document in a single UPDATE, without
    reading and rewriting the whole document. Keys may be dotted paths
    ("flags.home_seen"); a parent object must already exist. Used for the
    small bookkeeping writes made while serving GET requests, so concurrent
    requests cannot overwrite each other's changes. Returns True if the row
    exists."""
    if not fields:
        return False
    args, sql = [], "doc"
    for key, value in fields.items():
        if not all(p.isidentifier() for p in key.split(".")):
            raise ValueError(key)
        sql = f"json_set({sql}, '$.{key}', json(?))"
        args.append(json.dumps(value))
    c = conn()
    with _write_lock:
        cur = c.execute(f"UPDATE {table} SET doc = {sql} WHERE id=?", (*args, id))     # autocommit
    return cur.rowcount > 0


def get(table: str, id: str):
    row = conn().execute(f"SELECT doc FROM {table} WHERE id=?", (id,)).fetchone()
    return json.loads(row["doc"]) if row else None


def list_for_user(table: str, user_id: str, newest_first=True, limit=200):
    order = "DESC" if newest_first else "ASC"
    rows = conn().execute(f"SELECT doc FROM {table} WHERE user_id=? ORDER BY created {order} LIMIT ?",
                          (user_id, limit)).fetchall()
    return [json.loads(r["doc"]) for r in rows]


def find_one(table: str, field: str, value):
    """First row whose JSON doc has doc[field] == value (e.g. users by email)."""
    if not field.isidentifier():
        raise ValueError(field)
    row = conn().execute(f"SELECT doc FROM {table} WHERE json_extract(doc, '$.{field}') = ? LIMIT 1",
                         (value,)).fetchone()
    return json.loads(row["doc"]) if row else None


def find_all(table: str, field: str, value):
    if not field.isidentifier():
        raise ValueError(field)
    rows = conn().execute(f"SELECT doc FROM {table} WHERE json_extract(doc, '$.{field}') = ?",
                          (value,)).fetchall()
    return [json.loads(r["doc"]) for r in rows]


def delete(table: str, id: str):
    c = conn()
    with _write_lock:
        c.execute(f"DELETE FROM {table} WHERE id=?", (id,))     # autocommit
