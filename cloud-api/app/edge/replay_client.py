from datetime import datetime, timezone
from edge.sqlite_buffer import get_pending_events, mark_synced, count_pending
from services.event_bus import publish
from models.ies_event import IESEvent
import state as app_state


def replay_pending_events() -> dict:
    pending = get_pending_events()
    replayed = 0
    rejected = 0

    for event_dict in pending:
        try:
            event = IESEvent(**event_dict)
            publish(event, source="edge_replay")
            mark_synced(event.event_id)
            replayed += 1
        except Exception:
            rejected += 1

    app_state.state["events_replayed"] += replayed
    app_state.state["buffer_pending"] = count_pending()
    app_state.state["last_replay_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "replayed": replayed,
        "rejected": rejected,
        "pending_remaining": count_pending(),
        "replayed_at": app_state.state["last_replay_at"],
    }
