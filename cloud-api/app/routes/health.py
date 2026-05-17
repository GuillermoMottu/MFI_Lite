from fastapi import APIRouter
import state as app_state

router = APIRouter(tags=["Health"])


@router.get("/health")
@router.get("/api/health")
def health():
    return {"status": "ok", "service": "materialflow-intelligence-cloud-api", "version": "1.0.0"}


@router.get("/")
def root():
    return {
        "project": "MaterialFlow Intelligence Lite",
        "platform": "IES v2.0",
        "agents": ["erp_gestion_empresarial", "produccion_avanzada", "ai_ml_industrial"],
        "plant": "PLT-JUAREZ-01",
        "docs": "/docs",
    }
