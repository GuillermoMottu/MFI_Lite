from services import operational_store


def list_audit_records(
    entity_type: str | None = None,
    entity_id: str | None = None,
    sku_id: str | None = None,
    correlation_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    return operational_store.list_audit_records(
        entity_type=entity_type,
        entity_id=entity_id,
        sku_id=sku_id,
        correlation_id=correlation_id,
        limit=limit,
    )


def export_audit_records(
    export_format: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    sku_id: str | None = None,
    correlation_id: str | None = None,
    limit: int = 500,
) -> tuple[str, str]:
    records = list_audit_records(
        entity_type=entity_type,
        entity_id=entity_id,
        sku_id=sku_id,
        correlation_id=correlation_id,
        limit=limit,
    )
    if export_format == "csv":
        return operational_store.audit_records_to_csv(records), "text/csv"
    return _json_dump(records), "application/json"


def _json_dump(records: list[dict]) -> str:
    import json

    return json.dumps({"audit": records}, indent=2)
