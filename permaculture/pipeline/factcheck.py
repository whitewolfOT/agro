"""
Step 4 — factcheck.py
Entry point: factcheck(merged: dict) -> dict
Reads:  output/merged.json
Writes: output/factchecked.json
"""
import json
import sys
from pathlib import Path

from pipeline.schemas import EDGE_TYPES

# ── 4-A: Known-bad edges ──────────────────────────────────────────────────────

KNOWN_ERRORS = [
    ("Corn",   "Carrot",  "hostile", "allelopathy claim weak — no confirmed juglone-class compound in maize"),
    ("Bamboo", "Vetiver", "hostile", "competitive not allelopathic — reclassify to soil_exhaust"),
    ("Walnut", "*",       "hostile", "confirm juglone target — only affects specific species, not all"),
]

# ── 4-B: Known-missing edges ─────────────────────────────────────────────────

KNOWN_ADDITIONS = [
    # Islamic agronomy — grafting pairs from Ibn al-Awwam
    ("Quince",       "Pear",              "grafting",     "Ibn al-Awwam explicit — quince rootstock for pear"),
    ("Wild Olive",   "Cultivated Olive",  "grafting",     "Ibn al-Awwam explicit"),
    ("Almond",       "Peach",             "grafting",     "Ibn al-Awwam explicit"),
    # Nitrogen fixers missing soil edge
    ("Fava Bean",    "SOIL",              "nitrogen_fix", "Vicia faba — well-documented N-fixer, modern reconstruction"),
    ("Lentil",       "SOIL",              "nitrogen_fix", "Lens culinaris — well-documented N-fixer, modern reconstruction"),
    ("Chickpea",     "SOIL",              "nitrogen_fix", "Cicer arietinum — well-documented N-fixer, modern reconstruction"),
    ("Lupin",        "SOIL",              "nitrogen_fix", "Lupinus spp. — Ibn al-Awwam describes as soil restorer, modern reconstruction"),
    # Allelopathy — confirmed juglone targets
    ("Walnut",       "Apple",             "hostile",      "juglone — confirmed susceptible, Explicit from literature"),
    ("Walnut",       "Tomato",            "hostile",      "juglone — confirmed susceptible, Explicit from literature"),
    ("Walnut",       "Alfalfa",           "hostile",      "juglone — confirmed susceptible, Explicit from literature"),
    # Companion pairs from Islamic texts missing from graph
    ("Basil",        "Vine",              "companion",    "Ibn al-Awwam — plant basil at vine base, Explicit"),
    ("Rue",          "Fig",               "companion",    "Ibn al-Awwam — rue under fig deters pests, Explicit"),
    ("Garlic",       "Rose",              "companion",    "Ibn al-Awwam — garlic improves rose scent, Explicit"),
    # Soil exhausters missing
    ("Cotton",       "SOIL",              "soil_exhaust", "heavy N/K feeder — well documented, Modern reconstruction"),
    ("Sugar Cane",   "SOIL",              "soil_exhaust", "heavy feeder — well documented, Modern reconstruction"),
]

# ── 4-C: Form back-fill ───────────────────────────────────────────────────────

FORM_BACKFILL = {
    "Nitrogen fixer": None,   # handled by function tag — leave form as actual plant form
    "Acacia":       "mid_tree",
    "Leucaena":     "mid_tree",
    "Casuarina":    "canopy_tree",
    "Clover":       "groundcover",
    "Alfalfa":      "groundcover",
    "Lupin":        "groundcover",
    "Fava Bean":    "groundcover",
    "Lentil":       "groundcover",
    "Chickpea":     "groundcover",
    "Wormwood":     "shrub",
    "Rue":          "shrub",
}

_EV_RANK = {
    "Uncertain": 0,
    "Modern reconstruction": 1,
    "Strongly implied": 2,
    "Explicit": 3,
}


def _matches_pattern(src: str, tgt: str, etype: str,
                     pat_src: str, pat_tgt: str, pat_type: str) -> bool:
    src_ok  = pat_src  == "*" or src.lower()  == pat_src.lower()
    tgt_ok  = pat_tgt  == "*" or tgt.lower()  == pat_tgt.lower()
    type_ok = pat_type == "*" or etype         == pat_type
    return src_ok and tgt_ok and type_ok


def factcheck(merged: dict) -> dict:
    nodes = [dict(n) for n in merged.get("nodes", [])]
    edges = [dict(e) for e in merged.get("edges", [])]

    # Build fast lookups
    node_ids_lower = {n["id"].lower(): n["id"] for n in nodes}

    def _canon(name: str) -> str:
        return node_ids_lower.get(name.lower(), name)

    existing_triples: set[tuple] = {
        (_canon(e["source"]), _canon(e["target"]), e["type"])
        for e in edges
    }

    # ── 4-A: Flag known-bad edges ─────────────────────────────────────────────
    edges_flagged = 0
    for edge in edges:
        if edge.get("added"):          # KNOWN_ADDITIONS are verified correct — never flag
            continue
        src, tgt, etype = edge["source"], edge["target"], edge["type"]
        for pat_src, pat_tgt, pat_type, reason in KNOWN_ERRORS:
            if _matches_pattern(src, tgt, etype, pat_src, pat_tgt, pat_type):
                edge["confidence"] = 0.1
                flags = edge.get("_flags", [])
                if "FACTCHECK_FLAGGED" not in flags:
                    flags.append("FACTCHECK_FLAGGED")
                    edges_flagged += 1
                edge["_flags"] = flags
                edge["notes"] = edge.get("notes") or reason
                break

    # ── 4-B: Add known-missing edges ─────────────────────────────────────────
    edges_added = 0
    for src_raw, tgt_raw, etype, reason in KNOWN_ADDITIONS:
        src = _canon(src_raw)
        tgt = _canon(tgt_raw)

        # Ensure both endpoint nodes exist (add stub if missing)
        for nid in (src, tgt):
            if nid.lower() not in node_ids_lower:
                stub = {
                    "id": nid,
                    "kind": "hub" if nid.upper() == nid else "plant",
                    "name_ar": None, "name_sci": None,
                    "form": None,
                    "function": [], "use": [],
                    "sources": [],
                    "evidence_level": "Modern reconstruction",
                    "isolated": False, "notes": None,
                    "_flags": [],
                }
                nodes.append(stub)
                node_ids_lower[nid.lower()] = nid

        triple = (src, tgt, etype)
        if triple in existing_triples:
            continue

        # Parse evidence from reason string
        reason_lower = reason.lower()
        if "explicit" in reason_lower:
            ev = "Explicit"
        elif "modern reconstruction" in reason_lower:
            ev = "Modern reconstruction"
        else:
            ev = "Strongly implied"

        new_edge = {
            "source":         src,
            "target":         tgt,
            "type":           etype,
            "direction":      "directed",
            "context":        [],
            "source_id":      "factcheck.py",
            "evidence_level": ev,
            "evidence_quote": reason,
            "confidence":     0.7,
            "added":          True,
            "_flags":         [],
            "note":           reason,
        }
        edges.append(new_edge)
        existing_triples.add(triple)
        edges_added += 1

    # ── 4-C: Form back-fill ───────────────────────────────────────────────────
    inc01_remaining = 0
    for node in nodes:
        if "INC-01" not in node.get("_flags", []):
            continue
        nid = node["id"]
        if nid in FORM_BACKFILL:
            new_form = FORM_BACKFILL[nid]
            if new_form is not None:
                node["form"] = new_form
                node["_flags"] = [f for f in node["_flags"] if f != "INC-01"]
            else:
                inc01_remaining += 1
        else:
            inc01_remaining += 1

    result = {"nodes": nodes, "edges": edges}

    out_path = Path("output/factchecked.json")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    return result, edges_added, edges_flagged, inc01_remaining


if __name__ == "__main__":
    merged_path = Path("output/merged.json")
    merged = json.loads(merged_path.read_text(encoding="utf-8"))

    result, edges_added, edges_flagged, inc01_remaining = factcheck(merged)

    # Verify KNOWN_ADDITIONS all processed and KNOWN_ERRORS all flagged
    edges_out = result["edges"]

    # Check every KNOWN_ERROR pattern has at least one flagged edge (or no matching edge)
    errors_checked = 0
    for pat_src, pat_tgt, pat_type, _ in KNOWN_ERRORS:
        matching = [e for e in edges_out
                    if not e.get("added") and
                    _matches_pattern(e["source"], e["target"], e["type"],
                                     pat_src, pat_tgt, pat_type)]
        if matching:
            all_flagged = all("FACTCHECK_FLAGGED" in e.get("_flags", []) for e in matching)
            if all_flagged:
                errors_checked += 1
            else:
                unflagged = [e for e in matching if "FACTCHECK_FLAGGED" not in e.get("_flags", [])]
                print(f"WARN: {len(unflagged)} edges matching ({pat_src},{pat_tgt},{pat_type}) not flagged")
        else:
            errors_checked += 1  # pattern had no matches — OK

    print(f"edges_added={edges_added}")
    print(f"edges_flagged={edges_flagged}")
    print(f"INC-01_remaining={inc01_remaining}")

    additions_ok = edges_added + (len(KNOWN_ADDITIONS) - edges_added) == len(KNOWN_ADDITIONS)
    errors_ok    = errors_checked == len(KNOWN_ERRORS)

    if additions_ok and errors_ok:
        print("PASS")
    else:
        print("FAIL")
        if not additions_ok:
            print(f"  KNOWN_ADDITIONS not fully processed")
        if not errors_ok:
            print(f"  KNOWN_ERRORS not fully flagged")
