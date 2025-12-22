from fastapi import APIRouter, UploadFile, File
from app.services.tableau_parser import parse_tableau_file
from app.config import UPLOAD_DIR

router = APIRouter()

@router.post("/parse")
async def parse_tableau(file: UploadFile = File(...), report_id: str = "Report1"):

    # Save uploaded Tableau file
    local_path = UPLOAD_DIR / file.filename
    with open(local_path, "wb") as f:
        f.write(await file.read())

    # Parse (returns blob URL on Azure)
    parsed_blob_url = parse_tableau_file(str(local_path), report_id)

    return {
        "reportId": report_id,
        "parsedMetaUrl": parsed_blob_url
    }
