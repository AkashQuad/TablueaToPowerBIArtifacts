from pathlib import Path
import os

# --- Detect correct base path under Azure and local ---
if os.getenv("WEBSITE_SITE_NAME"):
    # Azure: detect dynamic extracted path automatically
    possible_tmp = Path(__file__).resolve().parents[2]

    if "/tmp" in str(possible_tmp):
        BASE_DIR = possible_tmp
    else:
        BASE_DIR = Path("/home/site/wwwroot")
else:
    BASE_DIR = Path(__file__).resolve().parents[1]

# --- Work directories ---
WORK_DIR = BASE_DIR / "work"
UPLOAD_DIR = WORK_DIR / "uploads"
PARSED_DIR = WORK_DIR / "parsed"
SOURCES_DIR = WORK_DIR / "sources"
ARTIFACTS_DIR = WORK_DIR / "artifacts"
LAYOUT_DIR = WORK_DIR / "layout"
TE3_DIR = WORK_DIR / "te3"

# Scripts folder dynamic
SCRIPTS_DIR = BASE_DIR / "scripts"

# Create dirs if missing
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
