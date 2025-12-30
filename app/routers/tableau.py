from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from pathlib import Path
import httpx
import uuid

from app.services.tableau_parser import parse_tableau_file
from app.config import UPLOAD_DIR

router = APIRouter()


# -----------------------------
# Request Schema
# -----------------------------
class ParseTableauRequest(BaseModel):
    blobUrl: HttpUrl


@router.post("/parse")
async def parse_tableau(
    payload: ParseTableauRequest,
    report_id: str = Query(
        ...,
        description="Migration job identifier (UUID or logical report id)"
    ),
):
    """
    Production-grade Tableau parsing endpoint.

    - Backend pulls file from Azure Blob
    - Frontend never uploads binaries
    - Deterministic artifact paths
    """

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # Download Tableau file
    # -----------------------------
    suffix = Path(payload.blobUrl.path).suffix
    if suffix not in {".twb", ".twbx"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid Tableau file type"
        )

    local_path = UPLOAD_DIR / f"{uuid.uuid4()}{suffix}"

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(str(payload.blobUrl))
            response.raise_for_status()
    except Exception as ex:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to download Tableau file: {str(ex)}"
        )

    with open(local_path, "wb") as f:
        f.write(response.content)

    # -----------------------------
    # Parse & Upload Metadata
    # -----------------------------
    try:
        parsed_blob_url = parse_tableau_file(
            local_path=str(local_path),
            report_id=report_id,
        )
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Tableau parsing failed: {str(ex)}"
        )

    return {
        "reportId": report_id,
        "parsedMetaUrl": parsed_blob_url,
    }
