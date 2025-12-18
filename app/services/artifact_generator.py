import subprocess
import json
from pathlib import Path
from app.config import SCRIPTS_DIR

def generate_pbi_artifacts(
    parsed_meta_path: str,
    output_dir: str,
    source_type: str,
    source_config: dict
):
    cmd = [
        "python",
        str(SCRIPTS_DIR / "generate_pbi_artifacts_prod.py"),
        "--input", parsed_meta_path,
        "--out", output_dir,
        "--source-type", source_type,
        "--source-config", json.dumps(source_config),
    ]

    subprocess.run(cmd, check=True)
