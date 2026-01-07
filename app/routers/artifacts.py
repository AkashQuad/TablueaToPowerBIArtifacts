from fastapi import APIRouter, HTTPException

from app.services.artifact_generator import generate_pbi_artifacts
from app.config import PARSED_DIR

router = APIRouter()


@router.post("/generate")
def generate_artifacts_api(payload: dict):
    """
    Generate Power BI artifacts from parsed Tableau metadata
    and store them in Azure Blob Storage.
    """

    report_id = payload.get("report_id")
    if not report_id:
        raise HTTPException(status_code=400, detail="report_id required")

    parsed_meta_path = PARSED_DIR / f"{report_id}_parsed_meta.json"
    if not parsed_meta_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Parsed metadata not found. Run /tableau/parse first."
        )

    try:
        artifact_urls = generate_pbi_artifacts(
            parsed_meta_path=str(parsed_meta_path),
            report_id=report_id,
        )
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Artifact generation failed: {str(ex)}"
        )

    return {
        "status": "generated",
        "reportId": report_id,
        "artifacts": artifact_urls,
    }
