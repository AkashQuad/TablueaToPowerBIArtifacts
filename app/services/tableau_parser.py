import subprocess
from pathlib import Path
import os
from app.config import SCRIPTS_DIR, PARSED_DIR
from app.storage.local import save_file as save_local
from app.storage.blob import upload_file as save_blob


def parse_tableau_file(input_path: str, report_id: str) -> str:

    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    output_file = PARSED_DIR / f"{report_id}_parsed_meta.json"

    cmd = [
        "python",
        str(SCRIPTS_DIR / "generate_parsed_meta.py"),
        "--input", input_path,
        "--output", str(output_file)
    ]

    subprocess.run(cmd, check=True)

    if os.getenv("WEBSITE_SITE_NAME"):
        return save_blob(output_file, f"parsed/{output_file.name}")
    else:
        return str(output_file)
