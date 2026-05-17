import re

from config import SKU
from services import operational_store


def list_suppliers(sku_id: str | None = None) -> list[dict]:
    return operational_store.list_suppliers(sku_id=sku_id)


def get_supplier(supplier_id: str) -> dict | None:
    return operational_store.get_supplier(supplier_id)


def create_supplier(payload: dict) -> tuple[dict | None, str | None]:
    supplier = _normalize_supplier(payload)
    if operational_store.get_supplier(supplier["supplier_id"]):
        return None, "duplicate"
    return operational_store.save_supplier(supplier), None


def update_supplier(supplier_id: str, payload: dict) -> tuple[dict | None, str | None]:
    current = operational_store.get_supplier(supplier_id)
    if not current:
        return None, "not_found"
    updated = {
        **current,
        **{key: value for key, value in payload.items() if value is not None},
        "supplier_id": supplier_id,
    }
    supplier = _normalize_supplier(updated, keep_id=True)
    return operational_store.save_supplier(supplier), None


def delete_supplier(supplier_id: str) -> bool:
    return operational_store.deactivate_supplier(supplier_id)


def recommend_supplier(sku_id: str = SKU, strategy: str = "urgency") -> dict | None:
    suppliers = operational_store.list_suppliers(sku_id=sku_id)
    if not suppliers:
        return None

    scored = [
        {
            **supplier,
            "selection_score": _selection_score(supplier, strategy),
            "selection_reason": _selection_reason(strategy),
        }
        for supplier in suppliers
    ]
    if strategy == "cost":
        return sorted(scored, key=lambda supplier: (supplier["unit_cost_mxn"], -supplier["reliability_score"]))[0]
    return sorted(scored, key=lambda supplier: (supplier["lead_time_days"], -supplier["reliability_score"]))[0]


def _normalize_supplier(payload: dict, keep_id: bool = False) -> dict:
    supplier_id = payload.get("supplier_id") if keep_id else payload.get("supplier_id") or _supplier_id(payload["name"])
    return {
        "supplier_id": supplier_id,
        "name": payload["name"].strip(),
        "sku_ids": payload.get("sku_ids") or [SKU],
        "lead_time_days": int(payload["lead_time_days"]),
        "unit_cost_mxn": round(float(payload["unit_cost_mxn"]), 2),
        "reliability_score": round(float(payload["reliability_score"]), 3),
        "minimum_order_quantity": int(payload["minimum_order_quantity"]),
        "active": True,
    }


def _supplier_id(name: str) -> str:
    slug = re.sub(r"[^A-Z0-9]+", "-", name.upper()).strip("-")
    return f"SUP-{slug[:32]}" if slug else "SUP-NUEVO"


def _selection_score(supplier: dict, strategy: str) -> float:
    if strategy == "cost":
        return round((1000 / max(supplier["unit_cost_mxn"], 1)) + supplier["reliability_score"], 3)
    return round((100 / max(supplier["lead_time_days"], 1)) + supplier["reliability_score"], 3)


def _selection_reason(strategy: str) -> str:
    if strategy == "cost":
        return "Mejor balance para reducir costo manteniendo confiabilidad aceptable."
    return "Mejor balance para urgencia: menor lead time con confiabilidad alta."
