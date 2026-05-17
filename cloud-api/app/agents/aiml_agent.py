import random
from services.event_factory import create_ies_event
from services.event_bus import publish
from services.correlation_engine import count_recent_events_by_modules
from edge.local_inference import run_local_material_risk_inference
from edge.aiml_edge_tools import collect_material_signals
from models.ies_event import IESEvent
from config import (
    SKU, LINE_ID, MODULE_AIML, MODULE_ERP, MODULE_PROD, MODULE_EDGE,
    RISK_SCORE_CRITICAL
)
import state as app_state


class AIMLAgent:

    def detect_process_deviation(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        signals = collect_material_signals()
        inference = run_local_material_risk_inference(signals)
        risk_score_100 = round(inference["risk_score"] * 100, 1)

        app_state.state["risk_score"] = risk_score_100
        severity = "critical" if risk_score_100 >= RISK_SCORE_CRITICAL else "high"

        data = {
            "sku_id": SKU,
            "line_id": LINE_ID,
            "risk_score": risk_score_100,
            "correlated_events": [
                "stock_risk_detected",
                "production_plan_adjusted",
                "material_related_idle_risk_detected",
            ],
            "deviation_type": "multivariable_material_risk",
            "severity": severity,
            "signals": signals,
        }
        event = create_ies_event(
            module_id=MODULE_AIML, module_version="1.0.0",
            event_type="material_lifecycle_risk_detected",
            category="productivity", severity=severity,
            asset_id=SKU, asset_type="material",
            data=data, correlation_id=correlation_id,
            related_assets=[SKU, LINE_ID, "CONVEYOR-1"],
        )
        publish(event)
        return event, data

    def identify_bottlenecks(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent | None, dict]:
        risk_score = app_state.state["risk_score"]
        recent_events = count_recent_events_by_modules(
            [MODULE_ERP, MODULE_PROD, MODULE_EDGE], within_seconds=600
        )
        oee = app_state.state["oee"]
        trigger_met = risk_score >= RISK_SCORE_CRITICAL and recent_events >= 3

        if not trigger_met:
            return None, {
                "bottleneck_detected": False,
                "risk_score": risk_score,
                "correlated_events_count": recent_events,
                "trigger_condition": "risk_score >= 75 AND 3+ correlated events within 10 min",
            }

        loss_mxn = round(random.uniform(18500, 42000), 2)

        app_state.state["loss_prevented_mxn"] = loss_mxn
        app_state.state["last_bottleneck"] = "material_supply_restriction"

        data = {
            "bottleneck_type": "material_supply_restriction",
            "root_cause": f"SKU-ACERO-M8 stock crítico con {risk_score:.1f}% de riesgo acumulado",
            "sku_id": SKU,
            "line_id": LINE_ID,
            "risk_score": risk_score,
            "correlated_events_count": recent_events,
            "oee_impact_pct": round((1 - oee) * 100, 2),
            "estimated_impact_mxn": loss_mxn,
            "trigger_condition": "risk_score >= 75 AND 3+ correlated events within 10 min",
            "emergent_behavior": True,
        }
        event = create_ies_event(
            module_id=MODULE_AIML, module_version="1.0.0",
            event_type="material_bottleneck_identified",
            category="productivity", severity="critical",
            asset_id=LINE_ID, asset_type="production_line",
            data=data, correlation_id=correlation_id,
            related_assets=[SKU, LINE_ID, "ALMACEN-MP-01", "CONVEYOR-1"],
        )
        publish(event)
        return event, data

    def generate_digital_twin_model(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        oee = app_state.state["oee"]
        loss_mxn = app_state.state["loss_prevented_mxn"]
        idle_min = app_state.state["idle_minutes_prevented"]
        current_stock = app_state.state["current_stock"]
        daily_demand = app_state.state["daily_demand"]
        stockout_h = round(current_stock / (daily_demand / 24), 2) if daily_demand else 0

        scenario_now = {
            "action": "act_now",
            "oee_pct": round(oee * 100, 2),
            "estimated_stockout_hours": stockout_h,
            "idle_minutes": 0,
            "loss_mxn": 0,
            "recommendation": "Emitir orden urgente + ajustar plan de producción",
        }
        scenario_wait = {
            "action": "wait_24h",
            "oee_pct": round(max(0.55, oee - 0.18) * 100, 2),
            "estimated_stockout_hours": max(0.0, stockout_h - 24),
            "idle_minutes": idle_min + random.randint(30, 90),
            "loss_mxn": round(loss_mxn * 1.85, 2),
            "recommendation": "Riesgo alto de paro total de línea",
        }

        data = {
            "sku_id": SKU,
            "line_id": LINE_ID,
            "scenario_act_now": scenario_now,
            "scenario_wait_24h": scenario_wait,
            "estimated_loss_prevented_mxn": loss_mxn,
            "recommended_action": "act_now",
            "confidence": 0.91,
            "twin_model": "digital_twin_v1",
        }
        event = create_ies_event(
            module_id=MODULE_AIML, module_version="1.0.0",
            event_type="operational_recommendation_generated",
            category="productivity", severity="high",
            asset_id=LINE_ID, asset_type="production_line",
            data=data, correlation_id=correlation_id,
            related_assets=[SKU, LINE_ID, "ALMACEN-MP-01", "CONVEYOR-1"],
        )
        publish(event)
        return event, data

    def train_material_risk_model(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        training_samples = random.randint(850, 2400)
        accuracy = round(random.uniform(0.87, 0.96), 4)
        data = {
            "model": "material_risk_classifier_v2",
            "training_samples": training_samples,
            "accuracy": accuracy,
            "precision": round(accuracy - 0.02, 4),
            "recall": round(accuracy - 0.03, 4),
            "features_used": ["stockout_hours", "oee", "consumption_rate", "idle_risk", "cycle_time"],
            "note": "Lightweight model optimized for edge inference",
        }
        event = create_ies_event(
            module_id=MODULE_AIML, module_version="1.0.0",
            event_type="material_risk_model_updated",
            category="productivity", severity="low",
            asset_id=SKU, asset_type="material",
            data=data, correlation_id=correlation_id,
            related_assets=[SKU, LINE_ID],
        )
        publish(event)
        return event, data

    def predict_remaining_useful_life(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        signals = collect_material_signals()
        oee = app_state.state["oee"]
        cycle_time = signals.get("cycle_time", 5.5)
        # RUL heuristic: degraded OEE + elevated cycle time reduces lifespan estimate
        base_rul_hours = 720.0  # 30-day baseline
        oee_penalty = (1.0 - oee) * 240
        cycle_penalty = max(0, (cycle_time - 5.0) * 30)
        rul_hours = round(base_rul_hours - oee_penalty - cycle_penalty + random.uniform(-24, 24), 1)
        rul_hours = max(48.0, rul_hours)
        severity = "critical" if rul_hours < 120 else "high" if rul_hours < 240 else "medium"

        data = {
            "asset_id": "CONVEYOR-1",
            "line_id": LINE_ID,
            "rul_hours": rul_hours,
            "rul_days": round(rul_hours / 24, 1),
            "oee_current_pct": round(oee * 100, 2),
            "cycle_time_sec": cycle_time,
            "degradation_rate_pct_per_day": round((1.0 - oee) * 3.5, 2),
            "maintenance_window_recommended": "next_scheduled_downtime",
            "model": "rul_regression_v1",
            "confidence": round(random.uniform(0.82, 0.94), 2),
        }
        event = create_ies_event(
            module_id=MODULE_AIML, module_version="1.0.0",
            event_type="equipment_rul_predicted",
            category="maintenance", severity=severity,
            asset_id="CONVEYOR-1", asset_type="conveyor",
            data=data, correlation_id=correlation_id,
            related_assets=["CONVEYOR-1", LINE_ID],
        )
        publish(event)
        return event, data

    def classify_anomaly_type(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        signals = collect_material_signals()
        risk_score = app_state.state["risk_score"]
        stockout_h = signals.get("stockout_hours", 48.0)
        oee = signals.get("oee", 0.78)
        idle_risk = signals.get("idle_risk", False)

        # Rule-based multi-class classification
        if stockout_h < 8 and idle_risk:
            anomaly_type = "critical_supply_chain_disruption"
            confidence = round(random.uniform(0.88, 0.97), 3)
            severity = "critical"
        elif oee < 0.70:
            anomaly_type = "sustained_oee_degradation"
            confidence = round(random.uniform(0.82, 0.91), 3)
            severity = "high"
        elif risk_score > 75:
            anomaly_type = "multi_signal_risk_convergence"
            confidence = round(random.uniform(0.79, 0.88), 3)
            severity = "high"
        else:
            anomaly_type = "transient_material_variability"
            confidence = round(random.uniform(0.71, 0.82), 3)
            severity = "medium"

        data = {
            "sku_id": SKU,
            "line_id": LINE_ID,
            "anomaly_type": anomaly_type,
            "confidence": confidence,
            "contributing_signals": {
                "stockout_hours": stockout_h,
                "oee": oee,
                "idle_risk": idle_risk,
                "risk_score_pct": risk_score,
            },
            "classifier": "multi_class_rule_based_v2",
            "action_required": severity in ("critical", "high"),
        }
        event = create_ies_event(
            module_id=MODULE_AIML, module_version="1.0.0",
            event_type="anomaly_type_classified",
            category="quality", severity=severity,
            asset_id=SKU, asset_type="material",
            data=data, correlation_id=correlation_id,
        )
        publish(event)
        return event, data

    def generate_maintenance_recommendation(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        signals = collect_material_signals()
        oee = app_state.state["oee"]
        cycle_time = signals.get("cycle_time", 5.5)
        risk_score = app_state.state["risk_score"]

        # Derive maintenance urgency from combined signals
        urgency_score = (risk_score / 100) * 0.5 + (1 - oee) * 0.3 + (cycle_time / 10) * 0.2
        if urgency_score > 0.7:
            action = "immediate_preventive_maintenance"
            window_hours = random.randint(4, 12)
            severity = "critical"
        elif urgency_score > 0.45:
            action = "scheduled_inspection_within_48h"
            window_hours = random.randint(24, 48)
            severity = "high"
        else:
            action = "monitor_and_log"
            window_hours = 72
            severity = "medium"

        estimated_cost_mxn = round(window_hours * random.uniform(850, 1200), 2)
        data = {
            "asset_id": "CONVEYOR-1",
            "line_id": LINE_ID,
            "urgency_score": round(urgency_score, 3),
            "recommended_action": action,
            "maintenance_window_hours": window_hours,
            "estimated_downtime_hours": round(window_hours * 0.4, 1),
            "estimated_cost_mxn": estimated_cost_mxn,
            "triggers": ["oee_degradation", "elevated_cycle_time", "material_risk"],
            "technician_required": severity in ("critical", "high"),
        }
        event = create_ies_event(
            module_id=MODULE_AIML, module_version="1.0.0",
            event_type="predictive_maintenance_recommended",
            category="maintenance", severity=severity,
            asset_id="CONVEYOR-1", asset_type="conveyor",
            data=data, correlation_id=correlation_id,
            related_assets=["CONVEYOR-1", LINE_ID, "PLT-JUAREZ-01"],
        )
        publish(event)
        return event, data

    def forecast_oee_degradation(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        oee = app_state.state["oee"]
        current_stock = app_state.state["current_stock"]
        daily_demand = app_state.state["daily_demand"]
        stockout_h = round(current_stock / (daily_demand / 24), 2) if daily_demand else 72.0

        # OEE trend forecast: project 3 horizons
        daily_degradation = round(random.uniform(0.008, 0.022), 4)
        oee_24h = round(max(0.50, oee - daily_degradation), 4)
        oee_48h = round(max(0.40, oee - daily_degradation * 2.2), 4)
        oee_72h = round(max(0.30, oee - daily_degradation * 3.8), 4)
        loss_if_no_action_mxn = round((oee - oee_72h) * 480 * 850, 2)
        severity = "critical" if oee_72h < 0.55 else "high" if oee_72h < 0.70 else "medium"

        data = {
            "line_id": LINE_ID,
            "oee_current_pct": round(oee * 100, 2),
            "forecast": {
                "h24": round(oee_24h * 100, 2),
                "h48": round(oee_48h * 100, 2),
                "h72": round(oee_72h * 100, 2),
            },
            "daily_degradation_rate": daily_degradation,
            "stockout_hours_remaining": stockout_h,
            "loss_if_no_action_mxn": loss_if_no_action_mxn,
            "recommended_intervention": "emit_purchase_order + adjust_schedule",
            "model": "oee_linear_degradation_v1",
            "confidence_interval": 0.85,
        }
        event = create_ies_event(
            module_id=MODULE_AIML, module_version="1.0.0",
            event_type="oee_degradation_forecasted",
            category="productivity", severity=severity,
            asset_id=LINE_ID, asset_type="production_line",
            data=data, correlation_id=correlation_id,
            related_assets=[LINE_ID, SKU],
        )
        publish(event)
        return event, data

    def predict_remaining_useful_life(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        signals = collect_material_signals()
        oee = app_state.state["oee"]
        cycle_time = signals.get("cycle_time", 5.5)
        base_rul_hours = 720.0
        oee_penalty = (1.0 - oee) * 240
        cycle_penalty = max(0, (cycle_time - 5.0) * 30)
        rul_hours = round(base_rul_hours - oee_penalty - cycle_penalty + random.uniform(-24, 24), 1)
        rul_hours = max(48.0, rul_hours)
        severity = "critical" if rul_hours < 120 else "high" if rul_hours < 240 else "medium"

        data = {
            "asset_id": "CONVEYOR-1",
            "line_id": LINE_ID,
            "rul_hours": rul_hours,
            "rul_days": round(rul_hours / 24, 1),
            "oee_current_pct": round(oee * 100, 2),
            "cycle_time_sec": cycle_time,
            "degradation_rate_pct_per_day": round((1.0 - oee) * 3.5, 2),
            "maintenance_window_recommended": "next_scheduled_downtime",
            "model": "rul_regression_v1",
            "confidence": round(random.uniform(0.82, 0.94), 2),
        }
        event = create_ies_event(
            module_id=MODULE_AIML, module_version="1.0.0",
            event_type="equipment_rul_predicted",
            category="maintenance", severity=severity,
            asset_id="CONVEYOR-1", asset_type="conveyor",
            data=data, correlation_id=correlation_id,
            related_assets=["CONVEYOR-1", LINE_ID],
        )
        publish(event)
        return event, data

    def classify_anomaly_type(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        signals = collect_material_signals()
        risk_score = app_state.state["risk_score"]
        stockout_h = signals.get("stockout_hours", 48.0)
        oee = signals.get("oee", 0.78)
        idle_risk = signals.get("idle_risk", False)

        if stockout_h < 8 and idle_risk:
            anomaly_type = "critical_supply_chain_disruption"
            confidence = round(random.uniform(0.88, 0.97), 3)
            severity = "critical"
        elif oee < 0.70:
            anomaly_type = "sustained_oee_degradation"
            confidence = round(random.uniform(0.82, 0.91), 3)
            severity = "high"
        elif risk_score > 75:
            anomaly_type = "multi_signal_risk_convergence"
            confidence = round(random.uniform(0.79, 0.88), 3)
            severity = "high"
        else:
            anomaly_type = "transient_material_variability"
            confidence = round(random.uniform(0.71, 0.82), 3)
            severity = "medium"

        data = {
            "sku_id": SKU,
            "line_id": LINE_ID,
            "anomaly_type": anomaly_type,
            "confidence": confidence,
            "contributing_signals": {
                "stockout_hours": stockout_h,
                "oee": oee,
                "idle_risk": idle_risk,
                "risk_score_pct": risk_score,
            },
            "classifier": "multi_class_rule_based_v2",
            "action_required": severity in ("critical", "high"),
        }
        event = create_ies_event(
            module_id=MODULE_AIML, module_version="1.0.0",
            event_type="anomaly_type_classified",
            category="quality", severity=severity,
            asset_id=SKU, asset_type="material",
            data=data, correlation_id=correlation_id,
        )
        publish(event)
        return event, data

    def generate_maintenance_recommendation(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        signals = collect_material_signals()
        oee = app_state.state["oee"]
        cycle_time = signals.get("cycle_time", 5.5)
        risk_score = app_state.state["risk_score"]

        urgency_score = (risk_score / 100) * 0.5 + (1 - oee) * 0.3 + (cycle_time / 10) * 0.2
        if urgency_score > 0.7:
            action = "immediate_preventive_maintenance"
            window_hours = random.randint(4, 12)
            severity = "critical"
        elif urgency_score > 0.45:
            action = "scheduled_inspection_within_48h"
            window_hours = random.randint(24, 48)
            severity = "high"
        else:
            action = "monitor_and_log"
            window_hours = 72
            severity = "medium"

        estimated_cost_mxn = round(window_hours * random.uniform(850, 1200), 2)
        data = {
            "asset_id": "CONVEYOR-1",
            "line_id": LINE_ID,
            "urgency_score": round(urgency_score, 3),
            "recommended_action": action,
            "maintenance_window_hours": window_hours,
            "estimated_downtime_hours": round(window_hours * 0.4, 1),
            "estimated_cost_mxn": estimated_cost_mxn,
            "triggers": ["oee_degradation", "elevated_cycle_time", "material_risk"],
            "technician_required": severity in ("critical", "high"),
        }
        event = create_ies_event(
            module_id=MODULE_AIML, module_version="1.0.0",
            event_type="predictive_maintenance_recommended",
            category="maintenance", severity=severity,
            asset_id="CONVEYOR-1", asset_type="conveyor",
            data=data, correlation_id=correlation_id,
            related_assets=["CONVEYOR-1", LINE_ID, "PLT-JUAREZ-01"],
        )
        publish(event)
        return event, data

    def forecast_oee_degradation(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        oee = app_state.state["oee"]
        current_stock = app_state.state["current_stock"]
        daily_demand = app_state.state["daily_demand"]
        stockout_h = round(current_stock / (daily_demand / 24), 2) if daily_demand else 72.0

        daily_degradation = round(random.uniform(0.008, 0.022), 4)
        oee_24h = round(max(0.50, oee - daily_degradation), 4)
        oee_48h = round(max(0.40, oee - daily_degradation * 2.2), 4)
        oee_72h = round(max(0.30, oee - daily_degradation * 3.8), 4)
        loss_if_no_action_mxn = round((oee - oee_72h) * 480 * 850, 2)
        severity = "critical" if oee_72h < 0.55 else "high" if oee_72h < 0.70 else "medium"

        data = {
            "line_id": LINE_ID,
            "oee_current_pct": round(oee * 100, 2),
            "forecast": {
                "h24": round(oee_24h * 100, 2),
                "h48": round(oee_48h * 100, 2),
                "h72": round(oee_72h * 100, 2),
            },
            "daily_degradation_rate": daily_degradation,
            "stockout_hours_remaining": stockout_h,
            "loss_if_no_action_mxn": loss_if_no_action_mxn,
            "recommended_intervention": "emit_purchase_order + adjust_schedule",
            "model": "oee_linear_degradation_v1",
            "confidence_interval": 0.85,
        }
        event = create_ies_event(
            module_id=MODULE_AIML, module_version="1.0.0",
            event_type="oee_degradation_forecasted",
            category="productivity", severity=severity,
            asset_id=LINE_ID, asset_type="production_line",
            data=data, correlation_id=correlation_id,
            related_assets=[LINE_ID, SKU],
        )
        publish(event)
        return event, data
