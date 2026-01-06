import subprocess
from pathlib import Path
from app.config import SCRIPTS_DIR


def generate_pbi_artifacts(
    parsed_meta_path: str,
    output_dir: str,
):
    """
    Generate Power BI artifacts from parsed Tableau metadata ONLY.
   
    """

    cmd = [
        "python",
        str(SCRIPTS_DIR / "generate_pbi_artifacts_prod.py"),
        "--input", parsed_meta_path,
        "--out", output_dir,
    ]

    subprocess.run(cmd, check=True)
