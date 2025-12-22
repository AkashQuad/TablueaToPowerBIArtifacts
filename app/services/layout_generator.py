import subprocess
import os
from app.config import SCRIPTS_DIR, LAYOUT_DIR
from app.storage.blob import upload_file


def generate_report_layout(visual_spec_path, dataset_name, report_id):

    output_file = LAYOUT_DIR / f"{report_id}_report.json"

    cmd = [
        "python",
        str(SCRIPTS_DIR / "visualspec_to_reportjson.py"),
        "--visual", visual_spec_path,
        "--dataset", dataset_name,
        "--out", str(output_file),
    ]

    subprocess.run(cmd, check=True)

    if os.getenv("WEBSITE_SITE_NAME"):
        return upload_file(output_file, f"layout/{output_file.name}")

    return str(output_file)
