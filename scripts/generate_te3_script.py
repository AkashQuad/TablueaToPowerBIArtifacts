#!/usr/bin/env python3
"""
generate_te3_script.py

Reads <reportId>_modelspec.json and generates a TE3 script:
TE3_apply_<reportId>.csx

Uses apply_modelspec_template.csx with placeholders:
  {{TABLES}}
  {{MEASURES}}
  {{RELATIONSHIPS}}

Fully compatible with Tabular Editor 3 and Fabric XMLA RW.

Author: Automated Pipeline Transformer
"""

import json
import os
import re
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("TE3-Generator")

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------

def safe_id(name: str) -> str:
    """Normalize name to valid identifier."""
    if not name:
        return "Unnamed"
    s = name.strip()
    s = re.sub(r"[^0-9A-Za-z_ ]", "_", s)
    s = s.replace(" ", "_")
    if re.fullmatch(r"\d+", s):
        s = "_" + s
    return s


def map_datatype(dt: str) -> str:
    """Map ModelSpec type → TE3 .NET DataType"""
    if not dt:
        return "DataType.String"

    t = dt.lower()
    if t in ("int64", "integer", "int", "long"):
        return "DataType.Int64"
    if t in ("double", "float", "decimal", "real", "number"):
        return "DataType.Double"
    if "date" in t:
        return "DataType.DateTime"
    if "bool" in t:
        return "DataType.Boolean"

    return "DataType.String"


# --------------------------------------------------------------------
# GENERATORS
# --------------------------------------------------------------------

def gen_table_block(table):
    """
    Generate C# code for creating a table and columns.
    """
    tname = table["name"]
    tname_safe = safe_id(tname)

    code = []
    code.append(f"// ---- Table: {tname} ----")
    code.append(
        f"var tbl_{tname_safe} = Model.Tables.Find(\"{tname}\") ?? Model.AddTable(\"{tname}\");"
    )

    for col in table.get("columns", []):
        cname = col["name"]
        ctype = map_datatype(col.get("type"))

        cname_safe = cname.replace('"', '\\"')

        code.append(
            f"if (!tbl_{tname_safe}.Columns.Contains(\"{cname_safe}\")) {{ "
            f"var c = tbl_{tname_safe}.AddDataColumn(\"{cname_safe}\"); "
            f"c.DataType = {ctype}; "
            f"LogInfo(\"Added column: {cname_safe} ({ctype})\"); }}"
        )

    code.append("")  # line break
    return "\n".join(code)


def gen_measure_block(measure):
    """
    Generate C# code for creating/updating a measure.
    """
    name = measure["name"]
    expr = measure["expression"] or f"// TODO: Define expression for {name}"

    # escape quotes
    name_safe = name.replace('"', '\\"')
    expr_safe = expr.replace('"', '\\"')

    code = []
    code.append(f"// ---- Measure: {name} ----")
    code.append(
        f"var m = Model.AllMeasures.FirstOrDefault(x => x.Name == \"{name_safe}\");"
    )
    code.append("if (m == null) {")
    code.append(f"    m = Model.AddMeasure(\"{name_safe}\", \"{expr_safe}\");")
    code.append("    LogInfo($\"Created measure: {m.Name}\");")
    code.append("} else {")
    code.append(f"    m.Expression = \"{expr_safe}\";")
    code.append("    LogInfo($\"Updated measure: {m.Name}\");")
    code.append("}")
    code.append("")
    return "\n".join(code)


def gen_relationship_block(rel, table_names):
    """
    Generate C# code for a relationship, or skip invalid ones.
    """
    ft = rel.get("from_table")
    fc = rel.get("from_column")
    tt = rel.get("to_table")
    tc = rel.get("to_column")

    if not ft or not fc or not tt or not tc:
        logger.warning("Skipping invalid relationship: %s", rel)
        return "// Skipped invalid relationship (missing elements)\n"

    if ft not in table_names or tt not in table_names:
        logger.warning(
            "Skipping relationship: table not found in ModelSpec (%s → %s)",
            ft, tt
        )
        return "// Skipped relationship (table not found)\n"

    ft_s  = safe_id(ft)
    tt_s  = safe_id(tt)

    code = []
    code.append(f"// ---- Relationship: {ft}.{fc} → {tt}.{tc} ----")
    code.append(
        f"Model.AddRelationship(tbl_{ft_s}, \"{fc}\", tbl_{tt_s}, \"{tc}\");"
    )
    code.append("")

    return "\n".join(code)


# --------------------------------------------------------------------
# MAIN GENERATOR
# --------------------------------------------------------------------

def generate_script(modelspec_path, template_path, out_dir):
    logger.info("Loading ModelSpec: %s", modelspec_path)

    with open(modelspec_path, "r", encoding="utf-8") as f:
        ms = json.load(f)

    reportId = ms.get("reportId", "Report")
    out_file = os.path.join(out_dir, f"TE3_apply_{reportId}.csx")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # ---------- Generate TABLES ----------
    table_blocks = []
    table_names = []

    for table in ms.get("tables", []):
        table_blocks.append(gen_table_block(table))
        table_names.append(table["name"])

    tables_code = "\n".join(table_blocks)

    # ---------- Generate MEASURES ----------
    measure_blocks = []
    for m in ms.get("measures", []):
        measure_blocks.append(gen_measure_block(m))

    measures_code = "\n".join(measure_blocks)

    # ---------- Generate RELATIONSHIPS ----------
    relationship_blocks = []

    for rel in ms.get("relationships", []):
        relationship_blocks.append(
            gen_relationship_block(rel, table_names)
        )

    relationships_code = "\n".join(relationship_blocks)

    # ---------- Apply template ----------
    final_script = (
        template
        .replace("{{TABLES}}", tables_code)
        .replace("{{MEASURES}}", measures_code)
        .replace("{{RELATIONSHIPS}}", relationships_code)
    )

    # Ensure output folder exists
    os.makedirs(out_dir, exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(final_script)

    logger.info("Generated TE3 script: %s", out_file)
    return out_file


# --------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate TE3 automation script from ModelSpec JSON"
    )
    parser.add_argument("--model", required=True, help="Path to <reportId>_modelspec.json")
    parser.add_argument("--template", required=True, help="Path to template .csx file")
    parser.add_argument("--out", default=".", help="Output folder")

    args = parser.parse_args()

    script_path = generate_script(args.model, args.template, args.out)
    print(f"\nTE3 script generated: {script_path}\n")

