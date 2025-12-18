#!/usr/bin/env python3
# visualspec_to_reportjson.py

import json
import uuid
import datetime
import os

def make_visual(v, dataset_name):
    """Convert VisualSpec visual → Power BI visual JSON."""
    vis_id = str(uuid.uuid4())

    fields = []
    for f in v.get("fields", []):
        if "." in f:
            continue
        fields.append({
            "Column": {
                "Expression": {"SourceRef": {"Entity": dataset_name}},
                "Property": f
            }
        })

    if v["type"] == "Table":
        visual_type = "tableEx"
    elif v["type"] == "PieChart":
        visual_type = "pieChart"
    else:
        visual_type = "tableEx"

    return {
        "name": vis_id,
        "visualType": visual_type,
        "title": v.get("title") or "",
        "prototypeQuery": {
            "From": [{"Name": "a", "Entity": dataset_name}],
            "Select": fields
        }
    }

def generate_report_json(visualspec, dataset_name, out_path):
    with open(visualspec, "r", encoding="utf-8") as f:
        vs = json.load(f)

    report = {
        "version": "1.13.0",
        "config": {"layoutOptimization": 1},
        "sections": []
    }

    for page in vs["pages"]:
        page_id = str(uuid.uuid4())

        visuals = []
        for v in page["visuals"]:
            if not v["fields"]:
                continue
            visuals.append(make_visual(v, dataset_name))

        section = {
            "name": page_id,
            "displayName": page["name"],
            "visualContainers": visuals
        }
        report["sections"].append(section)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("Generated report layout JSON:", out_path)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    generate_report_json(args.visual, args.dataset, args.out)
