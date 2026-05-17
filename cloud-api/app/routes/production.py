from fastapi import APIRouter
from agents.production_agent import ProductionAgent
from fastapi import HTTPException
from pydantic import BaseModel
from edge.production_edge_tools import (
    collect_production_data,
    detect_material_related_idle_time,
    monitor_material_consumption_rate,
)
from services.production_backlog_service import (
    apply_resequence,
    impacted_jobs,
    list_backlog,
    suggest_resequence,
    update_job,
)
import state as app_state

router = APIRouter(prefix="/api/production", tags=["Production"])
_agent = ProductionAgent()


class ResequenceRequest(BaseModel):
    user: str = "PA-OPERADOR"
    comment: str | None = None


class JobUpdate(BaseModel):
    priority: int | None = None
    sequence: int | None = None
    status: str | None = None
    required_start: str | None = None


@router.post("/plan-automatically")
def plan_production():
    event, data = _agent.plan_production_automatically()
    return {"event": event.model_dump(), "result": data}


@router.post("/optimize-flow")
def optimize_flow():
    event, data = _agent.optimize_production_flow()
    return {"event": event.model_dump(), "result": data}


@router.post("/calculate-oee")
def calculate_oee():
    event, data = _agent.calculate_oee_impact()
    return {"event": event.model_dump(), "result": data}


@router.post("/adjust-schedule")
def adjust_schedule():
    event, data = _agent.adjust_production_schedule()
    return {"event": event.model_dump(), "result": data}


@router.post("/simulate-stoppage")
def simulate_stoppage():
    event, data = _agent.simulate_line_stoppage()
    return {"event": event.model_dump(), "result": data}


@router.post("/allocate-materials")
def allocate_materials():
    event, data = _agent.allocate_materials_to_lines()
    return {"event": event.model_dump(), "result": data}


@router.get("/collect-data")
def collect_data():
    return collect_production_data()


@router.post("/detect-idle")
def detect_idle():
    result = detect_material_related_idle_time()
    if result is None:
        return {"risk_detected": False, "message": "No idle risk detected"}
    event, data = result
    return {"event": event.model_dump(), "result": data}


@router.get("/consumption-rate")
def consumption_rate():
    return monitor_material_consumption_rate()


@router.get("/status")
def production_status():
    return {
        "agent": "produccion_avanzada",
        "plan_units": app_state.state["plan_units"],
        "adjusted_plan_units": app_state.state["adjusted_plan_units"],
        "oee_pct": round(app_state.state["oee"] * 100, 2),
        "idle_minutes_prevented": app_state.state["idle_minutes_prevented"],
    }


@router.get("/backlog")
def backlog(status: str | None = None):
    return {"jobs": list_backlog(status=status)}


@router.get("/backlog/impacted")
def backlog_impacted():
    return {"jobs": impacted_jobs()}


@router.get("/backlog/suggestion")
def backlog_suggestion():
    return suggest_resequence()


@router.post("/backlog/resequence")
def resequence_backlog(request: ResequenceRequest | None = None):
    request = request or ResequenceRequest()
    result, event = apply_resequence(user=request.user, comment=request.comment)
    return {"result": result, "event": event}


@router.patch("/backlog/{job_id}")
def update_backlog_job(job_id: str, request: JobUpdate):
    job, error = update_job(job_id, request.model_dump(exclude_unset=True))
    if error == "not_found":
        raise HTTPException(status_code=404, detail="Production job not found")
    return {"job": job}
