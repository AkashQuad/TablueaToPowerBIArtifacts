#!/usr/bin/env python3
"""
generate_pbi_artifacts_prod.py

Production-grade Step-4 generator.


Input:
 - parsed_meta.json (from Tableau parser)

Output:
 artifacts/
 ├── model/{reportId}_modelspec.json
 ├── dax/*.dax
 ├── visuals/{reportId}_visual.json
 ├── powerquery/{reportId}_source.m
 └── artifact_manifest.json

Supports explicit source selection:
 - excel
 - sharepoint
 - sql
 - fabric

Fully compatible with:
 - Power BI Fabric
 - XMLA RW
 - Tabular Editor 3
"""

from __future__ import annotations
import argparse
import json
import os
import re
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

# -------------------------------------------------
# Logging
# -------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("pbi-artifacts-prod")

# -------------------------------------------------
# Helpers
# -------------------------------------------------
SAFE_NAME_RE = re.compile(r"[^0-9A-Za-z_]")

AGG_PATTERN = re.compile(
    r"^\[?(?P<agg>sum|avg|count|min|max|median|distinct)\:(?P<col>[^\:]+)",
    re.IGNORECASE
)

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def write_json(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    logger.info("Wrote JSON: %s", path)

def write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    logger.info("Wrote file: %s", path)

def safe_id(name: str) -> str:
    if not name:
        return "unnamed"
    s = name.strip().replace(" ", "_")
    s = SAFE_NAME_RE.sub("_", s)
    if s.isdigit():
        s = "_" + s
    return s

def normalize_type(t: str) -> str:
    if not t:
        return "String"
    t = t.lower()
    if t in ("int", "integer", "long"):
        return "Int64"
    if t in ("float", "double", "decimal", "real"):
        return "Double"
    if "date" in t:
        return "DateTime"
    if "bool" in t:
        return "Boolean"
    return "String"

# -------------------------------------------------
# Power Query Generator
# -------------------------------------------------
def generate_powerquery(source_type: str, cfg: Dict[str, Any]) -> str:
    if source_type == "excel":
        return f"""
let
    Source = Excel.Workbook(
        Web.Contents("{cfg['url']}"),
        null,
        true
    ),
    Data = Source{{[Item="{cfg['sheet']}",Kind="Sheet"]}}[Data],
    PromotedHeaders = Table.PromoteHeaders(Data)
in
    PromotedHeaders
"""

    if source_type == "sharepoint":
        return f"""
let
    Source = SharePoint.Files("{cfg['site']}", [ApiVersion=15]),
    File = Source{{[Name="{cfg['file']}"]}}[Content],
    Data = Excel.Workbook(File, null, true),
    Sheet = Data{{[Item="{cfg['sheet']}",Kind="Sheet"]}}[Data],
    PromotedHeaders = Table.PromoteHeaders(Sheet)
in
    PromotedHeaders
"""

    if source_type == "sql":
        return f"""
let
    Source = Sql.Database("{cfg['server']}", "{cfg['database']}"),
    Table = Source{{[Schema="{cfg['schema']}",Item="{cfg['table']}"]}}[Data]
in
    Table
"""

    if source_type == "fabric":
        return f"""
let
    Source = Fabric.Warehouse("{cfg['workspace']}", "{cfg['lakehouse']}"),
    Table = Source{{[Schema="dbo",Item="{cfg['table']}"]}}[Data]
in
    Table
"""

    raise ValueError(f"Unsupported sourceType: {source_type}")

# -------------------------------------------------
# Main Generator
# -------------------------------------------------
def generate_artifacts(
    parsed_meta: Dict[str, Any],
    out_root: str,
    source_type: str,
    source_config: Dict[str, Any]
) -> Dict[str, Any]:

    report_id = safe_id(os.environ.get("REPORT_ID", "report"))
    generated_at = datetime.now(timezone.utc).isoformat()

    ensure_dir(out_root)
    model_dir = os.path.join(out_root, "model")
    dax_dir = os.path.join(out_root, "dax")
    visuals_dir = os.path.join(out_root, "visuals")
    pq_dir = os.path.join(out_root, "powerquery")

    for d in (model_dir, dax_dir, visuals_dir, pq_dir):
        ensure_dir(d)

    # -------------------------------
    # ModelSpec
    # -------------------------------
    tables = []
    for t in parsed_meta.get("tables", []):
        cols = []
        for c in t.get("columns", []):
            cols.append({
                "name": c.get("name"),
                "type": normalize_type(c.get("type"))
            })
        tables.append({
            "name": safe_id(t.get("name")),
            "columns": cols
        })

    model_spec = {
        "reportId": report_id,
        "generatedAt": generated_at,
        "tables": tables,
        "relationships": parsed_meta.get("relationships", [])
    }

    model_path = os.path.join(model_dir, f"{report_id}_modelspec.json")
    write_json(model_path, model_spec)

    # -------------------------------
    # Measures → DAX
    # -------------------------------
    dax_files = []
    for m in parsed_meta.get("measures", []):
        name = m.get("name")
        expr = m.get("expression") or f"// TODO: Implement DAX for {name}"
        dax_path = os.path.join(dax_dir, f"{safe_id(name)}.dax")
        write_text(dax_path, expr)
        dax_files.append(dax_path)

    # -------------------------------
    # Visual Spec
    # -------------------------------
    visual_spec = {
        "reportId": report_id,
        "generatedAt": generated_at,
        "pages": parsed_meta.get("worksheets", [])
    }

    visual_path = os.path.join(visuals_dir, f"{report_id}_visual.json")
    write_json(visual_path, visual_spec)

    # -------------------------------
    # Power Query (ONE per model)
    # -------------------------------
    pq_text = generate_powerquery(source_type, source_config)
    pq_path = os.path.join(pq_dir, f"{report_id}_source.m")
    write_text(pq_path, pq_text)

    # -------------------------------
    # Manifest
    # -------------------------------
    manifest = {
        "reportId": report_id,
        "generatedAt": generated_at,
        "modelSpec": model_path,
        "daxFiles": dax_files,
        "visualSpec": visual_path,
        "powerQueryFiles": [pq_path]
    }

    manifest_path = os.path.join(out_root, "artifact_manifest.json")
    write_json(manifest_path, manifest)

    return manifest

# -------------------------------------------------
# CLI (local testing only)
# -------------------------------------------------
def cli():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="parsed_meta.json")
    p.add_argument("--out", default="artifacts")
    p.add_argument("--source-type", required=True)
    p.add_argument("--source-config", required=True, help="JSON string")

    args = p.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        parsed_meta = json.load(f)

    source_cfg = json.loads(args.source_config)

    manifest = generate_artifacts(
        parsed_meta,
        args.out,
        args.source_type,
        source_cfg
    )

    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    cli()
