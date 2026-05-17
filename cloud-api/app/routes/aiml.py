from datetime import datetime, timezone
from fastapi import APIRouter
from agents.aiml_agent import AIMLAgent
from edge.aiml_edge_tools import (
    collect_material_signals,
    run_edge_inference_and_buffer,
    trigger_local_recommendation,
)
from edge.local_inference import run_local_material_risk_inference
import state as app_state

router = APIRouter(prefix="/api/aiml", tags=["AI/ML"])
_agent = AIMLAgent()


@router.post("/detect-deviation")
def detect_deviation():
    event, data = _agent.detect_process_deviation()
    return {"event": event.model_dump(), "result": data}


@router.post("/identify-bottlenecks")
def identify_bottlenecks():
    event, data = _agent.identify_bottlenecks()
    return {"event": event.model_dump() if event else None, "result": data}


@router.post("/digital-twin")
def digital_twin():
    event, data = _agent.generate_digital_twin_model()
    return {"event": event.model_dump(), "result": data}


@router.post("/train-model")
def train_model():
    event, data = _agent.train_material_risk_model()
    return {"event": event.model_dump(), "result": data}


@router.post("/predict-rul")
def predict_rul():
    event, data = _agent.predict_remaining_useful_life()
    return {"event": event.model_dump(), "result": data}


@router.post("/classify-anomaly")
def classify_anomaly():
    event, data = _agent.classify_anomaly_type()
    return {"event": event.model_dump(), "result": data}


@router.post("/maintenance-recommendation")
def maintenance_recommendation():
    event, data = _agent.generate_maintenance_recommendation()
    return {"event": event.model_dump(), "result": data}


@router.post("/forecast-oee")
def forecast_oee():
    event, data = _agent.forecast_oee_degradation()
    return {"event": event.model_dump(), "result": data}


@router.get("/signals")
def get_signals():
    return collect_material_signals()


@router.post("/edge-inference")
def edge_inference():
    result = run_edge_inference_and_buffer()
    if result.get("inference"):
        app_state.state["last_inference"] = result["inference"]
    return result


@router.get("/inference-status")
def inference_status():
    """Última inferencia Edge con señales, risk_score, threshold y severity."""
    signals = collect_material_signals()
    inference = run_local_material_risk_inference(signals)
    app_state.state["last_inference"] = inference
    severity = (
        "critical" if inference["risk_score"] > 0.85
        else "high" if inference["risk_score"] > inference["threshold"]
        else "medium" if inference["risk_score"] > 0.5
        else "low"
    )
    return {
        "signals": signals,
        "risk_score": inference["risk_score"],
        "threshold": inference["threshold"],
        "is_critical": inference["is_critical"],
        "severity": severity,
        "model": inference["model"],
        "inference_ms": inference["inference_ms"],
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@router.get("/status")
def aiml_status():
    return {
        "agent": "ai_ml_industrial",
        "risk_score_pct": app_state.state["risk_score"],
        "last_bottleneck": app_state.state["last_bottleneck"],
        "loss_prevented_mxn": app_state.state["loss_prevented_mxn"],
    }
