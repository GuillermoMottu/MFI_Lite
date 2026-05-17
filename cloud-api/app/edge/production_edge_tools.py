import random
from datetime import datetime, timezone
from services.event_factory import create_ies_event
from services.event_bus import publish
from edge.sqlite_buffer import buffer_event
from edge.edge_state import is_cloud_connected, increment_buffer_pending
from config import (
    LINE_ID, LOCATION, MODULE_EDGE, SKU,
    PARTS_PER_MIN_MIN, PARTS_PER_MIN_MAX,
    CYCLE_TIME_MIN, CYCLE_TIME_MAX
)
import state as app_state


def collect_production_data() -> dict:
    parts_per_min = round(random.uniform(PARTS_PER_MIN_MIN, PARTS_PER_MIN_MAX), 1)
    cycle_time = round(random.uniform(CYCLE_TIME_MIN, CYCLE_TIME_MAX), 2)
    consumption_per_piece = 1
    consumption_rate = round(parts_per_min * consumption_per_piece, 2)
    temperature_c = round(random.uniform(62.0, 78.0), 1)

    return {
        "line_id": LINE_ID,
        "location": LOCATION,
        "parts_per_min": parts_per_min,
        "cycle_time_sec": cycle_time,
        "material_consumption_rate": consumption_rate,
        "temperature_c": temperature_c,
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def detect_material_related_idle_time(
    correlation_id: str | None = None
) -> tuple | None:
    current_stock = app_state.state["current_stock"]
    daily_demand = app_state.state["daily_demand"]
    stockout_h = round(current_stock / (daily_demand / 24), 2) if daily_demand else 99
    remaining_shift_h = 7.5
    has_risk = stockout_h < remaining_shift_h or current_stock < 200

    if not has_risk:
        return None

    idle_min = round((remaining_shift_h - stockout_h) * 60) if stockout_h < remaining_shift_h else 45
    idle_min = max(10, min(idle_min, 120))
    severity = "critical" if stockout_h < 2 else "high"

    data = {
        "line_id": LINE_ID,
        "sku_id": SKU,
        "estimated_stockout_hours": stockout_h,
        "remaining_shift_hours": remaining_shift_h,
        "estimated_idle_minutes": idle_min,
        "material_available": current_stock > 50,
        "trigger": "stock_below_threshold",
        "runtime": "edge",
    }

    event = create_ies_event(
        module_id=MODULE_EDGE, module_version="1.0.0",
        event_type="material_related_idle_risk_detected",
        category="productivity", severity=severity,
        asset_id=LINE_ID, asset_type="production_line",
        data=data, correlation_id=correlation_id,
        related_assets=[SKU, LINE_ID, "CONVEYOR-1"],
    )

    if is_cloud_connected():
        publish(event)
    else:
        buffer_event(event.model_dump())
        increment_buffer_pending()

    return event, data


def monitor_material_consumption_rate(
    correlation_id: str | None = None
) -> dict:
    production = collect_production_data()
    standard_rate = 12.5
    real_rate = production["material_consumption_rate"]
    deviation_pct = round(abs(real_rate - standard_rate) / standard_rate * 100, 2)
    has_deviation = deviation_pct > 12.0

    return {
        "line_id": LINE_ID,
        "standard_consumption_rate": standard_rate,
        "real_consumption_rate": real_rate,
        "deviation_pct": deviation_pct,
        "deviation_detected": has_deviation,
        "runtime": "edge",
    }
