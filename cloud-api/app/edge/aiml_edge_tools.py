import random
from services.event_factory import create_ies_event
from services.event_bus import publish
from edge.sqlite_buffer import buffer_event
from edge.edge_state import is_cloud_connected, increment_buffer_pending
from edge.local_inference import run_local_material_risk_inference
from config import SKU, LINE_ID, MODULE_EDGE
import state as app_state


def collect_material_signals() -> dict:
    current_stock = app_state.state["current_stock"]
    daily_demand = app_state.state["daily_demand"]
    stockout_h = round(current_stock / (daily_demand / 24), 2) if daily_demand else 99.0
    is_stockout_imminent = stockout_h < 8.0

    return {
        "stockout_hours": stockout_h,
        "oee": 0.52 if is_stockout_imminent else app_state.state["oee"],
        "consumption_rate": 22.0 if is_stockout_imminent else round(random.uniform(10.5, 15.5), 2),
        "idle_risk": is_stockout_imminent,
        "cycle_time": 7.5 if is_stockout_imminent else round(random.uniform(3.5, 7.5), 2),
        "temperature_c": round(random.uniform(62.0, 78.0), 1),
    }


def run_edge_inference_and_buffer(
    correlation_id: str | None = None
) -> dict:
    signals = collect_material_signals()
    result = run_local_material_risk_inference(signals)
    app_state.state["risk_score"] = result["risk_score"] * 100

    if result["is_critical"]:
        data = {
            "sku_id": SKU,
            "line_id": LINE_ID,
            **result,
            "runtime": "edge",
        }
        event = create_ies_event(
            module_id=MODULE_EDGE, module_version="1.0.0",
            event_type="material_lifecycle_risk_detected",
            category="productivity", severity="critical",
            asset_id=SKU, asset_type="material",
            data=data, correlation_id=correlation_id,
            related_assets=[SKU, LINE_ID, "CONVEYOR-1"],
        )
        if is_cloud_connected():
            publish(event)
        else:
            buffer_event(event.model_dump())
            increment_buffer_pending()
        return {"event": event.model_dump(), "inference": result}

    return {"event": None, "inference": result}


def trigger_local_recommendation(
    risk_score: float, correlation_id: str | None = None
) -> dict:
    recommendations = [
        "Reducir velocidad de línea al 70% para extender vida del material disponible",
        "Activar lote alternativo PERNO-M8-ZINC en ALMACEN-MP-01",
        "Escalar alerta a supervisor de turno A — riesgo crítico de desabasto",
        "Preparar orden urgente para replay cuando Cloud se restaure",
    ]
    selected = recommendations[0] if risk_score > 0.85 else random.choice(recommendations[:2])

    data = {
        "recommendation": selected,
        "risk_score": risk_score,
        "runtime": "edge",
        "cloud_available": is_cloud_connected(),
        "action_required": True,
    }

    if not is_cloud_connected():
        event = create_ies_event(
            module_id=MODULE_EDGE, module_version="1.0.0",
            event_type="operational_recommendation_generated",
            category="productivity", severity="high",
            asset_id=LINE_ID, asset_type="production_line",
            data=data, correlation_id=correlation_id,
            related_assets=[SKU, LINE_ID, "CONVEYOR-1"],
        )
        buffer_event(event.model_dump())
        increment_buffer_pending()
        return {"event": event.model_dump(), "buffered": True}

    return {"event": None, "data": data, "buffered": False}
