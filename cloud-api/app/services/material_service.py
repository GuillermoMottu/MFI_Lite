from uuid import uuid4

from config import SKU
from services import operational_store
from services.recommendation_service import create_inventory_risk_recommendation


def list_materials(status: str | None = None) -> list[dict]:
    return operational_store.list_materials(status=status)


def get_material(sku_id: str) -> dict | None:
    return operational_store.get_material(sku_id)


def update_material(sku_id: str, payload: dict) -> tuple[dict | None, str | None]:
    current = operational_store.get_material(sku_id)
    if not current:
        return None, "not_found"
    allowed = {
        "name",
        "line_id",
        "warehouse",
        "current_stock_units",
        "reorder_point_units",
        "daily_demand_units",
        "unit_cost_mxn",
        "criticality",
    }
    updated = {
        **current,
        **{key: value for key, value in payload.items() if key in allowed and value is not None},
        "sku_id": sku_id,
    }
    return operational_store.save_material(_normalize_material(updated)), None


def create_recommendation_for_material(sku_id: str = SKU) -> tuple[dict | None, str | None]:
    material = operational_store.get_material(sku_id)
    if not material:
        return None, "not_found"
    if material["risk_status"] == "normal":
        return None, "no_risk"
    recommendation = create_inventory_risk_recommendation(
        material=material,
        correlation_id=str(uuid4()),
        source_event_id=f"INV-{sku_id}",
    )
    return recommendation, None


def _normalize_material(material: dict) -> dict:
    return {
        "sku_id": material["sku_id"],
        "name": material["name"].strip(),
        "line_id": material["line_id"].strip(),
        "warehouse": material["warehouse"].strip(),
        "current_stock_units": int(material["current_stock_units"]),
        "reorder_point_units": int(material["reorder_point_units"]),
        "daily_demand_units": float(material["daily_demand_units"]),
        "unit_cost_mxn": round(float(material["unit_cost_mxn"]), 2),
        "criticality": material["criticality"],
        "active": True,
    }
