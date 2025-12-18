import subprocess
from pathlib import Path
from app.config import SCRIPTS_DIR, LAYOUT_DIR


def generate_report_layout(visual_spec_path: str, dataset_name: str) -> Path:
    """
    Converts VisualSpec → Power BI Report JSON
    """

    output_file = LAYOUT_DIR / "report.json"

    cmd = [
        "python",
        str(SCRIPTS_DIR / "visualspec_to_reportjson.py"),
        "--visual",
        visual_spec_path,
        "--dataset",
        dataset_name,
        "--out",
        str(output_file),
    ]

    subprocess.run(cmd, check=True)

    return output_file
