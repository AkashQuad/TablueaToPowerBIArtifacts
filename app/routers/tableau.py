from fastapi import APIRouter, UploadFile, File
from app.services.tableau_parser import parse_tableau_file
from app.config import UPLOAD_DIR

router = APIRouter()


@router.post("/parse")
async def parse_tableau(
    file: UploadFile = File(...),
    report_id: str = "Report1"
):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    input_path = UPLOAD_DIR / file.filename
    with open(input_path, "wb") as f:
        f.write(await file.read())

    parsed_meta_path = parse_tableau_file(
        input_path=str(input_path),
        report_id=report_id
    )

    return {
        "reportId": report_id,
        "parsedMetaPath": str(parsed_meta_path)
    }
