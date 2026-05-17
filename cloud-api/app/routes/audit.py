from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from auth.middleware import require_role
from services.audit_service import export_audit_records, list_audit_records

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("/")
def audit(
    entity_type: str | None = None,
    entity_id: str | None = None,
    sku_id: str | None = None,
    correlation_id: str | None = None,
    limit: int = 100,
    current_user: dict = require_role("pa", "supervisor", "admin"),
):
    if entity_type and entity_type not in ("recommendation", "purchase_order", "event"):
        raise HTTPException(status_code=400, detail="Invalid entity_type")
    return {
        "audit": list_audit_records(
            entity_type=entity_type,
            entity_id=entity_id,
            sku_id=sku_id,
            correlation_id=correlation_id,
            limit=limit,
        )
    }


@router.get("/export")
def audit_export(
    format: str = "json",
    entity_type: str | None = None,
    entity_id: str | None = None,
    sku_id: str | None = None,
    correlation_id: str | None = None,
    limit: int = 500,
    current_user: dict = require_role("supervisor", "admin"),
):
    if format not in ("json", "csv"):
        raise HTTPException(status_code=400, detail="Format must be json or csv")
    content, media_type = export_audit_records(
        export_format=format,
        entity_type=entity_type,
        entity_id=entity_id,
        sku_id=sku_id,
        correlation_id=correlation_id,
        limit=limit,
    )
    extension = "csv" if format == "csv" else "json"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="audit.{extension}"'},
    )
