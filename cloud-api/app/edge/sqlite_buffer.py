import json
import sqlite3
from config import EDGE_DB_PATH

_initialized = False


def _init() -> None:
    global _initialized
    if _initialized:
        return
    conn = sqlite3.connect(EDGE_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS offline_events (
            event_id TEXT PRIMARY KEY,
            event_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            synced INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    _initialized = True


def buffer_event(event_dict: dict) -> None:
    _init()
    conn = sqlite3.connect(EDGE_DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO offline_events (event_id, event_json, created_at, synced) VALUES (?, ?, ?, 0)",
        (event_dict["event_id"], json.dumps(event_dict), event_dict["timestamp"]),
    )
    conn.commit()
    conn.close()


def get_pending_events() -> list[dict]:
    _init()
    conn = sqlite3.connect(EDGE_DB_PATH)
    rows = conn.execute(
        "SELECT event_json FROM offline_events WHERE synced = 0 ORDER BY created_at ASC"
    ).fetchall()
    conn.close()
    return [json.loads(r[0]) for r in rows]


def mark_synced(event_id: str) -> None:
    _init()
    conn = sqlite3.connect(EDGE_DB_PATH)
    conn.execute("UPDATE offline_events SET synced = 1 WHERE event_id = ?", (event_id,))
    conn.commit()
    conn.close()


def count_pending() -> int:
    _init()
    conn = sqlite3.connect(EDGE_DB_PATH)
    row = conn.execute("SELECT COUNT(*) FROM offline_events WHERE synced = 0").fetchone()
    conn.close()
    return row[0] if row else 0


def clear_buffer() -> None:
    _init()
    conn = sqlite3.connect(EDGE_DB_PATH)
    conn.execute("DELETE FROM offline_events")
    conn.commit()
    conn.close()
