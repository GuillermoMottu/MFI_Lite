from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from auth.middleware import require_role
from services.purchase_order_service import (
    approve_purchase_order,
    get_purchase_order,
    list_purchase_orders,
    list_suppliers,
    update_purchase_order,
)

router = APIRouter(prefix="/api/purchase-orders", tags=["Purchase Orders"])


class PurchaseOrderUpdate(BaseModel):
    supplier_id: str | None = None
    quantity_units: int | None = None
    required_date: str | None = None
    comment: str | None = None


class PurchaseOrderApproval(BaseModel):
    user: str = "PA-OPERADOR"
    comment: str | None = None


@router.get("/")
def purchase_orders(status: str | None = None, current_user: dict = require_role("pa", "supervisor", "admin")):
    return {"purchase_orders": list_purchase_orders(status=status)}


@router.get("/suppliers")
def suppliers(sku_id: str = "SKU-ACERO-M8", current_user: dict = require_role("pa", "supervisor", "admin")):
    return {"suppliers": list_suppliers(sku_id)}


@router.get("/{po_id}")
def purchase_order(po_id: str, current_user: dict = require_role("pa", "supervisor", "admin")):
    order = get_purchase_order(po_id)
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return {"purchase_order": order}


@router.patch("/{po_id}")
def update(
    po_id: str,
    request: PurchaseOrderUpdate,
    current_user: dict = require_role("pa", "admin"),
):
    order, error = update_purchase_order(
        po_id=po_id,
        supplier_id=request.supplier_id,
        quantity_units=request.quantity_units,
        required_date=request.required_date,
        comment=request.comment,
    )
    if error == "not_found":
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if error == "locked_status":
        raise HTTPException(status_code=409, detail="Purchase order cannot be edited in its current status")
    if error == "supplier_not_found":
        raise HTTPException(status_code=400, detail="Supplier is not valid for this SKU")
    if error == "invalid_quantity":
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
    return {"purchase_order": order}


@router.post("/{po_id}/approve")
def approve(
    po_id: str,
    request: PurchaseOrderApproval | None = None,
    current_user: dict = require_role("pa", "admin"),
):
    request = request or PurchaseOrderApproval()
    order, error = approve_purchase_order(
        po_id=po_id,
        approved_by=current_user["display_name"],
        comment=request.comment,
    )
    if error == "not_found":
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if error == "locked_status":
        raise HTTPException(status_code=409, detail="Purchase order cannot be approved in its current status")
    if error == "missing_supplier":
        raise HTTPException(status_code=400, detail="Supplier is required")
    if error == "invalid_quantity":
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
    return {"purchase_order": order}
