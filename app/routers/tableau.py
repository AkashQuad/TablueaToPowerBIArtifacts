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
    report_id: str = Query(...),
    payload: ParseTableauRequest = Body(...),
):
    blob_url = str(payload.blobUrl)

    suffix = Path(blob_url).suffix.lower()
    if suffix not in {".twb", ".twbx"}:
        raise HTTPException(400, "Invalid Tableau file type")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    local_path = UPLOAD_DIR / f"{uuid.uuid4()}{suffix}"

    try:
        blob_client = BlobClient.from_blob_url(
            blob_url=blob_url,
            account_name=os.getenv("AZURE_STORAGE_ACCOUNT_NAME"),
            credential=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
        )

        with open(local_path, "wb") as f:
            f.write(blob_client.download_blob().readall())

    except Exception as ex:
        raise HTTPException(502, f"Blob download failed: {repr(ex)}")

    parsed_blob_url = parse_tableau_file(
        local_path=str(local_path),
        report_id=report_id,
    )

    return {
        "reportId": report_id,
        "parsedMetaUrl": parsed_blob_url,
    }
