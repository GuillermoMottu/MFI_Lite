import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from services.event_bus import list_events, subscribe, unsubscribe
from services.correlation_engine import get_correlated_events

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.get("/")
def get_events(
    limit: int = 50,
    module_id: str | None = None,
    asset_id: str | None = None,
    event_type: str | None = None,
    correlation_id: str | None = None,
):
    return list_events(
        limit=limit,
        module_id=module_id,
        asset_id=asset_id,
        event_type=event_type,
        correlation_id=correlation_id,
    )


@router.get("/chain")
def get_event_chain(correlation_id: str):
    """Devuelve todos los eventos vinculados a un correlation_id, ordenados por timestamp."""
    events = get_correlated_events(correlation_id)
    return {"correlation_id": correlation_id, "count": len(events), "events": events}


@router.get("/stream")
async def event_stream():
    q = subscribe()

    async def generator():
        try:
            # Enviar ping inicial
            yield "data: {\"type\":\"connected\"}\n\n"
            while True:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield payload
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            unsubscribe(q)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
