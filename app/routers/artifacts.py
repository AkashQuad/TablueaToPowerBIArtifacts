from fastapi import APIRouter, HTTPException
from app.services.artifact_generator import generate_pbi_artifacts
from app.storage.blob import download_file
from pathlib import Path
import tempfile
import json

router = APIRouter()

def blob_path_from_url(url: str) -> str:
    return url.split(".net/", 1)[1]

@router.post("/generate")
def generate_artifacts_api(payload: dict):

    report_id = payload.get("report_id")
    parsed_url = payload.get("parsedMetaUrl")
    source_url = payload.get("sourceConfigUrl")

    if not report_id:
        raise HTTPException(400, "report_id required")

    if not parsed_url or not source_url:
        raise HTTPException(400, "parsedMetaUrl & sourceConfigUrl required")

    # Temp directory (Azure-safe)
    tmp_dir = Path(tempfile.mkdtemp())

    parsed_local = tmp_dir / "parsed.json"
    source_local = tmp_dir / "source.json"

    # ✅ FIX: convert URL → blob path
    download_file(blob_path_from_url(parsed_url), parsed_local)
    download_file(blob_path_from_url(source_url), source_local)

    with open(source_local, "r", encoding="utf-8") as f:
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
