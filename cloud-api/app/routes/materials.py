from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.material_service import (
    create_recommendation_for_material,
    get_material,
    list_materials,
    update_material,
)

router = APIRouter(prefix="/api/materials", tags=["Materials"])


class MaterialUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2)
    line_id: str | None = None
    warehouse: str | None = None
    current_stock_units: int | None = Field(default=None, ge=0)
    reorder_point_units: int | None = Field(default=None, gt=0)
    daily_demand_units: float | None = Field(default=None, gt=0)
    unit_cost_mxn: float | None = Field(default=None, gt=0)
    criticality: str | None = None


@router.get("/")
def materials(status: str | None = None):
    if status and status not in ("critical", "low_stock", "normal"):
        raise HTTPException(status_code=400, detail="Status must be critical, low_stock or normal")
    return {"materials": list_materials(status=status)}


@router.get("/{sku_id}")
def material(sku_id: str):
    found = get_material(sku_id)
    if not found:
        raise HTTPException(status_code=404, detail="Material not found")
    return {"material": found}


@router.patch("/{sku_id}")
def update(sku_id: str, request: MaterialUpdate):
    material, error = update_material(sku_id, request.model_dump(exclude_unset=True))
    if error == "not_found":
        raise HTTPException(status_code=404, detail="Material not found")
    return {"material": material}


@router.post("/{sku_id}/recommendation")
def create_recommendation(sku_id: str):
    recommendation, error = create_recommendation_for_material(sku_id)
    if error == "not_found":
        raise HTTPException(status_code=404, detail="Material not found")
    if error == "no_risk":
        raise HTTPException(status_code=409, detail="Material is not currently at risk")
    return {"recommendation": recommendation}
