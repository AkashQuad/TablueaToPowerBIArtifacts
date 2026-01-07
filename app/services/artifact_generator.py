import subprocess
from pathlib import Path
from typing import List

from app.config import ARTIFACTS_DIR, SCRIPTS_DIR
from app.storage.blob import upload_file


def generate_pbi_artifacts(
    parsed_meta_path: str,
    report_id: str,
) -> List[str]:
    """
    Generate Power BI artifacts and upload them to Azure Blob Storage.
    Returns Blob URLs.
    """

    # ----------------------------------
    # Local output directory
    # ----------------------------------
    output_dir = ARTIFACTS_DIR / report_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------------
    # Run generator script
    # ----------------------------------
    cmd = [
        "python",
        str(SCRIPTS_DIR / "generate_pbi_artifacts_prod.py"),
        "--input", parsed_meta_path,
        "--out", str(output_dir),
    ]

    subprocess.run(cmd, check=True)

    # ----------------------------------
    # Upload artifacts to Blob
    # ----------------------------------
    blob_urls: List[str] = []
    blob_root = f"artifacts/{report_id}/"

    for file_path in output_dir.rglob("*"):
        if file_path.is_file():
            blob_path = blob_root + file_path.relative_to(output_dir).as_posix()
            url = upload_file(file_path, blob_path)
            blob_urls.append(url)

    return blob_urls
