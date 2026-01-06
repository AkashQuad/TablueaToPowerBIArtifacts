import subprocess
from pathlib import Path
from app.config import SCRIPTS_DIR, ARTIFACTS_DIR


def generate_pbi_artifacts(
    parsed_meta_path: str,
    report_id: str,
):
    """
    Generate Power BI artifacts WITHOUT any source configuration.
    """

    output_dir = ARTIFACTS_DIR / report_id
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python",
        str(SCRIPTS_DIR / "generate_pbi_artifacts_prod.py"),
        "--input", parsed_meta_path,
        "--out", str(output_dir),
    ]

    subprocess.run(cmd, check=True)

    return [str(p) for p in output_dir.rglob("*") if p.is_file()]
