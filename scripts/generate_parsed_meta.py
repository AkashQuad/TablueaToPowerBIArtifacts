#!/usr/bin/env python3
"""
generate_parsed_meta.py

Production-grade parser: Extracts normalized metadata from a Tableau workbook (.twb or .twbx).

Usage (examples):
  python generate_parsed_meta.py --input /path/to/workbook.twbx --output ./parsed_meta.json
  python generate_parsed_meta.py --input /path/to/workbook.twb  --output ./parsed_meta.json

Features:
- Accepts .twb (XML) or .twbx (zip archive containing .twb).
- Robust XML parsing using lxml and namespace-agnostic XPath.
- Produces JSON with keys: reportId, report_name, generatedAt, datasources, tables,
  relationships, worksheets, dashboards, measures, connections.
- Defensive: handles missing sections, logs warnings, provides extension points.
"""

from __future__ import annotations
import argparse
import logging
import json
import os
import zipfile
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from lxml import etree

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("tbx-parser")

# ---------- Helpers ----------
def read_twb_from_twbx(twbx_path: str, preferred_names: Optional[List[str]] = None) -> str:
    """
    Extract and return the content of the first .twb file found inside the .twbx archive.
    If preferred_names provided, attempt those filenames first.
    """
    preferred_names = preferred_names or []
    with zipfile.ZipFile(twbx_path, 'r') as z:
        # Try preferred names first
        for name in preferred_names:
            try:
                with z.open(name) as f:
                    data = f.read().decode('utf-8')
                    logger.info("Extracted TWB from preferred path: %s", name)
                    return data
            except KeyError:
                continue

        # fallback: find any .twb file
        twb_candidates = [f for f in z.namelist() if f.lower().endswith('.twb')]
        if not twb_candidates:
            raise ValueError(f"No .twb file found inside {twbx_path}")
        # pick the first candidate
        with z.open(twb_candidates[0]) as f:
            data = f.read().decode('utf-8')
            logger.info("Extracted TWB from archive path: %s", twb_candidates[0])
            return data

def parse_xml_string(xml_text: str) -> etree._ElementTree:
    """
    Parse XML string into an lxml ElementTree with recover=True for robustness.
    """
    parser = etree.XMLParser(recover=True, remove_blank_text=True, ns_clean=True)
    return etree.fromstring(xml_text.encode('utf-8'), parser=parser)

def text_of(node: Optional[etree._Element]) -> Optional[str]:
    if node is None:
        return None
    return (node.text or "").strip()

def findall_ns_agnostic(root: etree._Element, tag_localname: str) -> List[etree._Element]:
    """
    Return elements with local-name() == tag_localname, searching anywhere under root.
    """
    xpath = f".//*[local-name() = '{tag_localname}']"
    return root.xpath(xpath)

def find_ns_agnostic(root: etree._Element, tag_localname: str) -> Optional[etree._Element]:
    res = findall_ns_agnostic(root, tag_localname)
    return res[0] if res else None

# ---------- Extractors ----------
def extract_workbook_title(root: etree._Element) -> Optional[str]:
    # workbook title may be stored as <workbook ... name="..."> or <document-name> or <title>
    # check common locations
    if root is None:
        return None
    # try workbook attribute 'name'
    title = root.get("name")
    if title:
        return title
    # try /workbook/document-name or /workbook/title
    dn = root.xpath(".//*[local-name()='document-name']")
    if dn:
        return text_of(dn[0])
    t = root.xpath(".//*[local-name()='title']")
    if t:
        return text_of(t[0])
    return None

def extract_datasources(root: etree._Element) -> List[Dict[str, Any]]:
    """
    Extract datasource definitions: connection info, type, id/name, and any SQL/native-query found.
    """
    datasources = []
    ds_nodes = findall_ns_agnostic(root, "datasource") + findall_ns_agnostic(root, "data-source")
    seen_ids = set()

    for ds in ds_nodes:
        ds_id = ds.get("name") or ds.get("caption") or ds.get("formula") or ds.get("id") or ds.get("datasource-id") or ds.get("class")
        if not ds_id:
            # fallback to generated id
            ds_id = f"datasource_{len(datasources)+1}"
        if ds_id in seen_ids:
            # avoid duplicates (Tableau twb sometimes repeats)
            continue
        seen_ids.add(ds_id)

        # connection type / attributes
        conn_type = None
        conn_info = {}
        # connection blocks may be under <connection> or <connection-info> etc.
        conn_nodes = ds.xpath(".//*[local-name()='connection'] | .//*[local-name()='connection-info'] | .//*[local-name()='connectionType']")
        if conn_nodes:
            # pick the first
            cn = conn_nodes[0]
            conn_type = cn.get("class") or cn.get("connection-class") or cn.get("type")
            # gather attributes as available
            conn_info.update({k: v for k, v in cn.items()})
            # some connection nodes contain nested elements with host/db
            for child in cn:
                if isinstance(child.tag, str):
                    conn_info[child.tag.split("}")[-1]] = (child.text or "").strip()

        # find any native SQL query (Value.NativeQuery style or custom SQL)
        query_text = None
        # search within datasource node for nodes that look like custom-sql
        cs = ds.xpath(".//*[contains(local-name(),'custom-sql') or contains(local-name(),'customsql') or contains(local-name(),'query') or contains(local-name(),'sql')]")
        if cs:
            # pick the first non-empty text content we find
            for cnode in cs:
                txt = (cnode.text or "").strip()
                if txt:
                    query_text = txt
                    break

        datasources.append({
            "id": ds_id,
            "name": ds.get("caption") or ds.get("name"),
            "connection_type": conn_type,
            "connection": conn_info,
            "query": query_text
        })
    return datasources

def extract_tables_and_columns(root: etree._Element) -> List[Dict[str, Any]]:
    """
    Extract tables and columns referenced in the workbook.
    Note: Tableau's TWB does not always declare tables in a single canonical place; columns often appear in datasources or as column-list elements.
    This function gathers columns found under datasource / column elements and normalizes by table name when available.
    """
    tables: Dict[str, Dict[str, Any]] = {}
    # find column-like nodes
    column_nodes = root.xpath(".//*[local-name()='column' or local-name()='column-instance' or local-name()='column-group' or local-name()='column-definition']")
    for col in column_nodes:
        # try to infer table name from ancestor datasource or table-reference attributes
        parent_ds = col.xpath("ancestor::*[local-name()='datasource' or local-name()='data-source']")
        table_name = None
        if parent_ds:
            # there might be a 'table' attribute on column or parent datasource
            table_name = col.get("table") or parent_ds[0].get("name") or parent_ds[0].get("caption")

        # column name
        col_name = col.get("caption") or col.get("name") or col.get("column-name") or text_of(col)
        if not col_name:
            continue

        # datatype heuristics from attributes
        col_type = col.get("datatype") or col.get("type") or col.get("data-type")

        # If no table inferred, group under '_unnamed'
        table_key = table_name or "_unnamed"
        if table_key not in tables:
            tables[table_key] = {"name": table_key, "columns": []}
        tables[table_key]["columns"].append({
            "name": col_name,
            "type": col_type
        })

    # also attempt to find explicit table nodes (some TWB contain <table name="...">)
    explicit_tables = findall_ns_agnostic(root, "table")
    for t in explicit_tables:
        tname = t.get("name") or t.get("caption")
        if not tname:
            continue
        if tname not in tables:
            tables[tname] = {"name": tname, "columns": []}
        # add column children if present
        for c in t.xpath(".//*[local-name()='column']"):
            cname = c.get("name") or c.get("caption") or text_of(c)
            ctype = c.get("datatype") or c.get("type")
            if cname:
                tables[tname]["columns"].append({"name": cname, "type": ctype})

    return list(tables.values())

def extract_calculated_fields_and_measures(root: etree._Element) -> List[Dict[str, Any]]:
    """
    Extract calculated fields and measures. These often appear as <column class='calculation' ...> or <calculation> nodes.
    We'll collect their name, formula/expression, and scope if visible.
    """
    results = []
    # common node names: 'calculation', 'calculated-field', 'calculatedField', 'formula'
    calc_nodes = root.xpath(".//*[contains(local-name(),'calculation') or contains(local-name(),'calculated') or contains(local-name(),'formula')]")
    seen = set()
    for cn in calc_nodes:
        # try to find a name and expression
        name = cn.get("caption") or cn.get("name") or cn.get("field-name")
        # expression might be in text or in a nested <formula> or <expression> element
        expr = None
        if cn.text and cn.text.strip():
            expr = cn.text.strip()
        else:
            # search for nested formula/expression nodes
            nested = cn.xpath(".//*[contains(local-name(),'formula') or contains(local-name(),'expression') or contains(local-name(),'calculation')]")
            for n in nested:
                if n is not cn and n.text and n.text.strip():
                    expr = n.text.strip()
                    break
        if not name and not expr:
            continue
        key = (name or "") + "|" + (expr or "")
        if key in seen:
            continue
        seen.add(key)
        results.append({"name": name, "expression": expr})
    return results

def extract_worksheets_and_visuals(root: etree._Element) -> List[Dict[str, Any]]:
    """
    Extract worksheets and (high-level) visual definitions.
    We collect worksheet names and for each, the visuals (type, title, fields referenced).
    Note: Visual internals are complex; we extract a high-level view suitable for VisualSpec translation.
    """
    sheets = []
    ws_nodes = findall_ns_agnostic(root, "worksheet") + findall_ns_agnostic(root, "view") + findall_ns_agnostic(root, "sheet")
    seen = set()
    for ws in ws_nodes:
        name = ws.get("name") or ws.get("caption") or text_of(ws.find("."))
        if not name:
            # sometimes 'name' stored as child element
            nnode = ws.xpath(".//*[local-name()='name' or local-name()='caption']")
            name = text_of(nnode[0]) if nnode else None
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        # Collect visuals in this worksheet (graphic elements, marks, encodings)
        visuals = []
        # heuristic: visual nodes often labelled 'view', 'mark', 'viz' or contain 'mark' child
        viz_nodes = ws.xpath(".//*[contains(local-name(),'mark') or contains(local-name(),'viz') or contains(local-name(),'view') or contains(local-name(),'worksheet')]")
        for v in viz_nodes[:10]:  # limit to first N to avoid explosion
            vtype = v.get("type") or v.get("class") or v.tag.split("}")[-1]
            # fields referenced may be in 'field' or 'column' descendants
            fields = []
            for f in v.xpath(".//*[local-name()='field' or local-name()='column' or local-name()='ref' or local-name()='attribute']"):
                fname = f.get("name") or f.get("caption") or text_of(f)
                if fname:
                    fields.append(fname)
            title = v.get("title") or v.get("caption") or None
            visuals.append({"id": v.get("id") or None, "type": vtype, "title": title, "fields": fields})
        sheets.append({"name": name, "visuals": visuals})
    return sheets

def extract_dashboards(root: etree._Element) -> List[Dict[str, Any]]:
    """
    Extract high-level dashboards and their sheets/objects.
    """
    dash_nodes = findall_ns_agnostic(root, "dashboard")
    dashboards = []
    for d in dash_nodes:
        dname = d.get("name") or d.get("caption") or text_of(d)
        if not dname:
            continue
        # collect contained worksheet references or zones
        items = []
        for item in d.xpath(".//*[contains(local-name(),'zone') or contains(local-name(),'worksheet') or contains(local-name(),'view') or contains(local-name(),'object')]"):
            # attempt to find which worksheet/view it references
            ref = item.get("sheet") or item.get("worksheet") or item.get("source") or text_of(item)
            items.append({"id": item.get("id"), "ref": ref, "type": item.tag.split("}")[-1]})
        dashboards.append({"name": dname, "items": items})
    return dashboards

def extract_relationships(root: etree._Element) -> List[Dict[str, Any]]:
    """
    Extract relationships (joins / relationships) if present.
    These may appear under <relation>, <join>, <relation-list> or similar nodes.
    """
    rels = []
    join_nodes = findall_ns_agnostic(root, "relation") + findall_ns_agnostic(root, "join") + findall_ns_agnostic(root, "relationship")
    for j in join_nodes:
        # try to find left/right table & column attributes or nested elements
        left_table = j.get("left-table") or j.get("from-table") or j.get("table1") or j.get("left")
        right_table = j.get("right-table") or j.get("to-table") or j.get("table2") or j.get("right")
        left_col = j.get("left-column") or j.get("from-column") or j.get("left-field") or None
        right_col = j.get("right-column") or j.get("to-column") or j.get("right-field") or None
        cardinality = j.get("cardinality") or j.get("type") or None
        rels.append({
            "from_table": left_table,
            "from_column": left_col,
            "to_table": right_table,
            "to_column": right_col,
            "cardinality": cardinality
        })
    return rels

def extract_connections(root: etree._Element) -> List[Dict[str, Any]]:
    """
    Pull out connection blocks that may appear at top-level or under datasources.
    """
    conns = []
    conn_nodes = findall_ns_agnostic(root, "connection") + findall_ns_agnostic(root, "connection-info")
    seen = set()
    for c in conn_nodes:
        info = {k: v for k, v in c.items()}
        # include nested child text nodes for host/db/user if present
        for child in c:
            if hasattr(child, "tag"):
                key = child.tag.split("}")[-1]
                val = (child.text or "").strip()
                if val:
                    info.setdefault(key, val)
        signature = json.dumps(info, sort_keys=True)
        if signature in seen:
            continue
        seen.add(signature)
        conns.append(info)
    return conns

# ---------- Main orchestration ----------
def build_parsed_meta_from_tree(root: etree._Element, source_filename: str) -> Dict[str, Any]:
    """
    Compose the final parsed_meta dict from individual extractors.
    """
    report_name = extract_workbook_title(root) or os.path.splitext(os.path.basename(source_filename))[0]
    parsed = {
        "reportId": os.path.splitext(os.path.basename(source_filename))[0],
        "report_name": report_name,
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "datasources": extract_datasources(root),
        "tables": extract_tables_and_columns(root),
        "relationships": extract_relationships(root),
        "worksheets": extract_worksheets_and_visuals(root),
        "dashboards": extract_dashboards(root),
        "measures": extract_calculated_fields_and_measures(root),
        "connections": extract_connections(root)
    }
    return parsed

def write_json_file(path: str, obj: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def parse_twbx_or_twb(input_path: str, output_path: str, prefer_twb_names: Optional[List[str]] = None) -> int:
    """
    Main entry: parse input file (twbx or twb) and write parsed_meta json to output_path.
    Returns 0 on success, non-zero on error.
    """
    logger.info("Starting parse: input=%s output=%s", input_path, output_path)
    if not os.path.isfile(input_path):
        logger.error("Input file not found: %s", input_path)
        return 2

    # read TWB content
    try:
        if input_path.lower().endswith(".twbx"):
            logger.info("Input is .twbx; extracting .twb")
            xml_text = read_twb_from_twbx(input_path, preferred_names=prefer_twb_names)
        elif input_path.lower().endswith(".twb"):
            logger.info("Input is .twb; reading")
            with open(input_path, "r", encoding="utf-8") as f:
                xml_text = f.read()
        else:
            raise ValueError("Input must be .twb or .twbx")
    except Exception as ex:
        logger.exception("Failed to read workbook: %s", ex)
        return 3

    # parse XML
    try:
        root = parse_xml_string(xml_text)
    except Exception as ex:
        logger.exception("XML parsing failed: %s", ex)
        return 4

    try:
        parsed_meta = build_parsed_meta_from_tree(root, os.path.basename(input_path))
        # ensure output dir exists
        outdir = os.path.dirname(output_path)
        if outdir and not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)
        write_json_file(output_path, parsed_meta)
        logger.info("Parsed metadata written to %s", output_path)
    except Exception as ex:
        logger.exception("Failed to extract metadata: %s", ex)
        return 5

    return 0

# ---------- CLI ----------
def cli():
    p = argparse.ArgumentParser(description="Generate a normalized parsed_meta.json from a .twb/.twbx Tableau workbook")
    p.add_argument("--input", "-i", required=True, help="Path to .twb or .twbx workbook")
    p.add_argument("--output", "-o", required=True, help="Output parsed_meta JSON path")
    p.add_argument("--prefer-twb", "--prefer", nargs="*", help="Optional list of preferred internal .twb paths/filenames to try first inside a .twbx")
    args = p.parse_args()
    rc = parse_twbx_or_twb(args.input, args.output, prefer_twb_names=args.prefer_twb)
    if rc != 0:
        logger.error("Parser exited with code %d", rc)
        raise SystemExit(rc)
    logger.info("Parser finished successfully")

if __name__ == "__main__":
    cli()
