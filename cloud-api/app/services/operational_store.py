import json
import os
import sqlite3
from csv import DictWriter
from datetime import datetime, timezone
from io import StringIO

from config import CLOUD_DB_PATH, SKU

_initialized = False

DEFAULT_SUPPLIERS = [
    {
        "supplier_id": "SUP-PROVEEMETAL",
        "name": "ProveeMetal SA",
        "sku_ids": [SKU, "SKU-RESINA-P22"],
        "lead_time_days": 2,
        "unit_cost_mxn": 36.5,
        "reliability_score": 0.94,
        "minimum_order_quantity": 500,
        "active": True,
    },
    {
        "supplier_id": "SUP-ACEROS-NORTE",
        "name": "Aceros del Norte",
        "sku_ids": [SKU, "SKU-EMPAQUE-C7"],
        "lead_time_days": 4,
        "unit_cost_mxn": 33.8,
        "reliability_score": 0.89,
        "minimum_order_quantity": 750,
        "active": True,
    },
    {
        "supplier_id": "SUP-RAPIMETAL",
        "name": "RapiMetal Express",
        "sku_ids": [SKU, "SKU-RESINA-P22"],
        "lead_time_days": 1,
        "unit_cost_mxn": 41.2,
        "reliability_score": 0.91,
        "minimum_order_quantity": 300,
        "active": True,
    },
]

DEFAULT_MATERIALS = [
    {
        "sku_id": SKU,
        "name": "Acero M8",
        "line_id": "LINE-1",
        "warehouse": "ALMACEN-MP-01",
        "current_stock_units": 60,
        "reorder_point_units": 210,
        "daily_demand_units": 240.0,
        "unit_cost_mxn": 36.5,
        "criticality": "critical",
        "active": True,
    },
    {
        "sku_id": "SKU-RESINA-P22",
        "name": "Resina P22",
        "line_id": "LINE-2",
        "warehouse": "ALMACEN-MP-01",
        "current_stock_units": 460,
        "reorder_point_units": 520,
        "daily_demand_units": 130.0,
        "unit_cost_mxn": 72.0,
        "criticality": "high",
        "active": True,
    },
    {
        "sku_id": "SKU-EMPAQUE-C7",
        "name": "Empaque C7",
        "line_id": "LINE-3",
        "warehouse": "ALMACEN-MP-02",
        "current_stock_units": 2200,
        "reorder_point_units": 900,
        "daily_demand_units": 180.0,
        "unit_cost_mxn": 5.8,
        "criticality": "medium",
        "active": True,
    },
]

DEFAULT_PRODUCTION_JOBS = [
    {
        "job_id": "JOB-2401-EJE",
        "product": "EJE-TRACCION-2500",
        "sku_id": SKU,
        "line_id": "LINE-1",
        "planned_units": 1200,
        "priority": 1,
        "sequence": 1,
        "status": "scheduled",
        "required_start": "2026-05-18T08:00:00Z",
        "estimated_duration_min": 180,
    },
    {
        "job_id": "JOB-2402-RESINA",
        "product": "CARCASA-P22",
        "sku_id": "SKU-RESINA-P22",
        "line_id": "LINE-2",
        "planned_units": 800,
        "priority": 2,
        "sequence": 2,
        "status": "scheduled",
        "required_start": "2026-05-18T10:00:00Z",
        "estimated_duration_min": 150,
    },
    {
        "job_id": "JOB-2403-EMPAQUE",
        "product": "KIT-EMPAQUE-C7",
        "sku_id": "SKU-EMPAQUE-C7",
        "line_id": "LINE-3",
        "planned_units": 1600,
        "priority": 3,
        "sequence": 3,
        "status": "scheduled",
        "required_start": "2026-05-18T13:00:00Z",
        "estimated_duration_min": 120,
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _connect() -> sqlite3.Connection:
    db_dir = os.path.dirname(CLOUD_DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(CLOUD_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    global _initialized
    if _initialized:
        return
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS recommendations (
            recommendation_id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            sku_id TEXT NOT NULL,
            line_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            recommended_action TEXT NOT NULL,
            alternative_actions_json TEXT NOT NULL,
            estimated_impact_mxn REAL NOT NULL,
            risk_score REAL NOT NULL,
            source_event_id TEXT NOT NULL,
            correlation_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            decided_at TEXT,
            decided_by TEXT,
            decision_comment TEXT,
            purchase_order_id TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_recommendations_status
            ON recommendations(status, priority, created_at);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_recommendations_correlation_type
            ON recommendations(correlation_id, type);

        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            sku_ids_json TEXT NOT NULL,
            lead_time_days INTEGER NOT NULL,
            unit_cost_mxn REAL NOT NULL,
            reliability_score REAL NOT NULL,
            minimum_order_quantity INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS materials (
            sku_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            line_id TEXT NOT NULL,
            warehouse TEXT NOT NULL,
            current_stock_units INTEGER NOT NULL,
            reorder_point_units INTEGER NOT NULL,
            daily_demand_units REAL NOT NULL,
            unit_cost_mxn REAL NOT NULL,
            criticality TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            po_id TEXT PRIMARY KEY,
            sku_id TEXT NOT NULL,
            line_id TEXT NOT NULL,
            supplier_id TEXT NOT NULL,
            supplier_name TEXT NOT NULL,
            supplier_lead_time_days INTEGER NOT NULL,
            quantity_units INTEGER NOT NULL,
            unit_cost_mxn REAL NOT NULL,
            total_cost_mxn REAL NOT NULL,
            required_date TEXT NOT NULL,
            estimated_arrival_date TEXT NOT NULL,
            status TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            approved_by TEXT,
            approved_at TEXT,
            source_recommendation_id TEXT NOT NULL,
            correlation_id TEXT NOT NULL,
            pa_comment TEXT
        );

        CREATE TABLE IF NOT EXISTS production_jobs (
            job_id TEXT PRIMARY KEY,
            product TEXT NOT NULL,
            sku_id TEXT NOT NULL,
            line_id TEXT NOT NULL,
            planned_units INTEGER NOT NULL,
            priority INTEGER NOT NULL,
            sequence INTEGER NOT NULL,
            status TEXT NOT NULL,
            required_start TEXT NOT NULL,
            estimated_duration_min INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_production_jobs_sequence
            ON production_jobs(status, sequence);

        CREATE INDEX IF NOT EXISTS idx_purchase_orders_status
            ON purchase_orders(status, created_at);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_purchase_orders_recommendation
            ON purchase_orders(source_recommendation_id);

        CREATE TABLE IF NOT EXISTS decision_logs (
            decision_id TEXT PRIMARY KEY,
            recommendation_id TEXT NOT NULL,
            action TEXT NOT NULL,
            user TEXT NOT NULL,
            comment TEXT,
            correlation_id TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_decision_logs_correlation
            ON decision_logs(correlation_id, timestamp);
    """)
    _seed_suppliers(conn)
    _seed_materials(conn)
    _seed_production_jobs(conn)
    conn.commit()
    conn.close()
    _initialized = True


def _seed_suppliers(conn: sqlite3.Connection) -> None:
    for supplier in DEFAULT_SUPPLIERS:
        now = _now()
        conn.execute(
            """INSERT INTO suppliers
               (supplier_id, name, sku_ids_json, lead_time_days, unit_cost_mxn,
                reliability_score, minimum_order_quantity, active, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(supplier_id) DO UPDATE SET
                 name = excluded.name,
                 sku_ids_json = excluded.sku_ids_json,
                 lead_time_days = excluded.lead_time_days,
                 unit_cost_mxn = excluded.unit_cost_mxn,
                 reliability_score = excluded.reliability_score,
                 minimum_order_quantity = excluded.minimum_order_quantity,
                 active = excluded.active,
                 updated_at = excluded.updated_at""",
            (
                supplier["supplier_id"],
                supplier["name"],
                json.dumps(supplier["sku_ids"]),
                supplier["lead_time_days"],
                supplier["unit_cost_mxn"],
                supplier["reliability_score"],
                supplier["minimum_order_quantity"],
                1 if supplier.get("active", True) else 0,
                now,
                now,
            ),
        )


def _seed_materials(conn: sqlite3.Connection) -> None:
    for material in DEFAULT_MATERIALS:
        now = _now()
        conn.execute(
            """INSERT INTO materials
               (sku_id, name, line_id, warehouse, current_stock_units, reorder_point_units,
                daily_demand_units, unit_cost_mxn, criticality, active, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(sku_id) DO UPDATE SET
                 name = excluded.name,
                 line_id = excluded.line_id,
                 warehouse = excluded.warehouse,
                 current_stock_units = excluded.current_stock_units,
                 reorder_point_units = excluded.reorder_point_units,
                 daily_demand_units = excluded.daily_demand_units,
                 unit_cost_mxn = excluded.unit_cost_mxn,
                 criticality = excluded.criticality,
                 active = excluded.active,
                 updated_at = excluded.updated_at""",
            (
                material["sku_id"],
                material["name"],
                material["line_id"],
                material["warehouse"],
                material["current_stock_units"],
                material["reorder_point_units"],
                material["daily_demand_units"],
                material["unit_cost_mxn"],
                material["criticality"],
                1 if material.get("active", True) else 0,
                now,
                now,
            ),
        )


def _seed_production_jobs(conn: sqlite3.Connection) -> None:
    for job in DEFAULT_PRODUCTION_JOBS:
        now = _now()
        conn.execute(
            """INSERT INTO production_jobs
               (job_id, product, sku_id, line_id, planned_units, priority, sequence,
                status, required_start, estimated_duration_min, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(job_id) DO UPDATE SET
                 product = excluded.product,
                 sku_id = excluded.sku_id,
                 line_id = excluded.line_id,
                 planned_units = excluded.planned_units,
                 priority = excluded.priority,
                 sequence = excluded.sequence,
                 status = excluded.status,
                 required_start = excluded.required_start,
                 estimated_duration_min = excluded.estimated_duration_min,
                 updated_at = excluded.updated_at""",
            (
                job["job_id"],
                job["product"],
                job["sku_id"],
                job["line_id"],
                job["planned_units"],
                job["priority"],
                job["sequence"],
                job["status"],
                job["required_start"],
                job["estimated_duration_min"],
                now,
                now,
            ),
        )


def reset_operational_data() -> None:
    init_db()
    conn = _connect()
    conn.execute("DELETE FROM decision_logs")
    conn.execute("DELETE FROM purchase_orders")
    conn.execute("DELETE FROM recommendations")
    _seed_suppliers(conn)
    _seed_materials(conn)
    _seed_production_jobs(conn)
    conn.commit()
    conn.close()


def list_production_jobs(status: str | None = None) -> list[dict]:
    init_db()
    conn = _connect()
    if status:
        rows = conn.execute(
            "SELECT * FROM production_jobs WHERE status = ? ORDER BY sequence ASC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM production_jobs ORDER BY sequence ASC").fetchall()
    conn.close()
    return [_job_with_material_risk(dict(row)) for row in rows]


def get_production_job(job_id: str) -> dict | None:
    init_db()
    conn = _connect()
    row = conn.execute("SELECT * FROM production_jobs WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    return _job_with_material_risk(dict(row)) if row else None


def update_production_job(job: dict) -> dict:
    init_db()
    job["updated_at"] = _now()
    conn = _connect()
    conn.execute(
        """UPDATE production_jobs
           SET product = ?, sku_id = ?, line_id = ?, planned_units = ?, priority = ?,
               sequence = ?, status = ?, required_start = ?, estimated_duration_min = ?,
               updated_at = ?
           WHERE job_id = ?""",
        (
            job["product"],
            job["sku_id"],
            job["line_id"],
            job["planned_units"],
            job["priority"],
            job["sequence"],
            job["status"],
            job["required_start"],
            job["estimated_duration_min"],
            job["updated_at"],
            job["job_id"],
        ),
    )
    conn.commit()
    conn.close()
    return _job_with_material_risk(job)


def update_production_jobs(jobs: list[dict]) -> list[dict]:
    return [update_production_job(job) for job in jobs]


def list_materials(status: str | None = None) -> list[dict]:
    init_db()
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM materials WHERE active = 1 ORDER BY criticality ASC, sku_id ASC"
    ).fetchall()
    conn.close()
    materials = [_material_with_risk(dict(row)) for row in rows]
    if status:
        materials = [material for material in materials if material["risk_status"] == status]
    return materials


def get_material(sku_id: str) -> dict | None:
    init_db()
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM materials WHERE sku_id = ? AND active = 1",
        (sku_id,),
    ).fetchone()
    conn.close()
    return _material_with_risk(dict(row)) if row else None


def save_material(material: dict) -> dict:
    init_db()
    now = _now()
    existing = get_material(material["sku_id"])
    created_at = existing["created_at"] if existing else now
    material["active"] = material.get("active", True)
    material["created_at"] = created_at
    material["updated_at"] = now

    conn = _connect()
    conn.execute(
        """INSERT INTO materials
           (sku_id, name, line_id, warehouse, current_stock_units, reorder_point_units,
            daily_demand_units, unit_cost_mxn, criticality, active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(sku_id) DO UPDATE SET
             name = excluded.name,
             line_id = excluded.line_id,
             warehouse = excluded.warehouse,
             current_stock_units = excluded.current_stock_units,
             reorder_point_units = excluded.reorder_point_units,
             daily_demand_units = excluded.daily_demand_units,
             unit_cost_mxn = excluded.unit_cost_mxn,
             criticality = excluded.criticality,
             active = excluded.active,
             updated_at = excluded.updated_at""",
        (
            material["sku_id"],
            material["name"],
            material["line_id"],
            material["warehouse"],
            material["current_stock_units"],
            material["reorder_point_units"],
            material["daily_demand_units"],
            material["unit_cost_mxn"],
            material["criticality"],
            1 if material.get("active", True) else 0,
            material["created_at"],
            material["updated_at"],
        ),
    )
    conn.commit()
    conn.close()
    return _material_with_risk(material)


def list_suppliers(sku_id: str | None = None) -> list[dict]:
    init_db()
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM suppliers WHERE active = 1 ORDER BY lead_time_days ASC, unit_cost_mxn ASC"
    ).fetchall()
    conn.close()
    suppliers = [_supplier_from_row(row) for row in rows]
    if sku_id:
        suppliers = [supplier for supplier in suppliers if sku_id in supplier["sku_ids"]]
    return suppliers


def get_supplier(supplier_id: str, sku_id: str | None = None) -> dict | None:
    init_db()
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM suppliers WHERE supplier_id = ? AND active = 1",
        (supplier_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    supplier = _supplier_from_row(row)
    if sku_id and sku_id not in supplier["sku_ids"]:
        return None
    return supplier


def save_supplier(supplier: dict) -> dict:
    init_db()
    now = _now()
    existing = get_supplier(supplier["supplier_id"])
    created_at = existing["created_at"] if existing else now
    supplier["active"] = supplier.get("active", True)
    supplier["created_at"] = created_at
    supplier["updated_at"] = now

    conn = _connect()
    conn.execute(
        """INSERT INTO suppliers
           (supplier_id, name, sku_ids_json, lead_time_days, unit_cost_mxn,
            reliability_score, minimum_order_quantity, active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(supplier_id) DO UPDATE SET
             name = excluded.name,
             sku_ids_json = excluded.sku_ids_json,
             lead_time_days = excluded.lead_time_days,
             unit_cost_mxn = excluded.unit_cost_mxn,
             reliability_score = excluded.reliability_score,
             minimum_order_quantity = excluded.minimum_order_quantity,
             active = excluded.active,
             updated_at = excluded.updated_at""",
        (
            supplier["supplier_id"],
            supplier["name"],
            json.dumps(supplier["sku_ids"]),
            supplier["lead_time_days"],
            supplier["unit_cost_mxn"],
            supplier["reliability_score"],
            supplier["minimum_order_quantity"],
            1 if supplier.get("active", True) else 0,
            supplier["created_at"],
            supplier["updated_at"],
        ),
    )
    conn.commit()
    conn.close()
    return supplier


def deactivate_supplier(supplier_id: str) -> bool:
    init_db()
    conn = _connect()
    cursor = conn.execute(
        "UPDATE suppliers SET active = 0, updated_at = ? WHERE supplier_id = ? AND active = 1",
        (_now(), supplier_id),
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def insert_recommendation(recommendation: dict) -> dict:
    init_db()
    conn = _connect()
    conn.execute(
        """INSERT INTO recommendations
           (recommendation_id, type, priority, status, sku_id, line_id, reason,
            recommended_action, alternative_actions_json, estimated_impact_mxn,
            risk_score, source_event_id, correlation_id, created_at, decided_at,
            decided_by, decision_comment, purchase_order_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        _recommendation_values(recommendation),
    )
    conn.commit()
    conn.close()
    return recommendation


def get_recommendation(recommendation_id: str) -> dict | None:
    init_db()
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM recommendations WHERE recommendation_id = ?",
        (recommendation_id,),
    ).fetchone()
    conn.close()
    return _recommendation_from_row(row) if row else None


def get_recommendation_by_correlation_type(correlation_id: str, recommendation_type: str) -> dict | None:
    init_db()
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM recommendations WHERE correlation_id = ? AND type = ?",
        (correlation_id, recommendation_type),
    ).fetchone()
    conn.close()
    return _recommendation_from_row(row) if row else None


def list_recommendations(status: str | None = None) -> list[dict]:
    init_db()
    conn = _connect()
    if status:
        rows = conn.execute(
            "SELECT * FROM recommendations WHERE status = ? ORDER BY created_at DESC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM recommendations ORDER BY created_at DESC").fetchall()
    conn.close()
    return [_recommendation_from_row(row) for row in rows]


def update_recommendation(recommendation: dict) -> dict:
    init_db()
    conn = _connect()
    conn.execute(
        """UPDATE recommendations
           SET type = ?, priority = ?, status = ?, sku_id = ?, line_id = ?,
               reason = ?, recommended_action = ?, alternative_actions_json = ?,
               estimated_impact_mxn = ?, risk_score = ?, source_event_id = ?,
               correlation_id = ?, created_at = ?, decided_at = ?, decided_by = ?,
               decision_comment = ?, purchase_order_id = ?
           WHERE recommendation_id = ?""",
        (
            recommendation["type"],
            recommendation["priority"],
            recommendation["status"],
            recommendation["sku_id"],
            recommendation["line_id"],
            recommendation["reason"],
            recommendation["recommended_action"],
            json.dumps(recommendation["alternative_actions"]),
            recommendation["estimated_impact_mxn"],
            recommendation["risk_score"],
            recommendation["source_event_id"],
            recommendation["correlation_id"],
            recommendation["created_at"],
            recommendation.get("decided_at"),
            recommendation.get("decided_by"),
            recommendation.get("decision_comment"),
            recommendation.get("purchase_order_id"),
            recommendation["recommendation_id"],
        ),
    )
    conn.commit()
    conn.close()
    return recommendation


def insert_decision_log(decision: dict) -> dict:
    init_db()
    conn = _connect()
    conn.execute(
        """INSERT INTO decision_logs
           (decision_id, recommendation_id, action, user, comment, correlation_id, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            decision["decision_id"],
            decision["recommendation_id"],
            decision["action"],
            decision["user"],
            decision.get("comment"),
            decision["correlation_id"],
            decision["timestamp"],
        ),
    )
    conn.commit()
    conn.close()
    return decision


def list_decision_logs() -> list[dict]:
    init_db()
    conn = _connect()
    rows = conn.execute("SELECT * FROM decision_logs ORDER BY timestamp DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_audit_records(
    entity_type: str | None = None,
    entity_id: str | None = None,
    sku_id: str | None = None,
    correlation_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    init_db()
    records = []
    records.extend(_audit_decisions(entity_id, sku_id, correlation_id))
    records.extend(_audit_recommendations(entity_id, sku_id, correlation_id))
    records.extend(_audit_purchase_orders(entity_id, sku_id, correlation_id))
    records.extend(_audit_events(entity_id, sku_id, correlation_id))
    if entity_type:
        records = [record for record in records if record["entity_type"] == entity_type]
    records = sorted(records, key=lambda record: record["timestamp"], reverse=True)
    return records[:limit]


def audit_records_to_csv(records: list[dict]) -> str:
    output = StringIO()
    columns = [
        "timestamp",
        "source",
        "entity_type",
        "entity_id",
        "action",
        "status",
        "sku_id",
        "correlation_id",
        "user",
        "summary",
    ]
    writer = DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()


def insert_purchase_order(order: dict) -> dict:
    init_db()
    conn = _connect()
    conn.execute(
        """INSERT INTO purchase_orders
           (po_id, sku_id, line_id, supplier_id, supplier_name, supplier_lead_time_days,
            quantity_units, unit_cost_mxn, total_cost_mxn, required_date,
            estimated_arrival_date, status, created_by, created_at, updated_at,
            approved_by, approved_at, source_recommendation_id, correlation_id, pa_comment)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        _purchase_order_values(order),
    )
    conn.commit()
    conn.close()
    return order


def get_purchase_order(po_id: str) -> dict | None:
    init_db()
    conn = _connect()
    row = conn.execute("SELECT * FROM purchase_orders WHERE po_id = ?", (po_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_purchase_order_by_recommendation(recommendation_id: str) -> dict | None:
    init_db()
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM purchase_orders WHERE source_recommendation_id = ?",
        (recommendation_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_purchase_orders(status: str | None = None) -> list[dict]:
    init_db()
    conn = _connect()
    if status:
        rows = conn.execute(
            "SELECT * FROM purchase_orders WHERE status = ? ORDER BY created_at DESC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM purchase_orders ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_purchase_order(order: dict) -> dict:
    init_db()
    conn = _connect()
    conn.execute(
        """UPDATE purchase_orders
           SET sku_id = ?, line_id = ?, supplier_id = ?, supplier_name = ?,
               supplier_lead_time_days = ?, quantity_units = ?, unit_cost_mxn = ?,
               total_cost_mxn = ?, required_date = ?, estimated_arrival_date = ?,
               status = ?, created_by = ?, created_at = ?, updated_at = ?,
               approved_by = ?, approved_at = ?, source_recommendation_id = ?,
               correlation_id = ?, pa_comment = ?
           WHERE po_id = ?""",
        (
            order["sku_id"],
            order["line_id"],
            order["supplier_id"],
            order["supplier_name"],
            order["supplier_lead_time_days"],
            order["quantity_units"],
            order["unit_cost_mxn"],
            order["total_cost_mxn"],
            order["required_date"],
            order["estimated_arrival_date"],
            order["status"],
            order["created_by"],
            order["created_at"],
            order["updated_at"],
            order.get("approved_by"),
            order.get("approved_at"),
            order["source_recommendation_id"],
            order["correlation_id"],
            order.get("pa_comment"),
            order["po_id"],
        ),
    )
    conn.commit()
    conn.close()
    return order


def _supplier_from_row(row: sqlite3.Row) -> dict:
    supplier = dict(row)
    supplier["sku_ids"] = json.loads(supplier.pop("sku_ids_json"))
    supplier["active"] = bool(supplier["active"])
    return supplier


def _audit_decisions(entity_id: str | None, sku_id: str | None, correlation_id: str | None) -> list[dict]:
    conn = _connect()
    conditions = []
    params = []
    if entity_id:
        conditions.append("recommendation_id = ?")
        params.append(entity_id)
    if correlation_id:
        conditions.append("correlation_id = ?")
        params.append(correlation_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = conn.execute(f"SELECT * FROM decision_logs {where}", params).fetchall()
    conn.close()
    records = []
    for row in rows:
        decision = dict(row)
        recommendation = get_recommendation(decision["recommendation_id"])
        if sku_id and (not recommendation or recommendation["sku_id"] != sku_id):
            continue
        records.append({
            "timestamp": decision["timestamp"],
            "source": "decision_log",
            "entity_type": "recommendation",
            "entity_id": decision["recommendation_id"],
            "action": decision["action"],
            "status": decision["action"],
            "sku_id": recommendation["sku_id"] if recommendation else None,
            "correlation_id": decision["correlation_id"],
            "user": decision["user"],
            "summary": decision.get("comment") or f"Recommendation {decision['action']}",
            "details": decision,
        })
    return records


def _audit_recommendations(entity_id: str | None, sku_id: str | None, correlation_id: str | None) -> list[dict]:
    conditions = []
    params = []
    if entity_id:
        conditions.append("recommendation_id = ?")
        params.append(entity_id)
    if sku_id:
        conditions.append("sku_id = ?")
        params.append(sku_id)
    if correlation_id:
        conditions.append("correlation_id = ?")
        params.append(correlation_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    conn = _connect()
    rows = conn.execute(f"SELECT * FROM recommendations {where}", params).fetchall()
    conn.close()
    return [
        {
            "timestamp": row["created_at"],
            "source": "recommendations",
            "entity_type": "recommendation",
            "entity_id": row["recommendation_id"],
            "action": "created",
            "status": row["status"],
            "sku_id": row["sku_id"],
            "correlation_id": row["correlation_id"],
            "user": row["decided_by"],
            "summary": row["recommended_action"],
            "details": _recommendation_from_row(row),
        }
        for row in rows
    ]


def _audit_purchase_orders(entity_id: str | None, sku_id: str | None, correlation_id: str | None) -> list[dict]:
    conditions = []
    params = []
    if entity_id:
        conditions.append("po_id = ?")
        params.append(entity_id)
    if sku_id:
        conditions.append("sku_id = ?")
        params.append(sku_id)
    if correlation_id:
        conditions.append("correlation_id = ?")
        params.append(correlation_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    conn = _connect()
    rows = conn.execute(f"SELECT * FROM purchase_orders {where}", params).fetchall()
    conn.close()
    return [
        {
            "timestamp": row["updated_at"],
            "source": "purchase_orders",
            "entity_type": "purchase_order",
            "entity_id": row["po_id"],
            "action": "updated" if row["status"] != "draft" else "created",
            "status": row["status"],
            "sku_id": row["sku_id"],
            "correlation_id": row["correlation_id"],
            "user": row["approved_by"] or row["created_by"],
            "summary": f"{row['quantity_units']} uds con {row['supplier_name']}",
            "details": dict(row),
        }
        for row in rows
    ]


def _audit_events(entity_id: str | None, sku_id: str | None, correlation_id: str | None) -> list[dict]:
    conditions = []
    params = []
    if entity_id:
        conditions.append("(event_id = ? OR asset_id = ?)")
        params.extend([entity_id, entity_id])
    if sku_id:
        conditions.append("asset_id = ?")
        params.append(sku_id)
    if correlation_id:
        conditions.append("correlation_id = ?")
        params.append(correlation_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    conn = _connect()
    rows = conn.execute(
        f"SELECT event_json FROM events {where} ORDER BY timestamp DESC",
        params,
    ).fetchall()
    conn.close()
    records = []
    for row in rows:
        event = json.loads(row["event_json"])
        records.append({
            "timestamp": event["timestamp"],
            "source": "ies_event",
            "entity_type": "event",
            "entity_id": event["event_id"],
            "action": event["event"]["type"],
            "status": event["event"]["severity"],
            "sku_id": event["asset"]["asset_id"],
            "correlation_id": event["metadata"].get("correlation_id"),
            "user": event["data"].get("decided_by") or event["data"].get("applied_by"),
            "summary": event["event"]["type"],
            "details": event,
        })
    return records


def _material_with_risk(material: dict) -> dict:
    daily_demand = material["daily_demand_units"]
    current_stock = material["current_stock_units"]
    reorder_point = material["reorder_point_units"]
    stockout_hours = round(current_stock / (daily_demand / 24), 1) if daily_demand > 0 else None
    shortage_units = max(0, reorder_point - current_stock)
    risk_score = min(100, round((shortage_units / max(reorder_point, 1)) * 100 + _criticality_bonus(material["criticality"]), 1))
    if current_stock <= reorder_point * 0.5 or risk_score >= 75:
        risk_status = "critical"
    elif current_stock < reorder_point or risk_score >= 35:
        risk_status = "low_stock"
    else:
        risk_status = "normal"
    material["stockout_hours"] = stockout_hours
    material["shortage_units"] = shortage_units
    material["risk_score"] = risk_score
    material["risk_status"] = risk_status
    material["estimated_impact_mxn"] = round(shortage_units * material["unit_cost_mxn"], 2)
    material["active"] = bool(material["active"])
    return material


def _job_with_material_risk(job: dict) -> dict:
    material = get_material(job["sku_id"])
    if material:
        job["material_risk_status"] = material["risk_status"]
        job["material_risk_score"] = material["risk_score"]
        job["stockout_hours"] = material["stockout_hours"]
        job["shortage_units"] = material["shortage_units"]
        job["estimated_impact_mxn"] = material["estimated_impact_mxn"]
    else:
        job["material_risk_status"] = "unknown"
        job["material_risk_score"] = 0
        job["stockout_hours"] = None
        job["shortage_units"] = 0
        job["estimated_impact_mxn"] = 0
    if job["material_risk_status"] == "critical":
        job["suggested_action"] = "defer_or_expedite_material"
    elif job["material_risk_status"] == "low_stock":
        job["suggested_action"] = "monitor_and_prepare_po"
    else:
        job["suggested_action"] = "run_as_planned"
    return job


def _criticality_bonus(criticality: str) -> int:
    return {"critical": 25, "high": 15, "medium": 5}.get(criticality, 0)


def _recommendation_values(recommendation: dict) -> tuple:
    return (
        recommendation["recommendation_id"],
        recommendation["type"],
        recommendation["priority"],
        recommendation["status"],
        recommendation["sku_id"],
        recommendation["line_id"],
        recommendation["reason"],
        recommendation["recommended_action"],
        json.dumps(recommendation["alternative_actions"]),
        recommendation["estimated_impact_mxn"],
        recommendation["risk_score"],
        recommendation["source_event_id"],
        recommendation["correlation_id"],
        recommendation["created_at"],
        recommendation.get("decided_at"),
        recommendation.get("decided_by"),
        recommendation.get("decision_comment"),
        recommendation.get("purchase_order_id"),
    )


def _recommendation_from_row(row: sqlite3.Row) -> dict:
    recommendation = dict(row)
    recommendation["alternative_actions"] = json.loads(recommendation.pop("alternative_actions_json"))
    return recommendation


def _purchase_order_values(order: dict) -> tuple:
    return (
        order["po_id"],
        order["sku_id"],
        order["line_id"],
        order["supplier_id"],
        order["supplier_name"],
        order["supplier_lead_time_days"],
        order["quantity_units"],
        order["unit_cost_mxn"],
        order["total_cost_mxn"],
        order["required_date"],
        order["estimated_arrival_date"],
        order["status"],
        order["created_by"],
        order["created_at"],
        order["updated_at"],
        order.get("approved_by"),
        order.get("approved_at"),
        order["source_recommendation_id"],
        order["correlation_id"],
        order.get("pa_comment"),
    )
