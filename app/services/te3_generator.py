import subprocess
import os
import tempfile
from pathlib import Path

from app.config import SCRIPTS_DIR, TE3_DIR
from app.storage.blob import upload_file, download_file


def generate_te3_script(model_spec_path: str, report_id: str):
    """
    model_spec_path: blob path (NOT local path)
      e.g. artifacts/Report1/model/Report1_modelspec.json
    """

    # 1️⃣ Download ModelSpec from Blob → temp file
    tmp_dir = Path(tempfile.mkdtemp())
    local_model = tmp_dir / f"{report_id}_modelspec.json"

    download_file(model_spec_path, local_model)

    # 2️⃣ Ensure output dir exists
    TE3_DIR.mkdir(parents=True, exist_ok=True)

    # 3️⃣ Run TE3 generator
    cmd = [
        "python",
        str(SCRIPTS_DIR / "generate_te3_script.py"),
        "--model", str(local_model),
        "--template", str(SCRIPTS_DIR / "apply_modelspec_template.csx"),
        "--out", str(TE3_DIR),
    ]

    subprocess.run(cmd, check=True)

    # 4️⃣ Locate generated script
    scripts = list(TE3_DIR.glob(f"TE3_apply_{report_id}*.csx"))

    if not scripts:
        raise RuntimeError("TE3 script not generated")

    script = scripts[0]

    # 5️⃣ Upload to Blob
    if os.getenv("WEBSITE_SITE_NAME"):
        blob_path = f"artifacts/{report_id}/te3/{script.name}"
        return upload_file(script, blob_path)

    return str(script)
