import random
from config import RISK_THRESHOLD, WINDOW_SIZE


def run_local_material_risk_inference(signals: dict) -> dict:
    """Heurística ML ligera tipo Isolation Forest para demo edge."""
    stockout_h = signals.get("stockout_hours", 48.0)
    oee = signals.get("oee", 0.78)
    consumption_rate = signals.get("consumption_rate", 12.5)
    idle_risk = signals.get("idle_risk", False)
    cycle_time = signals.get("cycle_time", 5.0)

    # Score compuesto normalizado 0-1
    stockout_score = max(0.0, min(1.0, (72 - stockout_h) / 72))
    oee_score = max(0.0, 1.0 - oee)
    consumption_score = max(0.0, min(1.0, abs(consumption_rate - 12.5) / 12.5))
    idle_score = 1.0 if idle_risk else 0.0
    cycle_score = max(0.0, min(1.0, abs(cycle_time - 5.5) / 5.5))

    noise = random.uniform(0.0, 0.03) if idle_risk and stockout_h < 8 else random.uniform(-0.03, 0.03)
    risk_score = (
        stockout_score * 0.40
        + oee_score * 0.25
        + consumption_score * 0.15
        + idle_score * 0.15
        + cycle_score * 0.05
        + noise
    )
    risk_score = round(max(0.0, min(1.0, risk_score)), 4)
    is_critical = risk_score > RISK_THRESHOLD

    return {
        "risk_score": risk_score,
        "is_critical": is_critical,
        "threshold": RISK_THRESHOLD,
        "model": "heuristic_isolation_forest_v1",
        "inference_ms": random.randint(8, 45),
        "features": {
            "stockout_hours": stockout_h,
            "oee": oee,
            "consumption_rate": consumption_rate,
            "idle_risk": idle_risk,
            "cycle_time": cycle_time,
        },
    }
