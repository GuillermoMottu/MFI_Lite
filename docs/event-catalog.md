# Catálogo de Eventos IES v2.0 — MaterialFlow Intelligence Lite

Todos los eventos cumplen el estándar IES v2.0: `platform_version: "2.0.0"`, `timestamp` en UTC con `Z`, `event_id` UUID v4, `data` (no `payload`).

---

## Schema base IES v2.0

```json
{
  "event_id": "uuid-v4",
  "timestamp": "2026-01-15T14:32:10Z",
  "platform_version": "2.0.0",
  "module": { "id": "module_snake_case", "version": "1.0.0" },
  "asset": {
    "asset_id": "SKU-ACERO-M8",
    "asset_type": "material",
    "plant_id": "PLT-JUAREZ-01",
    "line_id": "LINE-1"
  },
  "event": {
    "type": "event_type_snake_case",
    "category": "productivity",
    "severity": "high"
  },
  "data": { },
  "metadata": {
    "correlation_id": "uuid-del-run",
    "related_assets": []
  }
}
```

**Categorías válidas**: `quality`, `productivity`, `maintenance`, `energy`, `safety`, `configuration`, `system`  
**Severidades válidas**: `low`, `medium`, `high`, `critical`

---

## Eventos por Agente

### ERP — `erp_gestion_empresarial`

| Event Type | Tool | Trigger | Severity | Campos clave en `data` |
|---|---|---|---|---|
| `material_demand_forecasted` | `predict_demand` | Llamada directa o paso 1 del demo | `medium` | `sku_id`, `avg_daily_consumption_units`, `horizon_days`, `demand_factor`, `predicted_units`, `confidence` |
| `stock_risk_detected` | `optimize_stock_levels` | Stock < punto de reorden | `high` / `critical` | `sku_id`, `current_stock_units`, `reorder_point_units`, `estimated_stockout_hours`, `risk_detected`, `lead_time_days` |
| `urgent_purchase_order_created` | `generate_purchase_order` | Stock en riesgo crítico | `critical` | `purchase_order_id`, `quantity_units`, `unit_cost_mxn`, `total_cost_mxn`, `provider`, `provider_lead_time_days`, `urgency` |
| `purchase_order_draft_created` | `approve_recommendation` | PA aprueba recomendación operativa | `medium` | `po_id`, `sku_id`, `supplier_id`, `supplier_name`, `quantity_units`, `unit_cost_mxn`, `total_cost_mxn`, `required_date`, `estimated_arrival_date`, `status`, `source_recommendation_id` |
| `purchase_order_updated` | `update_purchase_order` | PA edita proveedor, cantidad, fecha o comentario | `low` | `po_id`, `sku_id`, `supplier_id`, `supplier_name`, `quantity_units`, `unit_cost_mxn`, `total_cost_mxn`, `required_date`, `estimated_arrival_date`, `status`, `source_recommendation_id` |
| `purchase_order_approved` | `approve_purchase_order` | PA aprueba una orden operativa | `high` | `po_id`, `sku_id`, `supplier_id`, `supplier_name`, `quantity_units`, `unit_cost_mxn`, `total_cost_mxn`, `required_date`, `estimated_arrival_date`, `status`, `source_recommendation_id` |
| `erp_inventory_synced` | `sync_erp_data_local` | Sincronización programada | `low` | `synced_records`, `conflicts_resolved`, `sync_type`, `sync_duration_ms` |

### Producción — `produccion_avanzada`

| Event Type | Tool | Trigger | Severity | Campos clave en `data` |
|---|---|---|---|---|
| `production_plan_adjusted` | `plan_production_automatically` | Paso 3 del demo / llamada directa | `medium` | `line_id`, `original_plan_units`, `adjusted_plan_units`, `adjustment_reason`, `shift`, `parts_per_min`, `oee_estimated` |
| `production_flow_optimized` | `optimize_production_flow` | Paso 7 del demo | `medium` | `line_id`, `bottleneck_removed`, `cycle_time_before_s`, `cycle_time_after_s`, `throughput_improvement_pct`, `idle_minutes_prevented` |
| `oee_impact_calculated` | `calculate_oee_impact` | Llamada directa | `medium` | `line_id`, `availability`, `performance`, `quality`, `oee_current`, `oee_target`, `production_loss_units` |
| `material_related_idle_risk_detected` | `detect_material_related_idle_time` | Paso 4 del demo (Edge) | `high` | `line_id`, `idle_risk_detected`, `stockout_hours`, `idle_minutes_at_risk`, `estimated_loss_mxn`, `recommendation` |
| `production_backlog_resequenced` | `resequence_backlog` | PA aplica secuencia material-aware | `medium` / `high` | `strategy`, `jobs_total`, `jobs_impacted`, `critical_jobs`, `applied_by`, `updated_jobs` |

### AI/ML — `ai_ml_industrial`

| Event Type | Tool | Trigger | Severity | Campos clave en `data` |
|---|---|---|---|---|
| `material_lifecycle_risk_detected` | `detect_process_deviation` | Paso 5 del demo | `high` / `critical` | `sku_id`, `risk_score_pct`, `deviation_type`, `z_score`, `contributing_factors`, `recommended_action` |
| `material_bottleneck_identified` | `identify_bottlenecks` | Paso 6 del demo | `critical` | `line_id`, `bottleneck_location`, `bottleneck_type`, `throughput_loss_pct`, `root_cause`, `estimated_resolution_min` |
| `operational_recommendation_generated` | `generate_digital_twin_model` | Paso 9 del demo | `high` | `asset_id`, `scenario_act_now`, `scenario_wait_24h`, `recommended_scenario`, `confidence`, `risk_if_wait` |
| `operational_recommendation_approved` | `approve_recommendation` | PA aprueba recomendación operativa | `high` | `recommendation_id`, `recommendation_type`, `status`, `decided_by`, `decision_comment`, `sku_id`, `line_id`, `estimated_impact_mxn` |
| `operational_recommendation_rejected` | `reject_recommendation` | PA rechaza recomendación operativa con comentario | `medium` | `recommendation_id`, `recommendation_type`, `status`, `decided_by`, `decision_comment`, `sku_id`, `line_id`, `estimated_impact_mxn` |
| `material_risk_model_updated` | `train_material_risk_model` | Llamada directa | `low` | `model_id`, `training_samples`, `accuracy`, `f1_score`, `features_used`, `model_version` |

### Edge — `edge_material_runtime`

| Event Type | Tool | Trigger | Severity | Campos clave en `data` |
|---|---|---|---|---|
| `material_lifecycle_risk_detected` | `run_edge_inference_and_buffer` | Risk score > 0.72 en Edge | `critical` | `sku_id`, `line_id`, `risk_score`, `is_critical`, `threshold`, `model`, `inference_ms`, `runtime: "edge"` |
| `operational_recommendation_generated` | `trigger_local_recommendation` | Cloud offline + riesgo alto | `high` | `recommendation`, `risk_score`, `runtime: "edge"`, `cloud_available`, `action_required` |

---

## Flujo Cross-Agent (Demo Completo)

```
correlation_id = UUID4 (compartido por todos los pasos)

Paso 1  ERP     → material_demand_forecasted          [medium]
Paso 2  ERP     → stock_risk_detected                 [high/critical]
Paso 3  PROD    → production_plan_adjusted             [medium]
Paso 4  EDGE    → material_related_idle_risk_detected  [high]
Paso 5  AI/ML   → material_lifecycle_risk_detected     [high/critical]
Paso 6  AI/ML   → material_bottleneck_identified       [critical] ← 🔥 punto de escalación
Paso 7  PROD    → production_flow_optimized            [medium]
Paso 8  ERP     → urgent_purchase_order_created        [critical]
Paso 9  AI/ML   → operational_recommendation_generated [high]
```

---

## Escenario Offline

```
1. simulate-cloud-down   → cloud_connected = false
2. detect-idle           → eventos buffereados en edge_buffer.db (SQLite)
3. simulate-cloud-up     → cloud_connected = true
4. replay                → eventos FIFO del buffer publicados en cloud.db
                          deduplicación por event_id (PRIMARY KEY)
```

---

## Campos de metadata

| Campo | Tipo | Descripción |
|---|---|---|
| `correlation_id` | UUID4 string | Vincula todos los eventos de un run de demo |
| `related_assets` | array | Assets secundarios involucrados (e.g. CONVEYOR-1) |
| `source` | string | `"cloud"` o `"edge_replay"` |

---

## Reglas de validación IES v2.0

1. `platform_version` debe ser exactamente `"2.0.0"`
2. `timestamp` debe terminar en `Z` (UTC)
3. `event_id` debe ser UUID v4 (36 chars, 4 guiones)
4. `event.type` y `module.id` deben ser `snake_case`
5. `event.category` ∈ {quality, productivity, maintenance, energy, safety, configuration, system}
6. `event.severity` ∈ {low, medium, high, critical}
7. Campo `payload` está **prohibido** — usar `data`
