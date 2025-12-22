from fastapi import APIRouter, HTTPException
from app.services.artifact_generator import generate_pbi_artifacts
from app.storage.blob import download_file
import os
from pathlib import Path
import tempfile


router = APIRouter()


@router.post("/generate")
def generate_artifacts_api(payload: dict):

    report_id = payload.get("report_id")
    parsed_url = payload.get("parsedMetaUrl")
    source_url = payload.get("sourceConfigUrl")

    if not report_id:
        raise HTTPException(400, "report_id required")

    if not parsed_url or not source_url:
        raise HTTPException(400, "parsedMetaUrl & sourceConfigUrl required")


    # Download blob files temporarily on Azure tmp
    tmp_dir = Path(tempfile.mkdtemp())

    parsed_local = tmp_dir / "parsed.json"
    source_local = tmp_dir / "source.json"

    download_file(parsed_url, parsed_local)
    download_file(source_url, source_local)

    import json
    with open(source_local, "r") as f:
        source_data = json.load(f)

    # generate artifacts => returns list of blob URLs
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
