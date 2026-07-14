"""
pipeline/rededge.py
Remap, deduplicate, and merge master_edges.json using the node dedup map
from merged.json, then overwrite output/master_edges.json.

Steps:
  1. Rebuild canonical id map from normalized.json → merged.json
  2. Remap edge source/target to canonical ids
  3. Standardize direction for undirected types (companion, water, animal)
  4. Group by (source, target, type) and merge duplicates
  5. Overwrite output/master_edges.json
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

# Undirected edge types: sort source/target alphabetically so A→B ≡ B→A
UNDIRECTED_TYPES = {"companion", "water", "animal"}

# Evidence hierarchy (higher = stronger)
_EV_RANK = {
    "Uncertain": 1,
    "Modern reconstruction": 2,
    "Strongly implied": 3,
    "Explicit": 4,
}

# Origin hierarchy (higher = more authoritative)
_ORIGIN_RANK = {
    "enriched": 1,
    "factcheck": 2,
    "dataset": 3,
}


def _ev_rank(v):
    return _EV_RANK.get(v or "Uncertain", 1)


def _origin_rank(v):
    return _ORIGIN_RANK.get(v or "enriched", 1)


def _build_dedup_map(normalized_nodes: list, merged_nodes: list) -> dict:
    """
    Return {variant_id_lower: canonical_id} for every normalized id whose
    canonical form in merged.json differs (case or frequency-chosen name).
    Also covers name_sci and name_ar cross-matches.
    """
    merged_by_lower = {n["id"].lower(): n["id"] for n in merged_nodes}
    merged_by_sci   = {n["name_sci"]: n["id"]
                       for n in merged_nodes if n.get("name_sci")}
    merged_by_ar    = {n["name_ar"]: n["id"]
                       for n in merged_nodes if n.get("name_ar")}

    dedup: dict[str, str] = {}

    for node in normalized_nodes:
        nid = node.get("id", "").strip()
        if not nid:
            continue

        # id case-insensitive match
        canonical = merged_by_lower.get(nid.lower())
        if canonical and canonical != nid:
            dedup[nid] = canonical

        # name_sci match
        sci = node.get("name_sci", "")
        if sci and sci in merged_by_sci:
            canonical = merged_by_sci[sci]
            if canonical != nid:
                dedup[nid] = canonical

        # name_ar match
        ar = node.get("name_ar", "")
        if ar and ar in merged_by_ar:
            canonical = merged_by_ar[ar]
            if canonical != nid:
                dedup[nid] = canonical

    return dedup


def _resolve(name: str, dedup: dict) -> str:
    return dedup.get(name, name)


def _merge_group(group: list) -> dict:
    """Merge a list of duplicate edges into one canonical edge."""
    if len(group) == 1:
        return dict(group[0])

    base = dict(group[0])

    # context: union, deduplicate
    ctx = []
    for e in group:
        ctx.extend(e.get("context") or [])
    base["context"] = list(dict.fromkeys(ctx))

    # flags: union, deduplicate
    flags = []
    for e in group:
        flags.extend(e.get("flags") or [])
    base["flags"] = list(dict.fromkeys(flags))

    # evidence_level: keep highest rank
    base["evidence_level"] = max(
        (e.get("evidence_level") or "Uncertain" for e in group),
        key=_ev_rank
    )

    # added: false beats true — if any source edge was not added, result is not-added
    base["added"] = all(e.get("added", False) for e in group)

    # origin: dataset > factcheck > enriched (keep highest rank)
    base["origin"] = max(
        (e.get("origin") or "enriched" for e in group),
        key=_origin_rank
    )

    # evidence_quote: join non-null values with |
    quotes = [e["evidence_quote"] for e in group
              if e.get("evidence_quote")]
    base["evidence_quote"] = " | ".join(dict.fromkeys(quotes)) or None

    # confidence: numeric max
    base["confidence"] = max(
        (float(e.get("confidence") or 0.5) for e in group)
    )

    return base


def run(out_dir: str = "output"):
    out = Path(out_dir)

    normalized = json.loads((out / "normalized.json").read_text(encoding="utf-8"))
    merged     = json.loads((out / "merged.json").read_text(encoding="utf-8"))
    edges      = json.loads((out / "master_edges.json").read_text(encoding="utf-8"))

    edges_before = len(edges)

    # ── Step 1: Build dedup map ───────────────────────────────────────────────
    dedup = _build_dedup_map(normalized["nodes"], merged["nodes"])
    print(f"dedup map entries: {len(dedup)}", file=sys.stderr)

    # ── Step 2: Remap source/target ───────────────────────────────────────────
    edges_remapped = 0
    for edge in edges:
        new_src = _resolve(edge["source"], dedup)
        new_tgt = _resolve(edge["target"], dedup)
        if new_src != edge["source"] or new_tgt != edge["target"]:
            edge["source"] = new_src
            edge["target"] = new_tgt
            edges_remapped += 1

    # ── Step 3: Standardize direction for undirected types ────────────────────
    for edge in edges:
        if edge.get("type") in UNDIRECTED_TYPES:
            edge["direction"] = "undirected"
            if edge["source"] > edge["target"]:
                edge["source"], edge["target"] = edge["target"], edge["source"]

    # ── Step 4: Group and merge duplicates ────────────────────────────────────
    groups: dict[tuple, list] = defaultdict(list)
    for edge in edges:
        key = (edge["source"], edge["target"], edge["type"])
        groups[key].append(edge)

    merged_edges = []
    dupes_merged = 0
    for key, group in groups.items():
        if len(group) > 1:
            dupes_merged += len(group) - 1
        merged_edges.append(_merge_group(group))

    # ── Step 5: Overwrite master_edges.json ───────────────────────────────────
    (out / "master_edges.json").write_text(
        json.dumps(merged_edges, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return {
        "edges_before":   edges_before,
        "edges_remapped": edges_remapped,
        "dupes_merged":   dupes_merged,
        "final_count":    len(merged_edges),
    }


if __name__ == "__main__":
    stats = run()
    print(f"edges_before={stats['edges_before']}")
    print(f"edges_remapped={stats['edges_remapped']}")
    print(f"dupes_merged={stats['dupes_merged']}")
    print(f"final_count={stats['final_count']}")
