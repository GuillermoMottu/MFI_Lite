import random
from services.event_factory import create_ies_event
from services.event_bus import publish
from models.ies_event import IESEvent
from config import (
    LINE_ID, LOCATION, MODULE_PROD, PLAN_ORIGINAL_UNITS,
    OEE_BASE, AVAILABILITY_BASE, PERFORMANCE_BASE, QUALITY_BASE
)
import state as app_state


class ProductionAgent:

    def plan_production_automatically(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        current_stock = app_state.state["current_stock"]
        daily_demand = app_state.state["daily_demand"]
        reorder = app_state.state["reorder_point"] or round(daily_demand * 3)

        shortage_ratio = max(0.0, 1.0 - (current_stock / reorder)) if reorder else 0.0
        reduction_pct = round(shortage_ratio * 0.35, 3)
        adjusted = round(PLAN_ORIGINAL_UNITS * (1 - reduction_pct))
        idle_prevented = random.randint(15, 45)

        app_state.state["adjusted_plan_units"] = adjusted
        app_state.state["idle_minutes_prevented"] = idle_prevented

        data = {
            "line_id": LINE_ID,
            "original_plan_units": PLAN_ORIGINAL_UNITS,
            "adjusted_plan_units": adjusted,
            "reduction_percentage": round(reduction_pct * 100, 1),
            "trigger_event": "stock_risk_detected",
            "alternative_batch_available": True,
            "idle_minutes_prevented": idle_prevented,
            "shift": "A",
        }
        event = create_ies_event(
            module_id=MODULE_PROD, module_version="1.0.0",
            event_type="production_plan_adjusted",
            category="productivity", severity="high",
            asset_id=LINE_ID, asset_type="production_line",
            data=data, correlation_id=correlation_id,
            related_assets=["SKU-ACERO-M8", LINE_ID, "CONVEYOR-1"],
        )
        publish(event)
        return event, data

    def optimize_production_flow(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        original_seq = ["EJE-TRACCION-2500", "PERNO-M8-INOX", "BUJE-AXIAL-45"]
        optimized_seq = ["PERNO-M8-INOX", "BUJE-AXIAL-45", "EJE-TRACCION-2500"]
        time_saved = random.randint(18, 55)

        data = {
            "line_id": LINE_ID,
            "original_sequence": original_seq,
            "optimized_sequence": optimized_seq,
            "optimization_reason": "material_bottleneck_identified",
            "time_saved_minutes": time_saved,
            "priority_rule": "material_availability_first",
        }
        event = create_ies_event(
            module_id=MODULE_PROD, module_version="1.0.0",
            event_type="production_flow_optimized",
            category="productivity", severity="medium",
            asset_id=LINE_ID, asset_type="production_line",
            data=data, correlation_id=correlation_id,
            related_assets=["SKU-ACERO-M8", LINE_ID, "CONVEYOR-1"],
        )
        publish(event)
        return event, data

    def calculate_oee_impact(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        idle_min = app_state.state["idle_minutes_prevented"]
        shift_min = 480.0
        lost_availability = idle_min / shift_min
        avail_original = AVAILABILITY_BASE - lost_availability
        avail_adjusted = AVAILABILITY_BASE

        oee_original = round(avail_original * PERFORMANCE_BASE * QUALITY_BASE * 100, 2)
        oee_adjusted = round(avail_adjusted * PERFORMANCE_BASE * QUALITY_BASE * 100, 2)
        oee_loss_prevented = round(oee_adjusted - oee_original, 2)
        cost_per_min_mxn = 850.0
        loss_prevented_mxn = round(idle_min * cost_per_min_mxn, 2)

        app_state.state["oee"] = oee_adjusted / 100
        app_state.state["loss_prevented_mxn"] = loss_prevented_mxn

        data = {
            "line_id": LINE_ID,
            "oee_original_pct": oee_original,
            "oee_adjusted_pct": oee_adjusted,
            "oee_loss_prevented_pct": oee_loss_prevented,
            "idle_minutes_prevented": idle_min,
            "availability_original_pct": round(avail_original * 100, 2),
            "availability_adjusted_pct": round(avail_adjusted * 100, 2),
            "performance_pct": round(PERFORMANCE_BASE * 100, 2),
            "quality_pct": round(QUALITY_BASE * 100, 2),
            "loss_prevented_mxn": loss_prevented_mxn,
        }
        event = create_ies_event(
            module_id=MODULE_PROD, module_version="1.0.0",
            event_type="oee_impact_calculated",
            category="productivity", severity="medium",
            asset_id=LINE_ID, asset_type="production_line",
            data=data, correlation_id=correlation_id,
        )
        publish(event)
        return event, data

    def adjust_production_schedule(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        current_stock = app_state.state["current_stock"]
        daily_demand = app_state.state["daily_demand"]
        stockout_h = round(current_stock / (daily_demand / 24), 2) if daily_demand else 48.0
        priority_jobs = ["JOB-2401-EJE", "JOB-2402-BUJE"]
        deferred_jobs = ["JOB-2403-ENGRANE", "JOB-2404-POLEA"]
        rescheduled_units = round(app_state.state["adjusted_plan_units"] * 0.82)
        shift_hours_saved = round(random.uniform(1.5, 4.0), 1)

        data = {
            "line_id": LINE_ID,
            "trigger": "stock_risk_detected",
            "stockout_hours_at_trigger": stockout_h,
            "priority_jobs": priority_jobs,
            "deferred_jobs": deferred_jobs,
            "rescheduled_units": rescheduled_units,
            "shift_hours_saved": shift_hours_saved,
            "method": "stock_aware_priority_scheduling",
        }
        event = create_ies_event(
            module_id=MODULE_PROD, module_version="1.0.0",
            event_type="production_schedule_adjusted",
            category="productivity", severity="high",
            asset_id=LINE_ID, asset_type="production_line",
            data=data, correlation_id=correlation_id,
            related_assets=["JOB-2401-EJE", "JOB-2402-BUJE"],
        )
        publish(event)
        return event, data

    def simulate_line_stoppage(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        current_stock = app_state.state["current_stock"]
        daily_demand = app_state.state["daily_demand"]
        stockout_h = round(current_stock / (daily_demand / 24), 2) if daily_demand else 48.0
        cost_per_hour_mxn = round(daily_demand * 850 / 24, 2)
        stoppage_h = min(stockout_h, random.uniform(2.0, 6.0))
        total_loss_mxn = round(stoppage_h * cost_per_hour_mxn, 2)
        parts_lost = round(stoppage_h * 60 * random.uniform(8, 18))
        severity = "critical" if stockout_h < 8 else "high"

        data = {
            "line_id": LINE_ID,
            "scenario": "stockout_triggered_stoppage",
            "estimated_stockout_hours": stockout_h,
            "simulated_stoppage_hours": round(stoppage_h, 2),
            "parts_production_lost": parts_lost,
            "cost_per_hour_mxn": cost_per_hour_mxn,
            "total_estimated_loss_mxn": total_loss_mxn,
            "recovery_action": "urgent_purchase_order + priority_schedule",
            "simulation_confidence": 0.88,
        }
        event = create_ies_event(
            module_id=MODULE_PROD, module_version="1.0.0",
            event_type="line_stoppage_risk_assessed",
            category="productivity", severity=severity,
            asset_id=LINE_ID, asset_type="production_line",
            data=data, correlation_id=correlation_id,
            related_assets=[LINE_ID, "CONVEYOR-1", "ALMACEN-MP-01"],
        )
        publish(event)
        return event, data

    def allocate_materials_to_lines(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        current_stock = app_state.state["current_stock"]
        lines = ["LINE-1", "LINE-2", "LINE-3"]
        demands = [round(random.uniform(0.40, 0.55), 2),
                   round(random.uniform(0.25, 0.35), 2), 0.0]
        demands[2] = round(1.0 - demands[0] - demands[1], 2)
        allocation = {
            ln: {"units_allocated": round(current_stock * d), "allocation_pct": round(d * 100, 1)}
            for ln, d in zip(lines, demands)
        }
        # LINE-1 always gets priority
        allocation["LINE-1"]["priority"] = "critical"
        shortage_covered = allocation["LINE-1"]["units_allocated"] > 0

        data = {
            "sku_id": "SKU-ACERO-M8",
            "total_stock_units": current_stock,
            "allocation_strategy": "priority_weighted_by_demand",
            "allocation": allocation,
            "primary_line": LINE_ID,
            "shortage_covered": shortage_covered,
            "rebalance_trigger": "material_bottleneck_identified",
        }
        event = create_ies_event(
            module_id=MODULE_PROD, module_version="1.0.0",
            event_type="material_allocation_optimized",
            category="productivity", severity="medium",
            asset_id="SKU-ACERO-M8", asset_type="material",
            data=data, correlation_id=correlation_id,
            related_assets=lines,
        )
        publish(event)
        return event, data

    def adjust_production_schedule(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        current_stock = app_state.state["current_stock"]
        daily_demand = app_state.state["daily_demand"]
        stockout_h = round(current_stock / (daily_demand / 24), 2) if daily_demand else 48.0
        priority_jobs = ["JOB-2401-EJE", "JOB-2402-BUJE"]
        deferred_jobs = ["JOB-2403-ENGRANE", "JOB-2404-POLEA"]
        rescheduled_units = round(app_state.state["adjusted_plan_units"] * 0.82)
        shift_hours_saved = round(random.uniform(1.5, 4.0), 1)

        data = {
            "line_id": LINE_ID,
            "trigger": "stock_risk_detected",
            "stockout_hours_at_trigger": stockout_h,
            "priority_jobs": priority_jobs,
            "deferred_jobs": deferred_jobs,
            "rescheduled_units": rescheduled_units,
            "shift_hours_saved": shift_hours_saved,
            "method": "stock_aware_priority_scheduling",
        }
        event = create_ies_event(
            module_id=MODULE_PROD, module_version="1.0.0",
            event_type="production_schedule_adjusted",
            category="productivity", severity="high",
            asset_id=LINE_ID, asset_type="production_line",
            data=data, correlation_id=correlation_id,
            related_assets=["JOB-2401-EJE", "JOB-2402-BUJE"],
        )
        publish(event)
        return event, data

    def simulate_line_stoppage(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        current_stock = app_state.state["current_stock"]
        daily_demand = app_state.state["daily_demand"]
        stockout_h = round(current_stock / (daily_demand / 24), 2) if daily_demand else 48.0
        cost_per_hour_mxn = round(daily_demand * 850 / 24, 2)
        stoppage_h = min(stockout_h, random.uniform(2.0, 6.0))
        total_loss_mxn = round(stoppage_h * cost_per_hour_mxn, 2)
        parts_lost = round(stoppage_h * 60 * random.uniform(8, 18))
        severity = "critical" if stockout_h < 8 else "high"

        data = {
            "line_id": LINE_ID,
            "scenario": "stockout_triggered_stoppage",
            "estimated_stockout_hours": stockout_h,
            "simulated_stoppage_hours": round(stoppage_h, 2),
            "parts_production_lost": int(parts_lost),
            "cost_per_hour_mxn": cost_per_hour_mxn,
            "total_estimated_loss_mxn": total_loss_mxn,
            "recovery_action": "urgent_purchase_order + priority_schedule",
            "simulation_confidence": 0.88,
        }
        event = create_ies_event(
            module_id=MODULE_PROD, module_version="1.0.0",
            event_type="line_stoppage_risk_assessed",
            category="productivity", severity=severity,
            asset_id=LINE_ID, asset_type="production_line",
            data=data, correlation_id=correlation_id,
            related_assets=[LINE_ID, "CONVEYOR-1", "ALMACEN-MP-01"],
        )
        publish(event)
        return event, data

    def allocate_materials_to_lines(
        self, correlation_id: str | None = None
    ) -> tuple[IESEvent, dict]:
        current_stock = app_state.state["current_stock"]
        lines = ["LINE-1", "LINE-2", "LINE-3"]
        d0 = round(random.uniform(0.40, 0.55), 2)
        d1 = round(random.uniform(0.25, 0.35), 2)
        d2 = round(1.0 - d0 - d1, 2)
        demands = [d0, d1, d2]
        allocation = {
            ln: {"units_allocated": round(current_stock * d), "allocation_pct": round(d * 100, 1)}
            for ln, d in zip(lines, demands)
        }
        allocation["LINE-1"]["priority"] = "critical"
        shortage_covered = allocation["LINE-1"]["units_allocated"] > 0

        data = {
            "sku_id": "SKU-ACERO-M8",
            "total_stock_units": current_stock,
            "allocation_strategy": "priority_weighted_by_demand",
            "allocation": allocation,
            "primary_line": LINE_ID,
            "shortage_covered": shortage_covered,
            "rebalance_trigger": "material_bottleneck_identified",
        }
        event = create_ies_event(
            module_id=MODULE_PROD, module_version="1.0.0",
            event_type="material_allocation_optimized",
            category="productivity", severity="medium",
            asset_id="SKU-ACERO-M8", asset_type="material",
            data=data, correlation_id=correlation_id,
            related_assets=lines,
        )
        publish(event)
        return event, data
