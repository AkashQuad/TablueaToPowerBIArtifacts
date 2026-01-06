import subprocess
import os
import json
from pathlib import Path
from typing import List

from app.storage.blob import upload_file
from app.config import ARTIFACTS_DIR, SCRIPTS_DIR


def generate_pbi_artifacts(
    parsed_meta_path: str,
    report_id: str,
    output_dir: str,
) -> List[str]:
    """
    Generate Power BI artifacts from parsed Tableau metadata ONLY.
    NO source configuration.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # Run generator script (NO SOURCE FLAGS)
    # --------------------------------------------------
    cmd = [
        "python",
        str(SCRIPTS_DIR / "generate_pbi_artifacts_prod.py"),
        "--input", parsed_meta_path,
        "--out", str(output_dir),
    ]

    env = os.environ.copy()
    env["REPORT_ID"] = report_id

    subprocess.run(cmd, check=True, env=env)

    # --------------------------------------------------
    # Upload artifacts to Azure Blob (prod)
    # --------------------------------------------------
    uploaded_urls = []

    if os.getenv("WEBSITE_SITE_NAME"):
        blob_root = f"artifacts/{report_id}/"

        for path in output_dir.rglob("*"):
            if path.is_file():
                blob_path = blob_root + path.relative_to(output_dir).as_posix()
                url = upload_file(path, blob_path)
                uploaded_urls.append(url)

        return uploaded_urls

    # --------------------------------------------------
    # Local dev fallback
    # --------------------------------------------------
    return [str(p) for p in output_dir.rglob("*") if p.is_file()]
