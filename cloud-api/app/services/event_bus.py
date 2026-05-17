import asyncio
import json
import sqlite3
from models.ies_event import IESEvent
from config import CLOUD_DB_PATH

_subscribers: list[asyncio.Queue] = []
_db_initialized = False


def _init_db() -> None:
    global _db_initialized
    if _db_initialized:
        return
    conn = sqlite3.connect(CLOUD_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            module_id TEXT,
            event_type TEXT,
            severity TEXT,
            asset_id TEXT,
            correlation_id TEXT,
            event_json TEXT NOT NULL,
            source TEXT DEFAULT 'cloud'
        )
    """)
    conn.commit()
    conn.close()
    _db_initialized = True


def publish(event: IESEvent, source: str = "cloud") -> None:
    _init_db()
    event_dict = event.model_dump()
    event_json = json.dumps(event_dict)
    correlation_id = event.metadata.get("correlation_id")

    conn = sqlite3.connect(CLOUD_DB_PATH)
    conn.execute(
        """INSERT OR IGNORE INTO events
           (event_id, timestamp, module_id, event_type, severity, asset_id, correlation_id, event_json, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            event.event_id,
            event.timestamp,
            event.module.get("id"),
            event.event.get("type"),
            event.event.get("severity"),
            event.asset.get("asset_id"),
            correlation_id,
            event_json,
            source,
        ),
    )
    conn.commit()
    conn.close()

    # Notificar a todos los suscriptores SSE
    payload = f"data: {event_json}\n\n"
    for q in list(_subscribers):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            pass


def list_events(
    limit: int = 50,
    module_id: str | None = None,
    asset_id: str | None = None,
    event_type: str | None = None,
    correlation_id: str | None = None,
) -> list[dict]:
    _init_db()
    conditions = []
    params = []
    if module_id:
        conditions.append("module_id = ?")
        params.append(module_id)
    if asset_id:
        conditions.append("asset_id = ?")
        params.append(asset_id)
    if event_type:
        conditions.append("event_type = ?")
        params.append(event_type)
    if correlation_id:
        conditions.append("correlation_id = ?")
        params.append(correlation_id)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    conn = sqlite3.connect(CLOUD_DB_PATH)
    rows = conn.execute(
        f"SELECT event_json FROM events {where} ORDER BY timestamp DESC LIMIT ?", params
    ).fetchall()
    conn.close()
    return [json.loads(r[0]) for r in rows]


def clear_demo_events() -> None:
    _init_db()
    conn = sqlite3.connect(CLOUD_DB_PATH)
    conn.execute("DELETE FROM events")
    conn.commit()
    conn.close()


def publish_system_event(payload: dict) -> None:
    """Emite un mensaje de sistema sobre SSE sin escribir a SQLite.
    Usar para notificaciones de paso del demo (demo_step_started, etc.)."""
    message = f"data: {json.dumps(payload)}\n\n"
    for q in list(_subscribers):
        try:
            q.put_nowait(message)
        except asyncio.QueueFull:
            pass


def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=200)
    _subscribers.append(q)
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    if q in _subscribers:
        _subscribers.remove(q)
