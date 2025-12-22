import subprocess
import os
from app.storage.blob import upload_file
from pathlib import Path
from app.config import ARTIFACTS_DIR, SCRIPTS_DIR


def generate_pbi_artifacts(parsed_meta_path, report_id, source_type, source_config):

    output_dir = ARTIFACTS_DIR / report_id
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python",
        str(SCRIPTS_DIR / "generate_pbi_artifacts_prod.py"),
        "--input", parsed_meta_path,
        "--out", str(output_dir),
        "--source-type", source_type,
        "--source-config", json.dumps(source_config),
    ]

    subprocess.run(cmd, check=True)

    if os.getenv("WEBSITE_SITE_NAME"):
        blob_root = f"artifacts/{report_id}/"
        urls = []

        for file in output_dir.glob("*"):
            url = upload_file(file, blob_root + file.name)
            urls.append(url)

        return urls

    return [str(p) for p in output_dir.glob("*")]
