import os
import sys
import unittest

from fastapi.testclient import TestClient

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from auth.tokens import clear_all_tokens  # noqa: E402
from main import app  # noqa: E402


class OperationalFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        clear_all_tokens()
        self.pa_headers = self._login_headers("carlos", "demo123")
        self.supervisor_headers = self._login_headers("maria", "demo123")
        self.admin_headers = self._login_headers("admin", "admin123")
        response = self.client.post("/api/demo/reset", headers=self.admin_headers)
        self.assertEqual(response.status_code, 200)

    def tearDown(self) -> None:
        self.client.post("/api/demo/reset", headers=self.admin_headers)
        self.client.close()
        clear_all_tokens()

    def _login_headers(self, username: str, password: str) -> dict:
        response = self.client.post("/api/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200)
        return {"Authorization": f"Bearer {response.json()['token']}"}

    def test_auth_login_returns_token_and_user(self) -> None:
        response = self.client.post("/api/auth/login", json={"username": "carlos", "password": "demo123"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("token", body)
        self.assertEqual(body["user"]["display_name"], "Carlos Mendoza")
        self.assertEqual(body["user"]["role"], "pa")

    def test_auth_rejects_invalid_credentials(self) -> None:
        response = self.client.post("/api/auth/login", json={"username": "carlos", "password": "bad"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def test_auth_me_returns_current_user(self) -> None:
        response = self.client.get("/api/auth/me", headers=self.supervisor_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["display_name"], "María Torres")
        self.assertEqual(response.json()["user"]["role"], "supervisor")

    def test_protected_endpoint_requires_token(self) -> None:
        response = self.client.get("/api/recommendations/active")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def test_protected_endpoint_rejects_insufficient_role(self) -> None:
        response = self.client.post("/api/demo/reset", headers=self.pa_headers)
        self.assertEqual(response.status_code, 403)
        audit_response = self.client.get("/api/audit/export?format=json", headers=self.pa_headers)
        self.assertEqual(audit_response.status_code, 403)

    def test_recommendation_approval_creates_editable_approvable_purchase_order(self) -> None:
        demo_response = self.client.post("/api/demo/run", headers=self.pa_headers)
        self.assertEqual(demo_response.status_code, 200)

        active_response = self.client.get("/api/recommendations/active", headers=self.pa_headers)
        self.assertEqual(active_response.status_code, 200)
        recommendation = active_response.json()["recommendation"]
        self.assertIsNotNone(recommendation)

        approve_response = self.client.post(
            f"/api/recommendations/{recommendation['recommendation_id']}/approve",
            json={"comment": "Aprobar compra urgente"},
            headers=self.pa_headers,
        )
        self.assertEqual(approve_response.status_code, 200)
        approved_recommendation = approve_response.json()["recommendation"]
        self.assertEqual(approved_recommendation["status"], "approved")
        self.assertEqual(approved_recommendation["decided_by"], "Carlos Mendoza")
        self.assertIsNotNone(approved_recommendation["purchase_order_id"])

        duplicate_response = self.client.post(
            f"/api/recommendations/{recommendation['recommendation_id']}/approve",
            json={},
            headers=self.pa_headers,
        )
        self.assertEqual(duplicate_response.status_code, 409)

        orders_response = self.client.get("/api/purchase-orders/", headers=self.pa_headers)
        self.assertEqual(orders_response.status_code, 200)
        orders = orders_response.json()["purchase_orders"]
        self.assertEqual(len(orders), 1)
        order = orders[0]
        self.assertEqual(order["status"], "draft")

        update_response = self.client.patch(
            f"/api/purchase-orders/{order['po_id']}",
            json={"quantity_units": order["quantity_units"] + 100, "comment": "Subir cobertura"},
            headers=self.pa_headers,
        )
        self.assertEqual(update_response.status_code, 200)
        updated_order = update_response.json()["purchase_order"]
        self.assertEqual(updated_order["quantity_units"], order["quantity_units"] + 100)
        self.assertGreater(updated_order["total_cost_mxn"], order["total_cost_mxn"])

        po_approve_response = self.client.post(
            f"/api/purchase-orders/{order['po_id']}/approve",
            json={"comment": "Orden lista"},
            headers=self.pa_headers,
        )
        self.assertEqual(po_approve_response.status_code, 200)
        approved_order = po_approve_response.json()["purchase_order"]
        self.assertEqual(approved_order["status"], "approved")
        self.assertEqual(approved_order["approved_by"], "Carlos Mendoza")

        locked_update_response = self.client.patch(
            f"/api/purchase-orders/{order['po_id']}",
            json={"quantity_units": updated_order["quantity_units"] + 1},
            headers=self.pa_headers,
        )
        self.assertEqual(locked_update_response.status_code, 409)

    def test_supplier_catalog_crud_and_recommendation(self) -> None:
        self.client.delete("/api/suppliers/SUP-TEST-COSTO")
        create_response = self.client.post(
            "/api/suppliers/",
            json={
                "supplier_id": "SUP-TEST-COSTO",
                "name": "Proveedor Costo Test",
                "sku_ids": ["SKU-ACERO-M8"],
                "lead_time_days": 6,
                "unit_cost_mxn": 24.5,
                "reliability_score": 0.86,
                "minimum_order_quantity": 400,
            },
        )
        self.assertEqual(create_response.status_code, 200)

        recommended_response = self.client.get("/api/suppliers/recommended?sku_id=SKU-ACERO-M8&strategy=cost")
        self.assertEqual(recommended_response.status_code, 200)
        self.assertEqual(recommended_response.json()["supplier"]["supplier_id"], "SUP-TEST-COSTO")

        update_response = self.client.patch(
            "/api/suppliers/SUP-TEST-COSTO",
            json={"lead_time_days": 3, "reliability_score": 0.9},
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["supplier"]["lead_time_days"], 3)

        delete_response = self.client.delete("/api/suppliers/SUP-TEST-COSTO")
        self.assertEqual(delete_response.status_code, 200)

        get_response = self.client.get("/api/suppliers/SUP-TEST-COSTO")
        self.assertEqual(get_response.status_code, 404)

    def test_inventory_lists_multi_sku_and_generates_sku_recommendation(self) -> None:
        materials_response = self.client.get("/api/materials/")
        self.assertEqual(materials_response.status_code, 200)
        self.assertGreaterEqual(len(materials_response.json()["materials"]), 3)

        critical_response = self.client.get("/api/materials/?status=critical")
        self.assertEqual(critical_response.status_code, 200)
        critical_skus = {material["sku_id"] for material in critical_response.json()["materials"]}
        self.assertIn("SKU-ACERO-M8", critical_skus)

        update_response = self.client.patch("/api/materials/SKU-RESINA-P22", json={"current_stock_units": 120})
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["material"]["risk_status"], "critical")

        recommendation_response = self.client.post("/api/materials/SKU-RESINA-P22/recommendation")
        self.assertEqual(recommendation_response.status_code, 200)
        recommendation = recommendation_response.json()["recommendation"]
        self.assertEqual(recommendation["sku_id"], "SKU-RESINA-P22")

        approve_response = self.client.post(
            f"/api/recommendations/{recommendation['recommendation_id']}/approve",
            json={"comment": "Cubrir resina"},
            headers=self.pa_headers,
        )
        self.assertEqual(approve_response.status_code, 200)

        orders_response = self.client.get("/api/purchase-orders/", headers=self.pa_headers)
        self.assertEqual(orders_response.status_code, 200)
        self.assertTrue(any(order["sku_id"] == "SKU-RESINA-P22" for order in orders_response.json()["purchase_orders"]))

        self.client.patch("/api/materials/SKU-RESINA-P22", json={"current_stock_units": 460})

    def test_production_backlog_suggests_and_applies_resequence(self) -> None:
        backlog_response = self.client.get("/api/production/backlog")
        self.assertEqual(backlog_response.status_code, 200)
        jobs = backlog_response.json()["jobs"]
        self.assertGreaterEqual(len(jobs), 3)
        self.assertTrue(any(job["material_risk_status"] == "critical" for job in jobs))

        suggestion_response = self.client.get("/api/production/backlog/suggestion")
        self.assertEqual(suggestion_response.status_code, 200)
        self.assertEqual(suggestion_response.json()["strategy"], "material_availability_first")
        self.assertGreaterEqual(suggestion_response.json()["summary"]["jobs_impacted"], 1)

        resequence_response = self.client.post(
            "/api/production/backlog/resequence",
            json={"user": "PA-TEST", "comment": "Priorizar jobs con material disponible"},
        )
        self.assertEqual(resequence_response.status_code, 200)
        self.assertEqual(resequence_response.json()["event"]["event"]["type"], "production_backlog_resequenced")

        updated_response = self.client.get("/api/production/backlog")
        self.assertEqual(updated_response.status_code, 200)
        critical_jobs = [
            job for job in updated_response.json()["jobs"]
            if job["material_risk_status"] == "critical"
        ]
        self.assertTrue(all(job["status"] == "material_hold" for job in critical_jobs))

    def test_audit_trail_filters_and_exports_operational_history(self) -> None:
        demo_response = self.client.post("/api/demo/run", headers=self.pa_headers)
        self.assertEqual(demo_response.status_code, 200)
        correlation_id = demo_response.json()["correlation_id"]

        active_response = self.client.get("/api/recommendations/active", headers=self.pa_headers)
        recommendation = active_response.json()["recommendation"]
        self.assertIsNotNone(recommendation)

        approve_response = self.client.post(
            f"/api/recommendations/{recommendation['recommendation_id']}/approve",
            json={"comment": "Auditar decision"},
            headers=self.pa_headers,
        )
        self.assertEqual(approve_response.status_code, 200)

        audit_response = self.client.get(f"/api/audit/?correlation_id={correlation_id}", headers=self.pa_headers)
        self.assertEqual(audit_response.status_code, 200)
        audit = audit_response.json()["audit"]
        self.assertTrue(any(record["entity_type"] == "recommendation" for record in audit))
        self.assertTrue(any(record["entity_type"] == "purchase_order" for record in audit))
        self.assertTrue(any(record["entity_type"] == "event" for record in audit))
        self.assertTrue(any(record["user"] == "Carlos Mendoza" for record in audit if record["entity_type"] == "recommendation"))

        sku_audit_response = self.client.get(
            "/api/audit/?sku_id=SKU-ACERO-M8&entity_type=purchase_order",
            headers=self.pa_headers,
        )
        self.assertEqual(sku_audit_response.status_code, 200)
        self.assertTrue(all(record["sku_id"] == "SKU-ACERO-M8" for record in sku_audit_response.json()["audit"]))

        csv_response = self.client.get(
            f"/api/audit/export?format=csv&correlation_id={correlation_id}",
            headers=self.supervisor_headers,
        )
        self.assertEqual(csv_response.status_code, 200)
        self.assertIn("text/csv", csv_response.headers["content-type"])
        self.assertIn("entity_type", csv_response.text)

        json_response = self.client.get(
            f"/api/audit/export?format=json&correlation_id={correlation_id}",
            headers=self.supervisor_headers,
        )
        self.assertEqual(json_response.status_code, 200)
        self.assertIn("application/json", json_response.headers["content-type"])
        self.assertIn("audit", json_response.json())


if __name__ == "__main__":
    unittest.main()
