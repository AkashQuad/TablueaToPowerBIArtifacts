import subprocess
from pathlib import Path
from app.config import SCRIPTS_DIR, TE3_DIR


def generate_te3_script(model_spec_path: str) -> Path:
    """
    Generates:
    TE3_apply_<reportId>.csx
    """

    cmd = [
        "python",
        str(SCRIPTS_DIR / "generate_te3_script.py"),
        "--model",
        model_spec_path,
        "--template",
        str(SCRIPTS_DIR / "apply_modelspec_template.csx"),
        "--out",
        str(TE3_DIR),
    ]

    subprocess.run(cmd, check=True)

    # Return generated script
    scripts = list(TE3_DIR.glob("TE3_apply_*.csx"))
    if not scripts:
        raise RuntimeError("TE3 script not generated")

    return scripts[0]
