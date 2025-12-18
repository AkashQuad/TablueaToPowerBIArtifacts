from fastapi import APIRouter
from pathlib import Path
from app.services.layout_generator import generate_layout
from app.config import ARTIFACTS_ROOT

router = APIRouter()

@router.post("/generate")
def generate_report_layout(visual_spec: str, dataset: str):
    out = ARTIFACTS_ROOT / "layout.json"
    generate_layout(Path(visual_spec), dataset, out)
    return {"layout": str(out)}
