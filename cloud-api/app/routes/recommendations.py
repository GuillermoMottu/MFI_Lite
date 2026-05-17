from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from auth.middleware import require_role
from services.recommendation_service import (
    approve_recommendation,
    get_active_recommendation,
    list_decision_logs,
    list_recommendations,
    reject_recommendation,
)

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


class DecisionRequest(BaseModel):
    user: str = "PA-OPERADOR"
    comment: str | None = None


@router.get("/")
def recommendations(status: str | None = None, current_user: dict = require_role("pa", "supervisor", "admin")):
    return {"recommendations": list_recommendations(status=status)}


@router.get("/active")
def active_recommendation(current_user: dict = require_role("pa", "supervisor", "admin")):
    return {"recommendation": get_active_recommendation()}


@router.get("/decisions")
def decisions(current_user: dict = require_role("pa", "supervisor", "admin")):
    return {"decisions": list_decision_logs()}


@router.post("/{recommendation_id}/approve")
def approve(
    recommendation_id: str,
    request: DecisionRequest | None = None,
    current_user: dict = require_role("pa", "admin"),
):
    request = request or DecisionRequest()
    recommendation, event, error = approve_recommendation(
        recommendation_id=recommendation_id,
        approved_by=current_user["display_name"],
        comment=request.comment,
    )
    if error == "locked_status":
        raise HTTPException(status_code=409, detail="Recommendation already decided")
    if error == "not_found" or not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {
        "recommendation": recommendation,
        "event": event.model_dump() if event else None,
    }


@router.post("/{recommendation_id}/reject")
def reject(
    recommendation_id: str,
    request: DecisionRequest,
    current_user: dict = require_role("pa", "admin"),
):
    recommendation, event, error = reject_recommendation(
        recommendation_id=recommendation_id,
        rejected_by=current_user["display_name"],
        comment=request.comment,
    )
    if error == "comment_required":
        raise HTTPException(status_code=400, detail="Comment is required to reject a recommendation")
    if error == "locked_status":
        raise HTTPException(status_code=409, detail="Recommendation already decided")
    if error == "not_found" or not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {
        "recommendation": recommendation,
        "event": event.model_dump() if event else None,
    }
