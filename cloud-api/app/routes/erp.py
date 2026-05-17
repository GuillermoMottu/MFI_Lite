from fastapi import APIRouter
from agents.erp_agent import ERPAgent
from config import SKU
import state as app_state

router = APIRouter(prefix="/api/erp", tags=["ERP"])
_agent = ERPAgent()


@router.post("/predict-demand")
def predict_demand(sku_id: str = SKU):
    event, data = _agent.predict_demand(sku_id=sku_id)
    return {"event": event.model_dump(), "result": data}


@router.post("/optimize-stock-levels")
def optimize_stock_levels(sku_id: str = SKU):
    event, data = _agent.optimize_stock_levels(sku_id=sku_id)
    return {"event": event.model_dump() if event else None, "result": data}


@router.post("/generate-purchase-order")
def generate_purchase_order(sku_id: str = SKU):
    event, data = _agent.generate_purchase_order(sku_id=sku_id)
    return {"event": event.model_dump(), "result": data}


@router.post("/sync-erp-data")
def sync_erp_data(sku_id: str = SKU):
    event, data = _agent.sync_erp_data_local(sku_id=sku_id)
    return {"event": event.model_dump(), "result": data}


@router.get("/stock-history")
def stock_history():
    """Histórico de stock con timestamps para graficar evolución temporal."""
    return {
        "history": app_state.state.get("stock_history", []),
        "current_stock": app_state.state["current_stock"],
        "reorder_point": app_state.state["reorder_point"],
    }


@router.get("/status")
def erp_status():
    return {
        "agent": "erp_gestion_empresarial",
        "current_stock_units": app_state.state["current_stock"],
        "daily_demand_units": app_state.state["daily_demand"],
        "reorder_point_units": app_state.state["reorder_point"],
        "purchase_orders": app_state.state["purchase_orders"],
    }
