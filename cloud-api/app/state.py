import random
from datetime import datetime, timezone
from config import (
    STOCK_INITIAL_MIN, STOCK_INITIAL_MAX, OEE_BASE,
    AVAILABILITY_BASE, PERFORMANCE_BASE, QUALITY_BASE,
    PLAN_ORIGINAL_UNITS, DAILY_DEMAND_MIN, DAILY_DEMAND_MAX
)

_initial_stock = random.randint(STOCK_INITIAL_MIN, STOCK_INITIAL_MAX)
_initial_daily_demand = random.randint(DAILY_DEMAND_MIN, DAILY_DEMAND_MAX)

# Estado mutable del demo — se resetea con /api/demo/reset
state: dict = {
    "current_stock": _initial_stock,
    "daily_demand": float(_initial_daily_demand),
    "reorder_point": 0,
    "oee": OEE_BASE,
    "availability": AVAILABILITY_BASE,
    "performance": PERFORMANCE_BASE,
    "quality": QUALITY_BASE,
    "risk_score": 0.0,
    "plan_units": PLAN_ORIGINAL_UNITS,
    "adjusted_plan_units": PLAN_ORIGINAL_UNITS,
    "idle_minutes_prevented": 0,
    "loss_prevented_mxn": 0.0,
    "cloud_connected": True,
    "demo_running": False,
    "last_correlation_id": None,
    "buffer_pending": 0,
    "events_replayed": 0,
    "last_replay_at": None,
    "purchase_orders": [],
    "last_bottleneck": None,
    # Step indicator: número de paso activo durante el demo (0 = idle)
    "current_demo_step": 0,
    # Última inferencia Edge con señales y score
    "last_inference": None,
    # Historial de stock: lista de {timestamp, stock, reorder_point}
    "stock_history": [],
}


def _snapshot_stock() -> None:
    """Agrega punto al historial de stock con timestamp actual."""
    state["stock_history"].append({
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stock": state["current_stock"],
        "reorder_point": state["reorder_point"],
    })


def reset_state() -> None:
    global state
    new_stock = random.randint(STOCK_INITIAL_MIN, STOCK_INITIAL_MAX)
    new_demand = float(random.randint(DAILY_DEMAND_MIN, DAILY_DEMAND_MAX))
    state.update({
        "current_stock": new_stock,
        "daily_demand": new_demand,
        "reorder_point": 0,
        "oee": OEE_BASE,
        "availability": AVAILABILITY_BASE,
        "performance": PERFORMANCE_BASE,
        "quality": QUALITY_BASE,
        "risk_score": 0.0,
        "plan_units": PLAN_ORIGINAL_UNITS,
        "adjusted_plan_units": PLAN_ORIGINAL_UNITS,
        "idle_minutes_prevented": 0,
        "loss_prevented_mxn": 0.0,
        "cloud_connected": True,
        "demo_running": False,
        "last_correlation_id": None,
        "buffer_pending": 0,
        "events_replayed": 0,
        "last_replay_at": None,
        "purchase_orders": [],
        "last_bottleneck": None,
        "current_demo_step": 0,
        "last_inference": None,
        "stock_history": [],
    })
