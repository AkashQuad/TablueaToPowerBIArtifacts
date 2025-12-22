from pathlib import Path
import json
import os
from app.config import SOURCES_DIR
from app.storage.local import save_file as save_local
from app.storage.blob import upload_file as save_blob


def save_source_config(report_id, source_type, source_config):

    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    out_path = SOURCES_DIR / f"{report_id}_source.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "report_id": report_id,
            "source_type": source_type,
            "source_config": source_config
        }, f, indent=2)

    if os.getenv("WEBSITE_SITE_NAME"):
        return save_blob(out_path, f"sources/{out_path.name}")

    return str(out_path)
