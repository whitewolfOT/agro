"""
Step 5 — emit.py
Entry point: emit(factchecked: dict)
Reads:  output/factchecked.json
Writes: output/master_nodes.json
        output/master_edges.json
        output/inconsistencies.csv
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from pipeline.schemas import EDGE_TYPES, NODE_FORMS


def emit(factchecked: dict):
    nodes = [dict(n) for n in factchecked.get("nodes", [])]
    edges = [dict(e) for e in factchecked.get("edges", [])]

    # ── Pre-validation: add stub hub nodes for any missing edge endpoints ──────
    node_id_set = {n["id"] for n in nodes}
    for edge in edges:
        for endpoint in (edge["source"], edge["target"]):
            if endpoint not in node_id_set:
                stub = {
                    "id": endpoint,
                    "kind": "hub",
                    "name_ar": None,
                    "name_sci": None,
                    "form": None,
                    "function": [],
                    "use": [],
                    "sources": [],
                    "evidence_level": "Uncertain",
                    "isolated": False,
                    "notes": "Auto-generated stub for placeholder group target",
                    "_flags": ["INC-STUB"],
                }
                nodes.append(stub)
                node_id_set.add(endpoint)

    # ── Hard validations (crash if violated) ──────────────────────────────────
    node_id_set = {n["id"] for n in nodes}

    # 1. Every edge endpoint exists in nodes
    for edge in edges:
        for ep in (edge["source"], edge["target"]):
            if ep not in node_id_set:
                raise ValueError(f"Edge endpoint missing from nodes: {ep!r}")

    # 2. Every node form is in NODE_FORMS or null
    for node in nodes:
        form = node.get("form")
        if form is not None and form not in NODE_FORMS:
            raise ValueError(f"Node {node['id']!r} has invalid form {form!r}")

    # 3. Every edge type is in EDGE_TYPES
    for edge in edges:
        if edge.get("type") not in EDGE_TYPES:
            raise ValueError(
                f"Edge ({edge['source']}->{edge['target']}) has invalid type {edge['type']!r}"
            )

    # 4. Zero duplicate node ids
    ids = [n["id"] for n in nodes]
    counts = Counter(ids)
    dups = {k for k, v in counts.items() if v > 1}
    if dups:
        raise ValueError(f"Duplicate node ids: {dups}")

    # 5. Zero duplicate (source, target, type) triples
    triples = [(e["source"], e["target"], e["type"]) for e in edges]
    triple_counts = Counter(triples)
    dup_triples = {k for k, v in triple_counts.items() if v > 1}
    if dup_triples:
        raise ValueError(f"Duplicate (source,target,type) triples: {dup_triples}")

    # ── Build master_nodes ────────────────────────────────────────────────────
    master_nodes = []
    for node in nodes:
        master_nodes.append({
            "id":             node.get("id"),
            "kind":           node.get("kind", "plant"),
            "name_ar":        node.get("name_ar") or None,
            "name_sci":       node.get("name_sci") or None,
            "form":           node.get("form") or None,
            "function":       node.get("function") or [],
            "use":            node.get("use") or [],
            "sources":        node.get("sources") or [],
            "evidence_level": node.get("evidence_level", "Uncertain"),
            "isolated":       bool(node.get("isolated", False)),
            "added":          bool(node.get("added", False)),
            "flags":          node.get("_flags") or [],
            "notes":          node.get("notes") or None,
        })

    # ── Build master_edges ────────────────────────────────────────────────────
    master_edges = []
    added_count = 0
    flagged_count = 0
    for edge in edges:
        flags = edge.get("_flags") or []
        is_added  = bool(edge.get("added", False))
        is_flagged = "FACTCHECK_FLAGGED" in flags
        if is_added:
            added_count += 1
        if is_flagged:
            flagged_count += 1
        master_edges.append({
            "source":         edge.get("source"),
            "target":         edge.get("target"),
            "type":           edge.get("type"),
            "direction":      edge.get("direction", "directed"),
            "context":        edge.get("context") or [],
            "source_id":      edge.get("source_id") or edge.get("source_file") or "",
            "evidence_level": edge.get("evidence_level", "Uncertain"),
            "evidence_quote": edge.get("evidence_quote") or None,
            "confidence":     edge.get("confidence", 0.5),
            "added":          is_added,
            "flags":          flags,
        })

    # ── Build inconsistencies.csv ─────────────────────────────────────────────
    rows = []

    def _add_row(entity_id, flag_id, description, resolution, human_review):
        rows.append({
            "node_or_edge_id":       entity_id,
            "flag_id":               flag_id,
            "description":           description,
            "resolution_applied":    resolution,
            "requires_human_review": "TRUE" if human_review else "FALSE",
        })

    for node in nodes:
        nid = node["id"]
        for flag in (node.get("_flags") or []):
            if flag == "INC-01":
                _add_row(
                    nid, "INC-01",
                    f"Node form=UNKNOWN after normalization (cat={node.get('cat')!r})",
                    "form left as null; function/use tags applied where possible",
                    True,
                )
            elif flag == "INC-09":
                _add_row(
                    nid, "INC-09",
                    "form conflict between sources — kept Islamic agronomy source value",
                    f"form={node.get('form')!r} retained",
                    True,
                )
            elif flag == "INC-13":
                _add_row(
                    nid, "INC-13",
                    "name_ar or name_sci conflict between sources",
                    "first-encountered value retained",
                    True,
                )
            elif flag == "INC-STUB":
                _add_row(
                    nid, "INC-STUB",
                    "Placeholder group target auto-promoted to hub stub",
                    "kind=hub stub node created",
                    True,
                )
            else:
                _add_row(nid, flag, f"Flag {flag} on node", "see pipeline logs", False)

    for edge in edges:
        eid = f"{edge['source']}→{edge['target']}[{edge['type']}]"
        for flag in (edge.get("_flags") or []):
            if flag == "INC-03":
                _add_row(
                    eid, "INC-03",
                    f"Edge type could not be mapped to canonical EDGE_TYPES",
                    "type set to 'unknown'",
                    False,
                )
            elif flag == "FACTCHECK_FLAGGED":
                _add_row(
                    eid, "FACTCHECK_FLAGGED",
                    f"Known-bad or unverified edge: {edge.get('notes') or edge.get('note') or ''}",
                    "confidence=0.1; edge retained for human review",
                    True,
                )
            else:
                _add_row(eid, flag, f"Flag {flag} on edge", "see pipeline logs", False)

    # ── Write outputs ─────────────────────────────────────────────────────────
    out = Path("output")
    out.mkdir(exist_ok=True)

    (out / "master_nodes.json").write_text(
        json.dumps(master_nodes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "master_edges.json").write_text(
        json.dumps(master_edges, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    fieldnames = [
        "node_or_edge_id", "flag_id", "description",
        "resolution_applied", "requires_human_review",
    ]
    with open(out / "inconsistencies.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "final_node_count":        len(master_nodes),
        "final_edge_count":        len(master_edges),
        "added_edge_count":        added_count,
        "flagged_edge_count":      flagged_count,
        "inconsistencies_row_count": len(rows),
    }


if __name__ == "__main__":
    fc_path = Path("output/factchecked.json")
    factchecked = json.loads(fc_path.read_text(encoding="utf-8"))

    try:
        stats = emit(factchecked)
    except ValueError as exc:
        print(f"FAIL — validation error: {exc}")
        sys.exit(1)

    print(f"final_node_count={stats['final_node_count']}")
    print(f"final_edge_count={stats['final_edge_count']}")
    print(f"added_edge_count={stats['added_edge_count']}")
    print(f"flagged_edge_count={stats['flagged_edge_count']}")
    print(f"inconsistencies_row_count={stats['inconsistencies_row_count']}")
    print("PASS")
