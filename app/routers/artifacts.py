from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

from app.services.artifact_generator import generate_pbi_artifacts
from app.config import PARSED_DIR, ARTIFACTS_DIR, SOURCES_DIR

router = APIRouter()

@router.post("/generate")
def generate_artifacts_api(payload: dict):
    report_id = payload.get("report_id")
    if not report_id:
        raise HTTPException(status_code=400, detail="report_id required")

    parsed_meta_path = PARSED_DIR / f"{report_id}_parsed_meta.json"
    if not parsed_meta_path.exists():
        raise HTTPException(status_code=404, detail="Parsed metadata not found")

    source_path = SOURCES_DIR / f"{report_id}_source.json"
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Source config not found")

    with open(source_path, "r", encoding="utf-8") as f:
        source_data = json.load(f)

    output_dir = ARTIFACTS_DIR / report_id

    generate_pbi_artifacts(
        parsed_meta_path=str(parsed_meta_path),
        output_dir=str(output_dir),
        source_type=source_data["source_type"],
        source_config=source_data["source_config"],
    )

    return {
        "status": "generated",
        "artifacts_dir": str(output_dir)
    }
