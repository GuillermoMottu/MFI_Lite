# MaterialFlow Intelligence Lite

**Plataforma de Coordinación Inteligente del Ciclo de Vida de Materiales en Producción**  
CTRL+HACK 2.0 — IES v2.0 Platform

---

## Problema industrial

En plantas manufactureras como PLT-JUAREZ-01, la ruptura de stock de materiales clave (SKU-ACERO-M8) detiene líneas de producción completas. Los agentes ERP, Producción e IA/ML operan en silos: sin coordinación en tiempo real, el tiempo de respuesta ante un desabasto crítico supera las 4 horas. **MaterialFlow Intelligence Lite** conecta los 3 agentes bajo un evento estándar (IES v2.0), detecta riesgo en < 2 segundos y genera órdenes de compra urgentes de forma autónoma, incluso sin conectividad a la nube (Edge Computing).

---

## Los 3 Agentes

| Agente | ID oficial | Responsabilidad |
|---|---|---|
| **ERP** | `erp_gestion_empresarial` | Pronóstico de demanda, riesgo de stock, órdenes de compra |
| **Producción** | `produccion_avanzada` | Planificación, OEE, flujo de línea, detección de idle |
| **AI/ML** | `ai_ml_industrial` | Isolation Forest edge, desviaciones, bottleneck, digital twin |

---

## Levantar el sistema

```bash
# Clonar y construir
git clone <repo-url>
cd MFI_Lite
docker compose up --build
```

- **Frontend**: http://localhost:5173
- **API + Swagger UI**: http://localhost:8000/docs
- **SSE stream**: http://localhost:8000/api/events/stream

---

## Demo rápida (5 minutos)

1. Abrir http://localhost:5173 en el navegador
2. Click **▶ Ejecutar Demo** — observar el `FlowDiagram` iluminarse paso a paso (ERP → Prod → AI/ML → Prod → ERP → AI/ML)
3. Click sobre cualquier evento en el **Timeline IES v2.0** → ver JSON validado con `correlation_id` compartido

**Escenario Offline (Edge Computing):**
1. Click **🔴 Cloud Down** — edge sigue operando, eventos se bufferizarán en SQLite
2. Click **Demo Offline Narrativa** — Edge detecta → bufferiza → Cloud se restaura → Replay automático
3. Verificar que `Buffer Edge` en KPIs llegó a 0 tras el replay

---

## Tabla de Endpoints

### Demo
| Método | URL | Descripción |
|---|---|---|
| `POST` | `/api/demo/run` | Ejecuta flujo cross-agent de 9 pasos con `correlation_id` compartido |
| `POST` | `/api/demo/reset` | Resetea estado completo del demo |
| `GET` | `/api/demo/status` | KPIs actuales: stock, OEE, risk_score, buffer_pending |
| `POST` | `/api/demo/run-offline-narrative` | Escenario offline automatizado: down → buffer → up → replay |

### Eventos (IES v2.0)
| Método | URL | Descripción |
|---|---|---|
| `GET` | `/api/events/` | Lista eventos (`?limit=50&module_id=...&event_type=...`) |
| `GET` | `/api/events/stream` | SSE en tiempo real (`EventSource`) |
| `GET` | `/api/events/chain` | Cadena causal por `?correlation_id={uuid}` |

### ERP — `erp_gestion_empresarial`
| Método | URL | Body ejemplo | Descripción |
|---|---|---|---|
| `POST` | `/api/erp/predict-demand` | — | Pronostica demanda, emite `material_demand_forecasted` |
| `POST` | `/api/erp/optimize-stock-levels` | — | Detecta riesgo, emite `stock_risk_detected` |
| `POST` | `/api/erp/generate-purchase-order` | — | Genera PO urgente, emite `urgent_purchase_order_created` |
| `POST` | `/api/erp/sync-erp-data` | — | Sincroniza inventario, emite `erp_inventory_synced` |
| `GET` | `/api/erp/status` | — | Stock actual, reorder point, POs activas |
| `GET` | `/api/erp/stock-history` | — | Histórico de stock para gráfica |

### Producción — `produccion_avanzada`
| Método | URL | Descripción |
|---|---|---|
| `POST` | `/api/production/plan-automatically` | Plan automático, emite `production_plan_adjusted` |
| `POST` | `/api/production/optimize-flow` | Optimiza flujo, emite `production_flow_optimized` |
| `POST` | `/api/production/calculate-oee` | Calcula OEE, emite `oee_impact_calculated` |
| `POST` | `/api/production/adjust-schedule` | Reprograma jobs por restricción de material, emite `production_schedule_adjusted` |
| `POST` | `/api/production/simulate-stoppage` | Simula escenario de paro de línea, emite `line_stoppage_risk_assessed` |
| `POST` | `/api/production/allocate-materials` | Asigna stock a líneas por prioridad, emite `material_allocation_optimized` |
| `POST` | `/api/production/detect-idle` | Detecta idle risk, emite `material_related_idle_risk_detected` |
| `GET` | `/api/production/collect-data` | Señales actuales del Edge |
| `GET` | `/api/production/consumption-rate` | Tasa de consumo en tiempo real |
| `GET` | `/api/production/status` | OEE, plan, idle prevenido |

### AI/ML — `ai_ml_industrial`
| Método | URL | Descripción |
|---|---|---|
| `POST` | `/api/aiml/detect-deviation` | Desviación de proceso, emite `material_lifecycle_risk_detected` |
| `POST` | `/api/aiml/identify-bottlenecks` | Bottleneck crítico, emite `material_bottleneck_identified` |
| `POST` | `/api/aiml/digital-twin` | Modelo twin con 2 escenarios, emite `operational_recommendation_generated` |
| `POST` | `/api/aiml/train-model` | Entrena modelo de riesgo, emite `material_risk_model_updated` |
| `POST` | `/api/aiml/predict-rul` | Predice Remaining Useful Life del equipo, emite `equipment_rul_predicted` |
| `POST` | `/api/aiml/classify-anomaly` | Clasifica tipo de anomalía multi-señal, emite `anomaly_type_classified` |
| `POST` | `/api/aiml/maintenance-recommendation` | Recomienda mantenimiento predictivo, emite `predictive_maintenance_recommended` |
| `POST` | `/api/aiml/forecast-oee` | Proyecta degradación OEE a 24/48/72h, emite `oee_degradation_forecasted` |
| `GET` | `/api/aiml/signals` | 5 señales edge actuales |
| `POST` | `/api/aiml/edge-inference` | Ejecuta Isolation Forest local |
| `GET` | `/api/aiml/inference-status` | Última inferencia con señales y score |
| `GET` | `/api/aiml/status` | Risk score, pérdida evitada, último bottleneck |

### Operacion PA
| Metodo | URL | Descripcion |
|---|---|---|
| `GET` | `/api/recommendations/` | Lista recomendaciones operativas persistidas |
| `GET` | `/api/recommendations/active` | Devuelve la recomendacion pendiente prioritaria |
| `GET` | `/api/recommendations/decisions` | Lista decisiones auditables del PA |
| `POST` | `/api/recommendations/{id}/approve` | Aprueba recomendacion, emite IES y crea PO draft |
| `POST` | `/api/recommendations/{id}/reject` | Rechaza recomendacion con comentario |
| `GET` | `/api/purchase-orders/` | Lista ordenes de compra operativas |
| `PATCH` | `/api/purchase-orders/{po_id}` | Edita proveedor, cantidad, fecha requerida o comentario |
| `POST` | `/api/purchase-orders/{po_id}/approve` | Aprueba PO operativa |
| `GET` | `/api/suppliers/` | Lista catalogo activo de proveedores |
| `GET` | `/api/suppliers/recommended` | Recomienda proveedor por `strategy=urgency` o `strategy=cost` |
| `POST` | `/api/suppliers/` | Crea proveedor |
| `PATCH` | `/api/suppliers/{supplier_id}` | Actualiza proveedor |
| `DELETE` | `/api/suppliers/{supplier_id}` | Da de baja proveedor |
| `GET` | `/api/materials/` | Lista inventario multi-SKU con riesgo calculado |
| `GET` | `/api/materials/?status=critical` | Filtra inventario por `critical`, `low_stock` o `normal` |
| `PATCH` | `/api/materials/{sku_id}` | Actualiza stock, demanda, punto de reorden o criticidad |
| `POST` | `/api/materials/{sku_id}/recommendation` | Genera recomendacion operativa para SKU en riesgo |
| `GET` | `/api/production/backlog` | Lista jobs de produccion con riesgo de material |
| `GET` | `/api/production/backlog/impacted` | Lista jobs impactados por bajo stock o criticidad |
| `GET` | `/api/production/backlog/suggestion` | Sugiere nueva secuencia material-aware |
| `POST` | `/api/production/backlog/resequence` | Aplica reprogramacion y emite evento IES |
| `PATCH` | `/api/production/backlog/{job_id}` | Edita prioridad, secuencia, estado o inicio requerido |
| `GET` | `/api/audit/` | Historial unificado con filtros por entidad, SKU o correlation_id |
| `GET` | `/api/audit/export?format=json` | Exporta auditoria en JSON |
| `GET` | `/api/audit/export?format=csv` | Exporta auditoria en CSV |

### Offline / Edge
| Método | URL | Descripción |
|---|---|---|
| `POST` | `/api/offline/simulate-cloud-down` | Desconectar Cloud (Edge sigue operando) |
| `POST` | `/api/offline/simulate-cloud-up` | Restaurar conexión Cloud |
| `POST` | `/api/offline/replay` | Replay FIFO del buffer SQLite al Cloud |
| `GET` | `/api/offline/buffer-status` | Eventos pendientes en buffer, último replay |
| `POST` | `/api/offline/simulate-low-stock` | Forzar stock a 120 uds para activar riesgo crítico |

### Health
| Método | URL | Descripción |
|---|---|---|
| `GET` | `/api/health` | Liveness check del API |
| `GET` | `/health` | Alias de liveness para Docker healthcheck |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                  cloud-api (FastAPI)                 │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ ERP Agent │  │  Prod Agent  │  │ AI/ML Agent  │  │
│  └─────┬─────┘  └──────┬───────┘  └──────┬───────┘  │
│        └───────────────┴──────────────────┘         │
│                    IES v2.0 Event Bus (SSE)          │
│                    SQLite cloud.db                   │
│  ┌──────────────────────────────────────────────┐   │
│  │  Edge Module (dentro del mismo contenedor)   │   │
│  │  local_inference.py │ sqlite_buffer.db        │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                         │ nginx proxy /api/
┌─────────────────────────────────────────────────────┐
│              frontend (React 18 + Vite)              │
│  KpiCards │ FlowDiagram │ Timeline │ EdgeInference   │
└─────────────────────────────────────────────────────┘
```

---

## Mapeo criterios CTRL+HACK 2.0

- **D1 — Uso de IES v2.0**: Todos los eventos pasan validación Pydantic v2 (platform_version, timestamp Z, snake_case, categorías válidas). Ver `/docs` para schema completo.
- **D2 — Agentes coordinados**: 3 agentes oficiales comparten `correlation_id` en 9 pasos. FlowDiagram muestra la cadena en tiempo real.
- **D3 — Edge Computing**: `local_inference.py` ejecuta Isolation Forest heurístico en el edge. `sqlite_buffer.db` guarda eventos cuando la nube no está disponible. Replay automático FIFO al restaurar.
- **D4 — Valor industrial**: KPIs con fórmulas transparentes: pérdida evitada = ΔOEE × factor_línea × $480/hora. Stockout estimado en horas. OEE = Disponibilidad × Rendimiento × Calidad.
- **D5 — Demo funcional**: `docker compose up --build` levanta el sistema completo. `/api/demo/run` genera 9 eventos cross-agent en < 5 segundos. SSE stream disponible en `/api/events/stream`.

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| API | FastAPI + Uvicorn |
| Validación | Pydantic v2 |
| Base de datos | SQLite (`cloud.db`, `edge_buffer.db`) |
| Tiempo real | SSE con `StreamingResponse` |
| Frontend | React 18 + Vite + Tailwind CSS |
| Contenedores | Docker Compose (2 servicios) |

---

## Variables de entorno

```env
CLOUD_DB_PATH=/tmp/cloud.db
EDGE_DB_PATH=/tmp/edge_buffer.db
```

Ver `.env.example` en la raíz del proyecto.

---

## Colección Postman

Importa `docs/postman_collection.json` en Postman para probar todos los endpoints de forma interactiva.  
La colección incluye 26 requests organizados en 6 carpetas (Demo, ERP, Producción, AI/ML, Offline, Eventos) con un script pre-request que guarda automáticamente el `correlation_id` entre calls.

---

## Decisiones técnicas

| Decisión | Justificación |
|---|---|
| SQLite en lugar de PostgreSQL | Suficiente para demo; elimina dependencias externas y simplifica Docker |
| SSE en lugar de WebSocket | Comunicación unidireccional cloud → browser; menos código, nativo en navegadores |
| Edge como módulo lógico (no contenedor) | Separación por comportamiento, no por infraestructura; simplifica `docker compose` |
| Isolation Forest heurístico | Modelo ligero en < 1ms de inferencia; apto para ejecución en edge sin GPU |
