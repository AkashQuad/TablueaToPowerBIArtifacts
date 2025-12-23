import subprocess
import os
import json
from pathlib import Path

from app.storage.blob import upload_file
from app.config import ARTIFACTS_DIR, SCRIPTS_DIR


def generate_pbi_artifacts(
    parsed_meta_path: str,
    report_id: str,
    source_type: str,
    source_config: dict
):
    """
    Step 4:
    - Run artifact generator script
    - Upload generated artifacts to Azure Blob Storage (when on Azure)
    - Return list of artifact URLs or local paths
    """

    # --------------------------------------------------
    # Prepare output directory
    # --------------------------------------------------
    output_dir = ARTIFACTS_DIR / report_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # Run generator script
    # --------------------------------------------------
    cmd = [
        "python",
        str(SCRIPTS_DIR / "generate_pbi_artifacts_prod.py"),
        "--input", parsed_meta_path,
        "--out", str(output_dir),
        "--source-type", source_type,
        "--source-config", json.dumps(source_config),
    ]

    env = os.environ.copy() 
    env["REPORT_ID"] = report_id  
    subprocess.run(cmd, check=True, env=env)

    # --------------------------------------------------
    # Upload to Blob Storage (Azure only)
    # --------------------------------------------------
    if os.getenv("WEBSITE_SITE_NAME"):
        blob_root = f"artifacts/{report_id}/"
        uploaded_urls = []

        # Recursively upload files only
        for path in output_dir.rglob("*"):
            if path.is_file():
                blob_path = blob_root + path.relative_to(output_dir).as_posix()
                url = upload_file(path, blob_path)
                uploaded_urls.append(url)

        return uploaded_urls

    # --------------------------------------------------
    # Local fallback (dev mode)
    # --------------------------------------------------
    return [str(p) for p in output_dir.rglob("*") if p.is_file()]
