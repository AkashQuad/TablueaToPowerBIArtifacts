from pathlib import Path
import os

# ------------------------------
# Detect BASE_DIR (Local / Azure)
# ------------------------------

if os.getenv("WEBSITE_SITE_NAME"):
    # Azure runtime: code is extracted under /tmp/<guid>
    tmp_root = Path("/tmp")

    # Search for the extracted root folder containing our scripts
    found = None
    for p in tmp_root.glob("*/scripts"):
        if p.is_dir():
            found = p.parent      # this is /tmp/<guid>
            break

    if found:
        BASE_DIR = found
    else:
        # Fallback – when running from ZIP package mode
        BASE_DIR = Path("/home/site/wwwroot")

else:
    # Local development environment
    BASE_DIR = Path(__file__).resolve().parents[1]

# ------------------------------
# Work directories
# ------------------------------

WORK_DIR = BASE_DIR / "work"
UPLOAD_DIR = WORK_DIR / "uploads"
PARSED_DIR = WORK_DIR / "parsed"
SOURCES_DIR = WORK_DIR / "sources"
ARTIFACTS_DIR = WORK_DIR / "artifacts"
LAYOUT_DIR = WORK_DIR / "layout"
TE3_DIR = WORK_DIR / "te3"

# ------------------------------
# Scripts directory (Dynamic)
# ------------------------------

# 1st: check dynamic Azure location inside /tmp/<guid>
scripts_inside_tmp = list(Path("/tmp").glob("*/scripts"))
if scripts_inside_tmp:
    SCRIPTS_DIR = scripts_inside_tmp[0]
else:
    # Fallback to BASE_DIR/scripts (local or /home/site/wwwroot/scripts)
    SCRIPTS_DIR = BASE_DIR / "scripts"

# ------------------------------
# Ensure needed folders exist
# ------------------------------

for d in [
    WORK_DIR,
    UPLOAD_DIR,
    PARSED_DIR,
    SOURCES_DIR,
    ARTIFACTS_DIR,
    LAYOUT_DIR,
    TE3_DIR,
]:
    d.mkdir(parents=True, exist_ok=True)
