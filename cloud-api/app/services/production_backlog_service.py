from uuid import uuid4

from config import MODULE_PROD, WAREHOUSE
from services import operational_store
from services.event_bus import publish
from services.event_factory import create_ies_event


def list_backlog(status: str | None = None) -> list[dict]:
    return operational_store.list_production_jobs(status=status)


def impacted_jobs() -> list[dict]:
    return [
        job for job in operational_store.list_production_jobs()
        if job["material_risk_status"] in ("critical", "low_stock")
    ]


def suggest_resequence() -> dict:
    jobs = operational_store.list_production_jobs()
    normal = [job for job in jobs if job["material_risk_status"] == "normal"]
    low_stock = [job for job in jobs if job["material_risk_status"] == "low_stock"]
    critical = [job for job in jobs if job["material_risk_status"] == "critical"]
    suggested = normal + low_stock + critical
    return {
        "strategy": "material_availability_first",
        "summary": {
            "jobs_total": len(jobs),
            "jobs_impacted": len(low_stock) + len(critical),
            "critical_jobs": len(critical),
        },
        "suggested_sequence": [
            {
                "job_id": job["job_id"],
                "from_sequence": job["sequence"],
                "to_sequence": index + 1,
                "sku_id": job["sku_id"],
                "material_risk_status": job["material_risk_status"],
                "suggested_action": job["suggested_action"],
            }
            for index, job in enumerate(suggested)
        ],
    }


def apply_resequence(user: str = "PA-OPERADOR", comment: str | None = None) -> tuple[dict, dict]:
    plan = suggest_resequence()
    jobs_by_id = {job["job_id"]: job for job in operational_store.list_production_jobs()}
    updated_jobs = []

    for item in plan["suggested_sequence"]:
        job = jobs_by_id[item["job_id"]]
        job["sequence"] = item["to_sequence"]
        if job["material_risk_status"] == "critical":
            job["status"] = "material_hold"
            job["priority"] = max(job["priority"], 5)
        elif job["material_risk_status"] == "low_stock":
            job["status"] = "scheduled"
            job["priority"] = max(job["priority"], 3)
        else:
            job["status"] = "scheduled"
            job["priority"] = min(job["priority"], 2)
        updated_jobs.append(job)

    updated = operational_store.update_production_jobs(updated_jobs)
    event = _publish_resequence_event(plan, updated, user, comment)
    return {"plan": plan, "jobs": updated}, event.model_dump()


def update_job(job_id: str, payload: dict) -> tuple[dict | None, str | None]:
    job = operational_store.get_production_job(job_id)
    if not job:
        return None, "not_found"
    for field in ("priority", "sequence", "status", "required_start"):
        if field in payload and payload[field] is not None:
            job[field] = payload[field]
    return operational_store.update_production_job(job), None


def _publish_resequence_event(plan: dict, jobs: list[dict], user: str, comment: str | None):
    data = {
        "strategy": plan["strategy"],
        "jobs_total": plan["summary"]["jobs_total"],
        "jobs_impacted": plan["summary"]["jobs_impacted"],
        "critical_jobs": plan["summary"]["critical_jobs"],
        "applied_by": user,
        "comment": comment,
        "updated_jobs": [
            {
                "job_id": job["job_id"],
                "sku_id": job["sku_id"],
                "sequence": job["sequence"],
                "priority": job["priority"],
                "status": job["status"],
                "material_risk_status": job["material_risk_status"],
            }
            for job in jobs
        ],
    }
    event = create_ies_event(
        module_id=MODULE_PROD,
        module_version="1.0.0",
        event_type="production_backlog_resequenced",
        category="productivity",
        severity="high" if plan["summary"]["critical_jobs"] else "medium",
        asset_id="PRODUCTION-BACKLOG",
        asset_type="production_backlog",
        data=data,
        correlation_id=str(uuid4()),
        related_assets=[job["job_id"] for job in jobs] + [WAREHOUSE],
    )
    publish(event)
    return event
