from fastapi import APIRouter
from app.models.requests import SourceConfigRequest
from app.services.source_store import save_source_config

router = APIRouter()

@router.post("/configure")
def configure_source(req: SourceConfigRequest):
    path = save_source_config(
        req.report_id,
        req.source_type,
        req.source_config
    )
    return {
        "status": "saved",
        "path": str(path)
    }
