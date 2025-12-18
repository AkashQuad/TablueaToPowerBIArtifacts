from pathlib import Path
import json
from app.config import SOURCES_DIR


def save_source_config(report_id: str, source_type: str, source_config: dict) -> Path:
    """
    Saves user-selected source configuration for a report.
    """

    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "report_id": report_id,
        "source_type": source_type,
        "source_config": source_config
    }

    out_path = SOURCES_DIR / f"{report_id}_source.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return out_path
