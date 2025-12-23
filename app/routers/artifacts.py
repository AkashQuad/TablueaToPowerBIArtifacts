from fastapi import APIRouter, HTTPException
from app.services.artifact_generator import generate_pbi_artifacts
from app.storage.blob import download_file
from pathlib import Path
import tempfile
import json

router = APIRouter()

@router.post("/generate")
def generate_artifacts_api(payload: dict):

    report_id = payload.get("report_id")
    if not report_id:
        raise HTTPException(400, "report_id required")

    # 🔑 Canonical blob paths (server-owned)
    parsed_blob = f"artifacts/parsed/{report_id}_parsed_meta.json"
    source_blob = f"artifacts/sources/{report_id}_source.json"

    tmp_dir = Path(tempfile.mkdtemp())
    parsed_local = tmp_dir / "parsed.json"
    source_local = tmp_dir / "source.json"

    try:
        download_file(parsed_blob, parsed_local)
        download_file(source_blob, source_local)
    except Exception:
        raise HTTPException(
            404,
            "Parsed metadata or source configuration not found. "
            "Ensure /tableau/parse and /source/configure were executed."
        )

    with open(source_local, "r") as f:
        source_data = json.load(f)

    artifact_urls = generate_pbi_artifacts(
        parsed_meta_path=str(parsed_local),
        report_id=report_id,
        source_type=source_data["source_type"],
        source_config=source_data["source_config"],
    )

    return {
        "status": "generated",
        "artifacts": artifact_urls
    }
