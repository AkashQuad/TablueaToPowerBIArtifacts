from fastapi import APIRouter
from pathlib import Path
from app.services.te3_generator import generate_te3_script
from app.config import ARTIFACTS_ROOT

router = APIRouter()

@router.post("/generate")
def generate_te3(model_spec: str, template: str):
    output_dir = ARTIFACTS_ROOT / "te3"
    result = generate_te3_script(Path(model_spec), Path(template), output_dir)
    return {"result": result}
