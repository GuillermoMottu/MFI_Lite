import json
import sqlite3
from config import CLOUD_DB_PATH


def get_correlated_events(correlation_id: str) -> list[dict]:
    conn = sqlite3.connect(CLOUD_DB_PATH)
    rows = conn.execute(
        "SELECT event_json FROM events WHERE correlation_id = ? ORDER BY timestamp ASC",
        (correlation_id,),
    ).fetchall()
    conn.close()
    return [json.loads(r[0]) for r in rows]


def count_recent_events_by_modules(
    modules: list[str], within_seconds: int = 600
) -> int:
    """Cuenta eventos de los módulos dados en la ventana de tiempo."""
    conn = sqlite3.connect(CLOUD_DB_PATH)
    placeholders = ",".join("?" * len(modules))
    rows = conn.execute(
        f"""SELECT COUNT(*) FROM events
            WHERE module_id IN ({placeholders})
            AND datetime(timestamp) >= datetime('now', '-{within_seconds} seconds')""",
        modules,
    ).fetchone()
    conn.close()
    return rows[0] if rows else 0
