"""
Step 2 — normalize.py
Entry point: normalize(raw: dict) -> dict
Reads:  output/raw_extracted.json
Writes: output/normalized.json
"""
import json
import sys
from collections import Counter
from pathlib import Path

from pipeline.schemas import (
    EDGE_TYPES, LEGACY_CAT_MAP, LEGACY_EDGE_MAP, NODE_FORMS,
)

# ── Extended category map (covers abbreviations + new categories from sources) ─

_EXTENDED_CAT_MAP = {
    **LEGACY_CAT_MAP,
    # Long-form categories from catalog files
    "Fruit trees":             {"form": "canopy_tree", "use": ["food"]},
    "Fruit tree":              {"form": "canopy_tree", "use": ["food"]},
    "Vegetables":              {"form": "groundcover", "use": ["food"]},
    "Vegetable":               {"form": "groundcover", "use": ["food"]},
    "Herbs & kitchen":         {"form": "groundcover", "use": ["food", "aromatic"]},
    "Medicinal plants":        {"use": ["medicinal"], "form": "UNKNOWN"},
    "Aromatics & perfume":     {"use": ["aromatic"], "form": "UNKNOWN"},
    "Aromatics & medicinal":   {"use": ["aromatic", "medicinal"], "form": "UNKNOWN"},
    "Aromatic":                {"use": ["aromatic"], "form": "UNKNOWN"},
    "Structural trees":        {"form": "canopy_tree"},
    "Structural":              {"form": "canopy_tree"},
    "Toxic & pest-control":    {"form": "UNKNOWN"},
    "Toxic":                   {"form": "UNKNOWN"},
    "Wild & utility plants":   {"form": "UNKNOWN"},
    "Cereals & grains":        {"form": "grass_grain", "use": ["food"]},
    "Cereal":                  {"form": "grass_grain", "use": ["food"]},
    "Legumes & pulses":        {"form": "groundcover", "function": ["nitrogen_fixer"], "use": ["food"]},
    "Legume":                  {"form": "groundcover", "function": ["nitrogen_fixer"]},
    "Fodder & green manure":   {"form": "groundcover", "use": ["fodder"]},
    "Fodder":                  {"form": "groundcover", "use": ["fodder"]},
    "Shrubs & semi-shrubs":    {"form": "shrub"},
    "Special":                 {"form": "UNKNOWN"},
    "Industrial":              {"use": ["fiber_industrial"], "form": "UNKNOWN"},
    "hub":                     {"kind": "hub"},
    "HB":                      {"kind": "hub"},
    # Short codes (from network HTMLs)
    "FT":  {"form": "canopy_tree", "use": ["food"]},
    "VG":  {"form": "groundcover", "use": ["food"]},
    "HK":  {"form": "groundcover", "use": ["food", "aromatic"]},
    "MP":  {"use": ["medicinal"], "form": "UNKNOWN"},
    "AP":  {"use": ["aromatic"], "form": "UNKNOWN"},
    "ST":  {"form": "canopy_tree"},
    "TP":  {"form": "UNKNOWN"},
    "IF":  {"use": ["fiber_industrial"], "form": "UNKNOWN"},
    "WU":  {"form": "UNKNOWN"},
    "CG":  {"form": "grass_grain", "use": ["food"]},
    "LP":  {"form": "groundcover", "function": ["nitrogen_fixer"], "use": ["food"]},
    "FG":  {"form": "groundcover", "use": ["fodder"]},
    "SS":  {"form": "shrub"},
    "AW":  {"form": "aquatic_wetland"},
    # Permaculture network categories
    "food_tree":     {"form": "canopy_tree", "use": ["food"]},
    "food_annual":   {"form": "groundcover", "use": ["food"]},
    "herb":          {"form": "shrub", "use": ["food", "medicinal"]},
    "nitrogen_fixer":{"function": ["nitrogen_fixer"], "form": "UNKNOWN"},
    "pioneer":       {"function": ["pioneer"], "form": "UNKNOWN"},
    "ground_cover":  {"form": "groundcover"},
    "grass_bamboo":  {"form": "grass_grain"},
    "rootstock":     {"function": ["rootstock"], "form": "UNKNOWN"},
    "indicator":     {"form": "UNKNOWN"},
    "aquatic":       {"form": "aquatic_wetland"},
    "remediator":    {"form": "UNKNOWN"},
}

# ── Extended edge type map ─────────────────────────────────────────────────────

_EXTENDED_EDGE_MAP = {
    **LEGACY_EDGE_MAP,
    "G":           "grafting",
    "R":           "mulch_biomass",    # restores soil
    "E":           "soil_exhaust",     # exhausts soil
    "P":           "companion",        # pest-control companion
    "Ro":          "succession",       # rotation
    "friendship":  "companion",
    "hostility":   "hostile",
    "restores":    "mulch_biomass",
    "exhausts":    "soil_exhaust",
    "support":     "windbreak",
    # already-canonical pass-throughs (in case raw has them)
    "grafting":         "grafting",
    "windbreak":        "windbreak",
    "succession":       "succession",
    "nitrogen_fix":     "nitrogen_fix",
    "mulch_biomass":    "mulch_biomass",
    "soil_exhaust":     "soil_exhaust",
    "canopy_shade":     "canopy_shade",
    "water":            "water",
    "animal":           "animal",
}

_NITROGEN_KEYWORDS = {"nitrogen", "legume", "rhizobium", "frankia", "n-fix", "nodule"}
_MODERN_REC_KEYWORDS = {
    "ibn al-awwam", "east malling", "uc davis", "icarda", "modern reconstruction"
}


def _title_case(s: str) -> str:
    """Title-case a plant name, preserving existing capitalisation of all-caps words."""
    return " ".join(
        w if w.isupper() and len(w) > 1 else w.capitalize()
        for w in s.strip().split()
    )


def _apply_cat_map(node: dict, cat: str, inc_flags: list) -> None:
    """Apply category mapping rules to node in-place."""
    mapping = _EXTENDED_CAT_MAP.get(cat)
    if mapping is None:
        return

    if "kind" in mapping:
        node["kind"] = mapping["kind"]
    if "form" in mapping:
        if mapping["form"] == "UNKNOWN":
            if not node.get("form"):
                node["form"] = None          # leave as None; flag below
            if "INC-01" not in node["_flags"]:
                node["_flags"].append("INC-01")
                inc_flags.append("INC-01")
        else:
            if not node.get("form"):          # don't overwrite a better value
                node["form"] = mapping["form"]
    if "function" in mapping:
        node["function"] = list(set(node.get("function", []) + mapping["function"]))
    if "use" in mapping:
        node["use"] = list(set(node.get("use", []) + mapping["use"]))


def normalize(raw: dict) -> dict:
    inc_counter: Counter = Counter()
    extra_edges = []

    # ── Node normalization ─────────────────────────────────────────────────────
    norm_nodes = []
    for raw_node in raw.get("nodes", []):
        node = dict(raw_node)

        # 1. id → Title Case
        raw_id = str(node.get("id") or "").strip()
        if not raw_id:
            continue
        node["id"] = _title_case(raw_id)

        # Ensure required list/flag fields exist
        node.setdefault("kind", "plant")
        node.setdefault("form", None)
        node.setdefault("function", [])
        node.setdefault("use", [])
        node.setdefault("sources", node.pop("sources", []) or [])
        node.setdefault("evidence_level", "Uncertain")
        node.setdefault("_flags", [])

        fired = []

        # 2. cat → LEGACY_CAT_MAP (extended)
        cat = str(node.get("cat") or "").strip()
        if cat:
            _apply_cat_map(node, cat, fired)

        # 3. name_sci empty string → None
        sci = node.get("name_sci")
        if isinstance(sci, str) and sci.strip() == "":
            node["name_sci"] = None

        # 4. hub → clear form/function/use
        if node.get("kind") == "hub":
            node["form"] = None
            node["function"] = []
            node["use"] = []
            # remove INC-01 if it was set (hubs intentionally have no form)
            node["_flags"] = [f for f in node["_flags"] if f != "INC-01"]

        # 5. ensure evidence_level
        if not node.get("evidence_level"):
            node["evidence_level"] = "Uncertain"

        # 6. deduplicate function / use
        node["function"] = list(dict.fromkeys(node["function"]))
        node["use"] = list(dict.fromkeys(node["use"]))

        for f in fired:
            inc_counter[f] += 1

        norm_nodes.append(node)

    # ── Edge normalization ─────────────────────────────────────────────────────
    norm_edges = []
    for raw_edge in raw.get("edges", []):
        edge = dict(raw_edge)

        # Normalize source/target to Title Case
        edge["source"] = _title_case(str(edge.get("source") or ""))
        edge["target"] = _title_case(str(edge.get("target") or ""))

        # 1. type → LEGACY_EDGE_MAP → canonical
        raw_type = str(edge.get("type") or "").strip()
        canonical = _EXTENDED_EDGE_MAP.get(raw_type, raw_type)

        # 2. unknown type after mapping → INC-03
        if canonical not in EDGE_TYPES:
            edge["_flags"] = edge.get("_flags", []) + ["INC-03"]
            inc_counter["INC-03"] += 1
            edge["type"] = "unknown"
        else:
            edge["type"] = canonical

        # 3. soil_restore → mulch_biomass; maybe also emit nitrogen_fix
        if raw_type == "soil_restore" or raw_type == "R":
            edge["type"] = "mulch_biomass"
            note_text = (str(edge.get("note") or "") + " " +
                         str(edge.get("source_file") or "")).lower()
            if any(kw in note_text for kw in _NITROGEN_KEYWORDS):
                extra = dict(edge)
                extra["type"] = "nitrogen_fix"
                extra["added"] = False
                extra.setdefault("_flags", [])
                extra_edges.append(extra)

        # 4. evidence_level from source clues
        note_text = (str(edge.get("note") or "") + " " +
                     str(edge.get("source_file") or "")).lower()
        if "external" in str(edge.get("source_file") or "").lower() or \
                any(kw in note_text for kw in _MODERN_REC_KEYWORDS):
            edge["evidence_level"] = "Modern reconstruction"
            edge["added"] = False
        else:
            edge.setdefault("evidence_level", "Uncertain")

        # 5. default confidence
        if not edge.get("confidence"):
            edge["confidence"] = 0.5

        edge.setdefault("_flags", [])
        edge.setdefault("added", False)
        edge.setdefault("direction", "directed")
        edge.setdefault("context", [])
        edge.setdefault("source_id", edge.get("source_file", ""))
        edge.setdefault("evidence_quote", None)

        norm_edges.append(edge)

    norm_edges.extend(extra_edges)

    result = {"nodes": norm_nodes, "edges": norm_edges}

    out_path = Path("output/normalized.json")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    return result


def _report(result: dict, inc_counter: Counter) -> None:
    edges = result["edges"]
    type_dist = Counter(e["type"] for e in edges)
    unknown = type_dist.get("unknown", 0)

    print("=== INC flags fired ===")
    for flag, count in sorted(inc_counter.items()):
        print(f"  {flag}: {count}")

    print("\n=== Edge type distribution ===")
    for t, c in type_dist.most_common():
        print(f"  {t}: {c}")

    print(f"\nunknown edges: {unknown}")
    if unknown == 0:
        print("PASS — zero unknown-type edges")
    else:
        flagged = sum(1 for e in edges if e["type"] == "unknown" and "INC-03" in e.get("_flags", []))
        if flagged == unknown:
            print(f"PASS — {unknown} unknown-type edges, all flagged INC-03")
        else:
            print(f"FAIL — {unknown} unknown-type edges, only {flagged} flagged")


if __name__ == "__main__":
    raw_path = Path("output/raw_extracted.json")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))

    inc_counter: Counter = Counter()

    # Monkey-patch to capture inc_counter from inside normalize()
    _orig_normalize = normalize

    def _patched(raw):
        result = _orig_normalize(raw)
        # Re-count from output
        for node in result["nodes"]:
            for f in node.get("_flags", []):
                inc_counter[f] += 1
        for edge in result["edges"]:
            for f in edge.get("_flags", []):
                inc_counter[f] += 1
        return result

    result = _patched(raw)
    _report(result, inc_counter)
