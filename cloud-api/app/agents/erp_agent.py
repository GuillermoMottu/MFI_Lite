import random
from datetime import datetime, timezone
from uuid import uuid4
from services.event_factory import create_ies_event
from services.event_bus import publish
from models.ies_event import IESEvent
from config import (
    SKU, MODULE_ERP, DAILY_DEMAND_MIN, DAILY_DEMAND_MAX,
    LEAD_TIME_DAYS_MIN, LEAD_TIME_DAYS_MAX, SAFETY_STOCK_FACTOR,
    UNIT_COST_MXN_MIN, UNIT_COST_MXN_MAX, LINE_ID, WAREHOUSE
)
import state as app_state


class ERPAgent:

    def predict_demand(
        self, sku_id: str = SKU, horizon_days: int = 7, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        avg = float(random.randint(DAILY_DEMAND_MIN, DAILY_DEMAND_MAX))
        factor = round(random.uniform(1.0, 1.25), 2)
        predicted = round(avg * horizon_days * factor)

        app_state.state["daily_demand"] = avg

        data = {
            "sku_id": sku_id,
            "avg_daily_consumption_units": avg,
            "horizon_days": horizon_days,
            "demand_factor": factor,
            "predicted_units": predicted,
            "confidence": 0.84,
        }
        event = create_ies_event(
            module_id=MODULE_ERP, module_version="1.0.0",
            event_type="material_demand_forecasted",
            category="productivity", severity="medium",
            asset_id=sku_id, asset_type="material",
            data=data, correlation_id=correlation_id,
            related_assets=[sku_id, LINE_ID, WAREHOUSE],
        )
        publish(event)
        return event, data

    def optimize_stock_levels(
        self, sku_id: str = SKU, correlation_id: str | None = None
    ) -> tuple[IESEvent | None, dict]:
        daily_demand = app_state.state["daily_demand"]
        current_stock = app_state.state["current_stock"]
        lead = random.randint(LEAD_TIME_DAYS_MIN, LEAD_TIME_DAYS_MAX)
        safety = round(daily_demand * SAFETY_STOCK_FACTOR)
        reorder = round(daily_demand * lead + safety)
        stockout_h = round(current_stock / (daily_demand / 24), 2)

        app_state.state["reorder_point"] = reorder

        risk = current_stock < reorder
        severity = "critical" if stockout_h < 24 else "high" if risk else "low"

        data = {
            "sku_id": sku_id,
            "daily_demand_units": daily_demand,
            "lead_time_days": lead,
            "safety_stock_units": safety,
            "current_stock_units": current_stock,
            "reorder_point_units": reorder,
            "estimated_stockout_hours": stockout_h,
            "risk_detected": risk,
        }

        if risk:
            event = create_ies_event(
                module_id=MODULE_ERP, module_version="1.0.0",
                event_type="stock_risk_detected",
                category="productivity", severity=severity,
                asset_id=sku_id, asset_type="material",
                data=data, correlation_id=correlation_id,
                related_assets=[sku_id, LINE_ID, WAREHOUSE],
            )
            publish(event)
            return event, data

        return None, data

    def generate_purchase_order(
        self, sku_id: str = SKU, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        current_stock = app_state.state["current_stock"]
        daily_demand = app_state.state["daily_demand"]
        reorder = app_state.state["reorder_point"] or round(daily_demand * 3)
        unit_cost = round(random.uniform(UNIT_COST_MXN_MIN, UNIT_COST_MXN_MAX), 2)
        qty = round(daily_demand * 7)
        total_mxn = round(qty * unit_cost, 2)
        po_id = f"PO-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:4].upper()}"

        providers = [
            {"name": "ProveeMetal SA", "lead_time_days": 2, "price_mxn": unit_cost},
            {"name": "Aceros del Norte", "lead_time_days": 4, "price_mxn": unit_cost * 0.95},
        ]
        selected = min(providers, key=lambda p: p["lead_time_days"])

        data = {
            "purchase_order_id": po_id,
            "sku_id": sku_id,
            "quantity_units": qty,
            "unit_cost_mxn": unit_cost,
            "total_cost_mxn": total_mxn,
            "provider": selected["name"],
            "provider_lead_time_days": selected["lead_time_days"],
            "current_stock_units": current_stock,
            "reorder_point_units": reorder,
            "urgency": "critical",
            "trigger": "stock_risk_detected",
        }
        app_state.state["purchase_orders"].append(po_id)

        event = create_ies_event(
            module_id=MODULE_ERP, module_version="1.0.0",
            event_type="urgent_purchase_order_created",
            category="productivity", severity="critical",
            asset_id=sku_id, asset_type="material",
            data=data, correlation_id=correlation_id,
            related_assets=[sku_id, LINE_ID, WAREHOUSE],
        )
        publish(event)
        return event, data

    def sync_erp_data_local(
        self, sku_id: str = SKU, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        synced_records = random.randint(12, 48)
        conflicts = random.randint(0, 3)
        data = {
            "sku_id": sku_id,
            "synced_records": synced_records,
            "conflicts_resolved": conflicts,
            "sync_type": "incremental",
            "resolution_strategy": "latest_updated_at_wins",
            "sync_duration_ms": random.randint(120, 850),
        }
        event = create_ies_event(
            module_id=MODULE_ERP, module_version="1.0.0",
            event_type="erp_inventory_synced",
            category="productivity", severity="low",
            asset_id=sku_id, asset_type="material",
            data=data, correlation_id=correlation_id,
            related_assets=[sku_id, WAREHOUSE],
        )
        publish(event)
        return event, data
