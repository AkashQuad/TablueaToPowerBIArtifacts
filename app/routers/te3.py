from fastapi import APIRouter, HTTPException
from app.services.te3_generator import generate_te3_script

router = APIRouter()


@router.post("/generate")
def generate_te3_api(report_id: str):
    """
    Generate TE3 script from canonical ModelSpec,
    upload to Blob, return Blob URL.
    """

    # 🔑 Canonical ModelSpec location (server-owned)
    model_spec_path = f"artifacts/{report_id}/model/{report_id}_modelspec.json"

    try:
        blob_url = generate_te3_script(
            model_spec_path=model_spec_path,
            report_id=report_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"ModelSpec not found or TE3 generation failed: {str(e)}"
        )

    return {
        "status": "success",
        "reportId": report_id,
        "te3BlobUrl": blob_url
    }
