from uuid import uuid4
from agents.erp_agent import ERPAgent
from agents.production_agent import ProductionAgent
from agents.aiml_agent import AIMLAgent
from edge.production_edge_tools import detect_material_related_idle_time
from services.event_bus import clear_demo_events, publish_system_event
from edge.sqlite_buffer import clear_buffer
from state import _snapshot_stock
import state as app_state

erp = ERPAgent()
prod = ProductionAgent()
aiml = AIMLAgent()

DEMO_STEPS = [
    (1, "erp_gestion_empresarial", "predict_demand"),
    (2, "erp_gestion_empresarial", "optimize_stock_levels"),
    (3, "produccion_avanzada", "plan_production_automatically"),
    (4, "edge_material_runtime", "detect_material_related_idle_time"),
    (5, "ai_ml_industrial", "detect_process_deviation"),
    (6, "ai_ml_industrial", "identify_bottlenecks"),
    (7, "produccion_avanzada", "optimize_production_flow"),
    (8, "erp_gestion_empresarial", "generate_purchase_order"),
    (9, "ai_ml_industrial", "generate_digital_twin_model"),
]


def _emit_step(step_num: int, agent: str, tool: str, correlation_id: str, started: bool) -> None:
    app_state.state["current_demo_step"] = step_num if started else 0
    publish_system_event({
        "__type": "demo_step",
        "started": started,
        "step_number": step_num,
        "total_steps": len(DEMO_STEPS),
        "agent": agent,
        "tool": tool,
        "correlation_id": correlation_id,
    })


def run_full_demo() -> list[dict]:
    correlation_id = str(uuid4())
    app_state.state["last_correlation_id"] = correlation_id
    app_state.state["demo_running"] = True
    app_state.state["stock_history"] = []
    events_collected = []

    def _collect(result):
        if isinstance(result, tuple):
            event, _ = result
            if event:
                events_collected.append(event.model_dump())
        elif isinstance(result, dict) and result.get("event"):
            events_collected.append(result["event"])

    # Paso 1: ERP predict_demand
    _emit_step(1, *DEMO_STEPS[0][1:], correlation_id, True)
    _collect(erp.predict_demand(correlation_id=correlation_id))
    _emit_step(1, *DEMO_STEPS[0][1:], correlation_id, False)

    # Paso 2: ERP optimize_stock_levels
    _emit_step(2, *DEMO_STEPS[1][1:], correlation_id, True)
    app_state.state["current_stock"] = 60
    _collect(erp.optimize_stock_levels(correlation_id=correlation_id))
    _snapshot_stock()
    _emit_step(2, *DEMO_STEPS[1][1:], correlation_id, False)

    # Paso 3: Producción plan_production_automatically
    _emit_step(3, *DEMO_STEPS[2][1:], correlation_id, True)
    _collect(prod.plan_production_automatically(correlation_id=correlation_id))
    _emit_step(3, *DEMO_STEPS[2][1:], correlation_id, False)

    # Paso 4: Edge detect_material_related_idle_time
    _emit_step(4, *DEMO_STEPS[3][1:], correlation_id, True)
    result = detect_material_related_idle_time(correlation_id=correlation_id)
    if result:
        _collect(result)
    else:
        # Forzar stock bajo para garantizar idle risk en el demo
        app_state.state["current_stock"] = min(app_state.state["current_stock"], 150)
        result = detect_material_related_idle_time(correlation_id=correlation_id)
        if result:
            _collect(result)
    _emit_step(4, *DEMO_STEPS[3][1:], correlation_id, False)

    # Paso 5: AI/ML detect_process_deviation
    _emit_step(5, *DEMO_STEPS[4][1:], correlation_id, True)
    _collect(aiml.detect_process_deviation(correlation_id=correlation_id))
    _emit_step(5, *DEMO_STEPS[4][1:], correlation_id, False)

    # Paso 6: AI/ML identify_bottlenecks
    _emit_step(6, *DEMO_STEPS[5][1:], correlation_id, True)
    _collect(aiml.identify_bottlenecks(correlation_id=correlation_id))
    _emit_step(6, *DEMO_STEPS[5][1:], correlation_id, False)

    # Paso 7: Producción optimize_production_flow
    _emit_step(7, *DEMO_STEPS[6][1:], correlation_id, True)
    _collect(prod.optimize_production_flow(correlation_id=correlation_id))
    _emit_step(7, *DEMO_STEPS[6][1:], correlation_id, False)

    # Paso 8: ERP generate_purchase_order
    _emit_step(8, *DEMO_STEPS[7][1:], correlation_id, True)
    _collect(erp.generate_purchase_order(correlation_id=correlation_id))
    _snapshot_stock()
    _emit_step(8, *DEMO_STEPS[7][1:], correlation_id, False)

    # Paso 9: AI/ML generate_digital_twin_model
    _emit_step(9, *DEMO_STEPS[8][1:], correlation_id, True)
    _collect(aiml.generate_digital_twin_model(correlation_id=correlation_id))
    _emit_step(9, *DEMO_STEPS[8][1:], correlation_id, False)

    app_state.state["demo_running"] = False
    app_state.state["current_demo_step"] = 0
    return events_collected


def reset_demo() -> None:
    clear_demo_events()
    clear_buffer()
    app_state.reset_state()
