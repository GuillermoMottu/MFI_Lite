from datetime import datetime, timezone
from uuid import uuid4
from models.ies_event import IESEvent
from config import PLATFORM_VERSION, PLANT_ID, LINE_ID, LOCATION


def create_ies_event(
    module_id: str,
    module_version: str,
    event_type: str,
    category: str,
    severity: str,
    asset_id: str,
    asset_type: str,
    data: dict,
    metadata: dict | None = None,
    correlation_id: str | None = None,
    related_assets: list | None = None,
) -> IESEvent:
    meta = metadata or {}
    if correlation_id:
        meta["correlation_id"] = correlation_id
    if related_assets:
        meta["related_assets"] = related_assets

    return IESEvent(
        event_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        platform_version=PLATFORM_VERSION,
        module={"id": module_id, "version": module_version},
        asset={
            "asset_id": asset_id,
            "asset_type": asset_type,
            "plant_id": PLANT_ID,
            "line_id": LINE_ID,
            "location": LOCATION,
        },
        event={"type": event_type, "category": category, "severity": severity},
        data=data,
        metadata=meta,
    )
