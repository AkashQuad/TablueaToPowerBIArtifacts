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
    report_id: str = Query(
        ...,
        description="Migration job identifier (UUID or logical report id)"
    ),
    payload: ParseTableauRequest = Body(...),
):
    """
    Production-grade Tableau parsing endpoint.
    Backend pulls file from Azure Blob (private container safe).
    """

    blob_url = str(payload.blobUrl)  # ✅ FIX IS HERE

    print("PARSE CALLED:", report_id, blob_url)

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    suffix = Path(blob_url).suffix.lower()
    if suffix not in {".twb", ".twbx"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid Tableau file type"
        )

    local_path = UPLOAD_DIR / f"{uuid.uuid4()}{suffix}"

    try:
        blob_client = BlobClient.from_blob_url(
            blob_url=blob_url,
            credential=os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        )

        with open(local_path, "wb") as f:
            f.write(blob_client.download_blob().readall())

    except Exception as ex:
        raise HTTPException(
            status_code=502,
            detail=f"Blob download failed: {repr(ex)}"
        )

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
