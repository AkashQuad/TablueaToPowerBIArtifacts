from fastapi import APIRouter
from app.services.te3_generator import generate_te3_script

router = APIRouter()


@router.post("/generate")
def generate_te3_api(model_spec: str, report_id: str):
    """
    Generate TE3 script, upload to Blob, return Blob URL.
    """

    blob_url = generate_te3_script(
        model_spec_path=model_spec,
        report_id=report_id
    )

    return {
        "status": "success",
        "reportId": report_id,
        "te3BlobUrl": blob_url
    }
