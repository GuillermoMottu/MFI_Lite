from fastapi import APIRouter
from edge.edge_state import set_cloud_connected
from edge.sqlite_buffer import count_pending, buffer_event
from edge.replay_client import replay_pending_events
from services.event_factory import create_ies_event
from config import SKU, MODULE_EDGE
import state as app_state

router = APIRouter(prefix="/api/offline", tags=["Offline"])


@router.post("/simulate-cloud-down")
def simulate_cloud_down():
    set_cloud_connected(False)
    return {
        "status": "cloud_disconnected",
        "cloud_connected": False,
        "buffer_pending": count_pending(),
        "message": "Cloud marcado como offline. Edge sigue operando. Eventos se bufferizarán en SQLite.",
    }


@router.post("/simulate-cloud-up")
def simulate_cloud_up():
    set_cloud_connected(True)
    return {
        "status": "cloud_connected",
        "cloud_connected": True,
        "buffer_pending": count_pending(),
        "message": "Cloud restaurado. Ejecuta /replay para sincronizar eventos pendientes.",
    }


@router.post("/replay")
def replay():
    if not app_state.state["cloud_connected"]:
        return {"error": "Cloud still offline. Restore connection first with /simulate-cloud-up"}
    result = replay_pending_events()
    return {"status": "replay_completed", **result}


@router.get("/buffer-status")
def buffer_status():
    return {
        "cloud_connected": app_state.state["cloud_connected"],
        "buffer_pending": count_pending(),
        "events_replayed": app_state.state["events_replayed"],
        "last_replay_at": app_state.state["last_replay_at"],
    }


@router.post("/simulate-low-stock")
def simulate_low_stock():
    app_state.state["current_stock"] = 120
    return {
        "status": "stock_forced_low",
        "current_stock_units": 120,
        "message": "Stock forzado a 120 unidades para activar riesgo crítico.",
    }
