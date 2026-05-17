from datetime import datetime, timedelta, timezone
from uuid import uuid4

from config import LINE_ID, MODULE_ERP, SKU, UNIT_COST_MXN_MIN, UNIT_COST_MXN_MAX, WAREHOUSE
from services.event_factory import create_ies_event
from services.event_bus import publish
from services import operational_store
import state as app_state


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _date_after(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d")


def list_purchase_orders(status: str | None = None) -> list[dict]:
    return operational_store.list_purchase_orders(status=status)


def list_suppliers(sku_id: str = SKU) -> list[dict]:
    return operational_store.list_suppliers(sku_id=sku_id)


def get_purchase_order(po_id: str) -> dict | None:
    return operational_store.get_purchase_order(po_id)


def create_purchase_order_from_recommendation(
    recommendation: dict,
    created_by: str = "PA-OPERADOR",
) -> dict:
    existing = operational_store.get_purchase_order_by_recommendation(recommendation["recommendation_id"])
    if existing:
        return existing

    supplier = _select_supplier(recommendation)
    if not supplier:
        raise ValueError(f"No active supplier found for SKU {recommendation['sku_id']}")
    quantity = _recommended_quantity(recommendation["sku_id"])
    order = _build_order(
        recommendation=recommendation,
        supplier=supplier,
        quantity_units=quantity,
        status="draft",
        created_by=created_by,
    )
    operational_store.insert_purchase_order(order)
    _publish_po_event(order, "purchase_order_draft_created", "medium")
    return order


def update_purchase_order(
    po_id: str,
    supplier_id: str | None = None,
    quantity_units: int | None = None,
    required_date: str | None = None,
    comment: str | None = None,
) -> tuple[dict | None, str | None]:
    order = get_purchase_order(po_id)
    if not order:
        return None, "not_found"
    if order["status"] not in ("draft", "pending_approval"):
        return None, "locked_status"

    if supplier_id:
        supplier = _find_supplier(supplier_id, order["sku_id"])
        if not supplier:
            return None, "supplier_not_found"
        order["supplier_id"] = supplier["supplier_id"]
        order["supplier_name"] = supplier["name"]
        order["supplier_lead_time_days"] = supplier["lead_time_days"]
        order["unit_cost_mxn"] = supplier["unit_cost_mxn"]
        order["estimated_arrival_date"] = _date_after(supplier["lead_time_days"])

    if quantity_units is not None:
        if quantity_units <= 0:
            return None, "invalid_quantity"
        order["quantity_units"] = quantity_units

    if required_date:
        order["required_date"] = required_date

    if comment is not None:
        order["pa_comment"] = comment

    order["total_cost_mxn"] = round(order["quantity_units"] * order["unit_cost_mxn"], 2)
    order["updated_at"] = _now()
    operational_store.update_purchase_order(order)
    _publish_po_event(order, "purchase_order_updated", "low")
    return order, None


def approve_purchase_order(
    po_id: str,
    approved_by: str = "PA-OPERADOR",
    comment: str | None = None,
) -> tuple[dict | None, str | None]:
    order = get_purchase_order(po_id)
    if not order:
        return None, "not_found"
    if not order["supplier_id"]:
        return None, "missing_supplier"
    if order["quantity_units"] <= 0:
        return None, "invalid_quantity"
    if order["status"] not in ("draft", "pending_approval"):
        return None, "locked_status"

    order["status"] = "approved"
    order["approved_by"] = approved_by
    order["approved_at"] = _now()
    order["pa_comment"] = comment if comment is not None else order.get("pa_comment")
    order["updated_at"] = _now()
    operational_store.update_purchase_order(order)
    _publish_po_event(order, "purchase_order_approved", "high")
    return order, None


def _select_supplier(recommendation: dict) -> dict:
    suppliers = list_suppliers(recommendation["sku_id"])
    if not suppliers:
        return {}
    if recommendation["priority"] == "critical":
        return min(suppliers, key=lambda supplier: supplier["lead_time_days"])
    return min(suppliers, key=lambda supplier: supplier["unit_cost_mxn"])


def _find_supplier(supplier_id: str, sku_id: str) -> dict | None:
    return operational_store.get_supplier(supplier_id, sku_id)


def _recommended_quantity(sku_id: str) -> int:
    material = operational_store.get_material(sku_id)
    if material:
        daily_demand = material["daily_demand_units"]
        reorder_point = material["reorder_point_units"]
        current_stock = material["current_stock_units"]
    else:
        daily_demand = app_state.state["daily_demand"]
        reorder_point = app_state.state["reorder_point"]
        current_stock = app_state.state["current_stock"]
    coverage_units = round(daily_demand * 7)
    shortage_units = max(0, reorder_point - current_stock)
    return max(500, coverage_units, shortage_units)


def _build_order(
    recommendation: dict,
    supplier: dict,
    quantity_units: int,
    status: str,
    created_by: str,
) -> dict:
    unit_cost = supplier.get("unit_cost_mxn") or round((UNIT_COST_MXN_MIN + UNIT_COST_MXN_MAX) / 2, 2)
    return {
        "po_id": f"PO-OPS-{str(uuid4())[:8].upper()}",
        "sku_id": recommendation["sku_id"],
        "line_id": recommendation["line_id"],
        "supplier_id": supplier["supplier_id"],
        "supplier_name": supplier["name"],
        "supplier_lead_time_days": supplier["lead_time_days"],
        "quantity_units": int(quantity_units),
        "unit_cost_mxn": unit_cost,
        "total_cost_mxn": round(quantity_units * unit_cost, 2),
        "required_date": _date_after(1),
        "estimated_arrival_date": _date_after(supplier["lead_time_days"]),
        "status": status,
        "created_by": created_by,
        "created_at": _now(),
        "updated_at": _now(),
        "approved_by": None,
        "approved_at": None,
        "source_recommendation_id": recommendation["recommendation_id"],
        "correlation_id": recommendation["correlation_id"],
        "pa_comment": recommendation.get("decision_comment"),
    }


def _publish_po_event(order: dict, event_type: str, severity: str):
    data = {
        "po_id": order["po_id"],
        "sku_id": order["sku_id"],
        "supplier_id": order["supplier_id"],
        "supplier_name": order["supplier_name"],
        "quantity_units": order["quantity_units"],
        "unit_cost_mxn": order["unit_cost_mxn"],
        "total_cost_mxn": order["total_cost_mxn"],
        "required_date": order["required_date"],
        "estimated_arrival_date": order["estimated_arrival_date"],
        "status": order["status"],
        "source_recommendation_id": order["source_recommendation_id"],
    }
    event = create_ies_event(
        module_id=MODULE_ERP,
        module_version="1.0.0",
        event_type=event_type,
        category="productivity",
        severity=severity,
        asset_id=order["sku_id"],
        asset_type="material",
        data=data,
        correlation_id=order["correlation_id"],
        related_assets=[order["sku_id"], LINE_ID, WAREHOUSE],
    )
    publish(event)
    return event
