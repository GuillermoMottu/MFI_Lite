from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config import SKU
from services.supplier_service import (
    create_supplier,
    delete_supplier,
    get_supplier,
    list_suppliers,
    recommend_supplier,
    update_supplier,
)

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])


class SupplierCreate(BaseModel):
    supplier_id: str | None = None
    name: str = Field(min_length=2)
    sku_ids: list[str] = Field(default_factory=lambda: [SKU])
    lead_time_days: int = Field(gt=0)
    unit_cost_mxn: float = Field(gt=0)
    reliability_score: float = Field(ge=0, le=1)
    minimum_order_quantity: int = Field(gt=0)


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2)
    sku_ids: list[str] | None = None
    lead_time_days: int | None = Field(default=None, gt=0)
    unit_cost_mxn: float | None = Field(default=None, gt=0)
    reliability_score: float | None = Field(default=None, ge=0, le=1)
    minimum_order_quantity: int | None = Field(default=None, gt=0)


@router.get("/")
def suppliers(sku_id: str | None = None):
    return {"suppliers": list_suppliers(sku_id=sku_id)}


@router.get("/recommended")
def recommended_supplier(sku_id: str = SKU, strategy: str = "urgency"):
    if strategy not in ("urgency", "cost"):
        raise HTTPException(status_code=400, detail="Strategy must be urgency or cost")
    supplier = recommend_supplier(sku_id=sku_id, strategy=strategy)
    if not supplier:
        raise HTTPException(status_code=404, detail="No active supplier found for this SKU")
    return {"supplier": supplier}


@router.get("/{supplier_id}")
def supplier(supplier_id: str):
    found = get_supplier(supplier_id)
    if not found:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"supplier": found}


@router.post("/")
def create(request: SupplierCreate):
    supplier, error = create_supplier(request.model_dump())
    if error == "duplicate":
        raise HTTPException(status_code=409, detail="Supplier already exists")
    return {"supplier": supplier}


@router.patch("/{supplier_id}")
def update(supplier_id: str, request: SupplierUpdate):
    supplier, error = update_supplier(
        supplier_id,
        request.model_dump(exclude_unset=True),
    )
    if error == "not_found":
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"supplier": supplier}


@router.delete("/{supplier_id}")
def delete(supplier_id: str):
    if not delete_supplier(supplier_id):
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"status": "deleted", "supplier_id": supplier_id}
