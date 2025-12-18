# from pathlib import Path

# # Root of the repo
# BASE_DIR = Path(__file__).resolve().parents[1]

# # Runtime working directories
# WORK_DIR = BASE_DIR / "work"

# UPLOAD_DIR = WORK_DIR / "uploads"
# PARSED_DIR = WORK_DIR / "parsed"
# SOURCES_DIR = WORK_DIR / "sources"      # <<< REQUIRED
# ARTIFACTS_DIR = WORK_DIR / "artifacts"
# LAYOUT_DIR = WORK_DIR / "layout"
# TE3_DIR = WORK_DIR / "te3"

# # Scripts directory (unchanged legacy scripts)
# SCRIPTS_DIR = BASE_DIR / "scripts"

# # Ensure directories exist
# for d in [
#     WORK_DIR,
#     UPLOAD_DIR,
#     PARSED_DIR,
#     SOURCES_DIR,
#     ARTIFACTS_DIR,
#     LAYOUT_DIR,
#     TE3_DIR,
# ]:
#     d.mkdir(parents=True, exist_ok=True)


from pathlib import Path
import os

# Detect Azure
if os.getenv("WEBSITE_SITE_NAME"):
    BASE_DIR = Path("/home/site/wwwroot")
else:
    BASE_DIR = Path(__file__).resolve().parents[1]

WORK_DIR = BASE_DIR / "work"
UPLOAD_DIR = WORK_DIR / "uploads"
PARSED_DIR = WORK_DIR / "parsed"
SOURCES_DIR = WORK_DIR / "sources"
ARTIFACTS_DIR = WORK_DIR / "artifacts"
LAYOUT_DIR = WORK_DIR / "layout"
TE3_DIR = WORK_DIR / "te3"

SCRIPTS_DIR = BASE_DIR / "scripts"

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
