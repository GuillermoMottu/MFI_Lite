from fastapi import APIRouter
from auth.middleware import require_role
from services.demo_orchestrator import run_full_demo, reset_demo
from edge.edge_state import set_cloud_connected
from edge.production_edge_tools import detect_material_related_idle_time
from edge.sqlite_buffer import count_pending
from edge.replay_client import replay_pending_events
from edge.aiml_edge_tools import run_edge_inference_and_buffer
from services.event_bus import publish_system_event
import state as app_state

router = APIRouter(prefix="/api/demo", tags=["Demo"])


@router.post("/run")
def run_demo(current_user: dict = require_role("pa", "supervisor", "admin")):
    events = run_full_demo()
    return {
        "status": "completed",
        "events_generated": len(events),
        "correlation_id": app_state.state["last_correlation_id"],
        "events": events,
    }


@router.post("/reset")
def reset(current_user: dict = require_role("admin")):
    reset_demo()
    return {"status": "reset_ok", "message": "Demo state cleared. Ready to run again."}


@router.get("/status")
def demo_status():
    return {
        "demo_running": app_state.state["demo_running"],
        "current_demo_step": app_state.state.get("current_demo_step", 0),
        "cloud_connected": app_state.state["cloud_connected"],
        "buffer_pending": app_state.state["buffer_pending"],
        "events_replayed": app_state.state["events_replayed"],
        "last_replay_at": app_state.state["last_replay_at"],
        "current_stock_units": app_state.state["current_stock"],
        "daily_demand_units": app_state.state["daily_demand"],
        "reorder_point_units": app_state.state["reorder_point"],
        "oee_pct": round(app_state.state["oee"] * 100, 2),
        "risk_score_pct": app_state.state["risk_score"],
        "loss_prevented_mxn": app_state.state["loss_prevented_mxn"],
        "adjusted_plan_units": app_state.state["adjusted_plan_units"],
        "idle_minutes_prevented": app_state.state["idle_minutes_prevented"],
        "purchase_orders": app_state.state["purchase_orders"],
        "last_bottleneck": app_state.state["last_bottleneck"],
        "last_correlation_id": app_state.state["last_correlation_id"],
    }


@router.post("/run-offline-narrative")
def run_offline_narrative(current_user: dict = require_role("supervisor", "admin")):
    """Escenario Edge completo en un solo request:
    1. Cloud Down → 2. Edge detecta + bufferiza → 3. Cloud Up → 4. Replay FIFO."""

    def _notify(phase: str, detail: str) -> None:
        publish_system_event({"__type": "offline_narrative", "phase": phase, "detail": detail})

    # Fase 1: Cloud Down
    set_cloud_connected(False)
    _notify("cloud_down", "Edge activado — Cloud marcado como offline")

    # Fase 2: Edge detecta y bufferiza
    _notify("edge_detecting", "Edge ejecutando Isolation Forest local")
    inference_result = run_edge_inference_and_buffer()

    idle_result = detect_material_related_idle_time()
    buffered_count = count_pending()
    _notify("buffering", f"{buffered_count} evento(s) almacenado(s) en SQLite edge_buffer.db")

    # Fase 3: Cloud Up
    set_cloud_connected(True)
    _notify("cloud_up", "Conectividad Cloud restaurada")

    # Fase 4: Replay FIFO
    _notify("replaying", "Sincronizando buffer → Cloud (FIFO, deduplicación por event_id)")
    replay_result = replay_pending_events()
    _notify("completed", f"Replay completado — {replay_result.get('replayed', 0)} evento(s) sincronizado(s)")

    return {
        "status": "offline_narrative_completed",
        "phases": ["cloud_down", "edge_detecting", "buffering", "cloud_up", "replaying", "completed"],
        "edge_inference": inference_result.get("inference"),
        "idle_detected": idle_result is not None,
        "replayed": replay_result.get("replayed", 0),
        "pending_after": replay_result.get("pending_after", 0),
    }
