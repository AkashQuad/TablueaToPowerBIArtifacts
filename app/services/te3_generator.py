import subprocess
import os
from app.config import SCRIPTS_DIR, TE3_DIR
from app.storage.blob import upload_file


def generate_te3_script(model_spec_path, report_id):

    cmd = [
        "python",
        str(SCRIPTS_DIR / "generate_te3_script.py"),
        "--model", model_spec_path,
        "--template", str(SCRIPTS_DIR / "apply_modelspec_template.csx"),
        "--out", str(TE3_DIR),
    ]

    subprocess.run(cmd, check=True)

    scripts = list(TE3_DIR.glob("TE3_apply_*.csx"))

    if not scripts:
        raise RuntimeError("TE3 script not generated")

    script = scripts[0]

    if os.getenv("WEBSITE_SITE_NAME"):
        return upload_file(script, f"te3/{script.name}")

    return str(script)
