from fastapi import APIRouter
from app.services.layout_generator import generate_report_layout

router = APIRouter()


@router.post("/generate")
def generate_report_layout(visual_spec: str, dataset: str, report_id: str):
    """
    Generate Power BI layout JSON and upload to blob.
    Returns blob URL.
    """

    blob_url = generate_report_layout(
        visual_spec_path=visual_spec,
        dataset_name=dataset,
        report_id=report_id
    )

    return {
        "status": "success",
        "reportId": report_id,
        "layoutBlobUrl": blob_url
    }
