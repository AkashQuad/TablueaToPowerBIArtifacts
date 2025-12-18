import subprocess
from pathlib import Path
from app.config import SCRIPTS_DIR, PARSED_DIR


def parse_tableau_file(input_path: str, report_id: str) -> Path:
    """
    Runs generate_parsed_meta.py
    """

    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    output_file = PARSED_DIR / f"{report_id}_parsed_meta.json"

    cmd = [
        "python",
        str(SCRIPTS_DIR / "generate_parsed_meta.py"),
        "--input",
        input_path,
        "--output",
        str(output_file),
    ]

    subprocess.run(cmd, check=True)

    return output_file
