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
app.include_router(events_router)
app.include_router(demo_router)
app.include_router(erp_router)
app.include_router(production_router)
app.include_router(aiml_router)
app.include_router(offline_router)
