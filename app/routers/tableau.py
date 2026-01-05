from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, HttpUrl
from pathlib import Path
import uuid
import os

from azure.storage.blob import BlobClient

from app.services.tableau_parser import parse_tableau_file
from app.config import UPLOAD_DIR

router = APIRouter()


class ParseTableauRequest(BaseModel):
    blobUrl: HttpUrl


@router.post("/parse")
async def parse_tableau(
    report_id: str = Query(..., description="Migration job identifier"),
    payload: ParseTableauRequest = Body(...),
):
    """
    Backend pulls Tableau file from PRIVATE Azure Blob.
    """

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    suffix = Path(payload.blobUrl.path).suffix.lower()
    if suffix not in {".twb", ".twbx"}:
        raise HTTPException(400, "Invalid Tableau file type")

    local_path = UPLOAD_DIR / f"{uuid.uuid4()}{suffix}"

    # ---- Download from Azure Blob (private) ----
    try:
        blob_client = BlobClient.from_blob_url(
            str(payload.blobUrl),
            credential=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
        )

        with open(local_path, "wb") as f:
            f.write(blob_client.download_blob().readall())

    except Exception as ex:
        raise HTTPException(
            status_code=502,
            detail=f"Blob download failed: {repr(ex)}"
        )

    # ---- Parse ----
    try:
        parsed_blob_url = parse_tableau_file(
            str(local_path),
            report_id,
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
