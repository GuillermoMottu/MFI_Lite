from datetime import datetime, timezone
from uuid import uuid4

from config import LINE_ID, MODULE_AIML, SKU, WAREHOUSE
from models.ies_event import IESEvent
from services.event_factory import create_ies_event
from services.event_bus import publish
from services.purchase_order_service import create_purchase_order_from_recommendation
from services import operational_store


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def list_recommendations(status: str | None = None) -> list[dict]:
    return operational_store.list_recommendations(status=status)


def get_active_recommendation() -> dict | None:
    pending = operational_store.list_recommendations(status="pending")
    if not pending:
        return None
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(pending, key=lambda r: (priority_order.get(r["priority"], 9), r["created_at"]))[0]


def create_material_risk_recommendation(
    correlation_id: str,
    source_event_id: str,
    impact_mxn: float,
    risk_score: float,
) -> dict:
    existing = operational_store.get_recommendation_by_correlation_type(
        correlation_id,
        "urgent_purchase_order",
    )
    if existing:
        return existing

    recommendation = {
        "recommendation_id": f"REC-{str(uuid4())[:8].upper()}",
        "type": "urgent_purchase_order",
        "priority": "critical",
        "status": "pending",
        "sku_id": SKU,
        "line_id": LINE_ID,
        "reason": "Riesgo de desabasto de SKU-ACERO-M8 puede causar paro de LINE-1.",
        "recommended_action": "Generar orden urgente y ajustar secuencia de producción",
        "alternative_actions": [
            "Usar lote alternativo disponible",
            "Reducir velocidad de línea",
            "Reprogramar jobs no críticos",
        ],
        "estimated_impact_mxn": impact_mxn,
        "risk_score": risk_score,
        "source_event_id": source_event_id,
        "correlation_id": correlation_id,
        "created_at": _now(),
        "decided_at": None,
        "decided_by": None,
        "decision_comment": None,
    }
    return operational_store.insert_recommendation(recommendation)


def create_inventory_risk_recommendation(
    material: dict,
    correlation_id: str,
    source_event_id: str,
) -> dict:
    existing = operational_store.get_recommendation_by_correlation_type(
        correlation_id,
        "urgent_purchase_order",
    )
    if existing:
        return existing

    priority = "critical" if material["risk_status"] == "critical" else "high"
    recommendation = {
        "recommendation_id": f"REC-{str(uuid4())[:8].upper()}",
        "type": "urgent_purchase_order",
        "priority": priority,
        "status": "pending",
        "sku_id": material["sku_id"],
        "line_id": material["line_id"],
        "reason": f"Riesgo de desabasto de {material['sku_id']} en {material['line_id']}.",
        "recommended_action": "Generar orden de compra para recuperar cobertura de inventario",
        "alternative_actions": [
            "Cambiar proveedor por menor lead time",
            "Ajustar prioridad de consumo",
            "Revisar transferencia entre almacenes",
        ],
        "estimated_impact_mxn": material["estimated_impact_mxn"],
        "risk_score": material["risk_score"],
        "source_event_id": source_event_id,
        "correlation_id": correlation_id,
        "created_at": _now(),
        "decided_at": None,
        "decided_by": None,
        "decision_comment": None,
    }
    return operational_store.insert_recommendation(recommendation)


def approve_recommendation(
    recommendation_id: str,
    approved_by: str = "PA-OPERADOR",
    comment: str | None = None,
) -> tuple[dict | None, IESEvent | None, str | None]:
    recommendation = _find_recommendation(recommendation_id)
    if not recommendation:
        return None, None, "not_found"
    if recommendation["status"] != "pending":
        return None, None, "locked_status"
    recommendation["status"] = "approved"
    recommendation["decided_at"] = _now()
    recommendation["decided_by"] = approved_by
    recommendation["decision_comment"] = comment
    operational_store.update_recommendation(recommendation)
    _log_decision(recommendation, "approved", approved_by, comment)
    event = _publish_decision_event(recommendation, "operational_recommendation_approved", "high")
    purchase_order = create_purchase_order_from_recommendation(recommendation, created_by=approved_by)
    recommendation["purchase_order_id"] = purchase_order["po_id"]
    operational_store.update_recommendation(recommendation)
    return recommendation, event, None


def reject_recommendation(
    recommendation_id: str,
    rejected_by: str = "PA-OPERADOR",
    comment: str | None = None,
) -> tuple[dict | None, IESEvent | None, str | None]:
    if not comment or not comment.strip():
        return None, None, "comment_required"
    recommendation = _find_recommendation(recommendation_id)
    if not recommendation:
        return None, None, "not_found"
    if recommendation["status"] != "pending":
        return None, None, "locked_status"
    recommendation["status"] = "rejected"
    recommendation["decided_at"] = _now()
    recommendation["decided_by"] = rejected_by
    recommendation["decision_comment"] = comment.strip()
    operational_store.update_recommendation(recommendation)
    _log_decision(recommendation, "rejected", rejected_by, comment.strip())
    event = _publish_decision_event(recommendation, "operational_recommendation_rejected", "medium")
    return recommendation, event, None


def list_decision_logs() -> list[dict]:
    return operational_store.list_decision_logs()


def _find_recommendation(recommendation_id: str) -> dict | None:
    return operational_store.get_recommendation(recommendation_id)


def _log_decision(recommendation: dict, action: str, user: str, comment: str | None) -> None:
    operational_store.insert_decision_log({
        "decision_id": f"DEC-{str(uuid4())[:8].upper()}",
        "recommendation_id": recommendation["recommendation_id"],
        "action": action,
        "user": user,
        "comment": comment,
        "correlation_id": recommendation["correlation_id"],
        "timestamp": _now(),
    })


def _publish_decision_event(recommendation: dict, event_type: str, severity: str) -> IESEvent:
    data = {
        "recommendation_id": recommendation["recommendation_id"],
        "recommendation_type": recommendation["type"],
        "status": recommendation["status"],
        "decided_by": recommendation["decided_by"],
        "decision_comment": recommendation["decision_comment"],
        "sku_id": recommendation["sku_id"],
        "line_id": recommendation["line_id"],
        "estimated_impact_mxn": recommendation["estimated_impact_mxn"],
    }
    event = create_ies_event(
        module_id=MODULE_AIML,
        module_version="1.0.0",
        event_type=event_type,
        category="productivity",
        severity=severity,
        asset_id=recommendation["sku_id"],
        asset_type="material",
        data=data,
        correlation_id=recommendation["correlation_id"],
        related_assets=[recommendation["sku_id"], recommendation["line_id"], WAREHOUSE],
    )
    publish(event)
    return event
