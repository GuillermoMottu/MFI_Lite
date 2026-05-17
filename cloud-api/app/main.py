import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.health import router as health_router
from routes.events import router as events_router
from routes.demo import router as demo_router
from routes.erp import router as erp_router
from routes.production import router as production_router
from routes.aiml import router as aiml_router
from routes.offline import router as offline_router
from routes.recommendations import router as recommendations_router
from routes.purchase_orders import router as purchase_orders_router
from routes.suppliers import router as suppliers_router
from routes.materials import router as materials_router
from routes.audit import router as audit_router
from routes.auth import router as auth_router
from services.operational_store import init_db as init_operational_db

app = FastAPI(
    title="MaterialFlow Intelligence Lite — IES v2.0",
    description="Plataforma de Coordinación Inteligente del Ciclo de Vida de Materiales en Producción.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(events_router)
app.include_router(demo_router)
app.include_router(erp_router)
app.include_router(production_router)
app.include_router(aiml_router)
app.include_router(offline_router)
app.include_router(recommendations_router)
app.include_router(purchase_orders_router)
app.include_router(suppliers_router)
app.include_router(materials_router)
app.include_router(audit_router)


@app.on_event("startup")
def startup() -> None:
    init_operational_db()
