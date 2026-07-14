"""
pipeline/finaledge.py
Dedup enriched_edges.json with the same rededge logic, then merge with
master_edges.json, skipping existing (source, target, type) triples.
Writes output/final_edges.json.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

from pipeline.rededge import (
    UNDIRECTED_TYPES,
    _build_dedup_map,
    _merge_group,
    _resolve,
)


def run(out_dir: str = "output"):
    out = Path(out_dir)

    normalized = json.loads((out / "normalized.json").read_text(encoding="utf-8"))
    merged     = json.loads((out / "merged.json").read_text(encoding="utf-8"))
    master     = json.loads((out / "master_edges.json").read_text(encoding="utf-8"))
    enriched   = json.loads((out / "enriched_edges.json").read_text(encoding="utf-8"))

    master_count   = len(master)
    enriched_count = len(enriched)

    # ── Build dedup map ───────────────────────────────────────────────────────
    dedup = _build_dedup_map(normalized["nodes"], merged["nodes"])

    # ── Dedup enriched_edges.json (same pipeline as rededge) ─────────────────
    for edge in enriched:
        edge["source"] = _resolve(edge["source"], dedup)
        edge["target"] = _resolve(edge["target"], dedup)
        if edge.get("type") in UNDIRECTED_TYPES:
            edge["direction"] = "undirected"
            if edge["source"] > edge["target"]:
                edge["source"], edge["target"] = edge["target"], edge["source"]

    groups: dict[tuple, list] = defaultdict(list)
    for edge in enriched:
        key = (edge["source"], edge["target"], edge["type"])
        groups[key].append(edge)

    deduped_enriched = [_merge_group(g) for g in groups.values()]

    # ── Build existing triple set from master_edges ───────────────────────────
    existing: set[tuple] = {
        (e["source"], e["target"], e["type"]) for e in master
    }

    # ── Merge: add enriched edges not already in master ───────────────────────
    final = list(master)
    dupes_skipped = 0

    for edge in deduped_enriched:
        triple = (edge["source"], edge["target"], edge["type"])
        if triple in existing:
            dupes_skipped += 1
        else:
            final.append(edge)
            existing.add(triple)

    # ── Write output ──────────────────────────────────────────────────────────
    (out / "final_edges.json").write_text(
        json.dumps(final, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return {
        "master_count":   master_count,
        "enriched_count": enriched_count,
        "dupes_skipped":  dupes_skipped,
        "final_count":    len(final),
    }


if __name__ == "__main__":
    stats = run()
    print(f"master_count={stats['master_count']}")
    print(f"enriched_count={stats['enriched_count']}")
    print(f"dupes_skipped={stats['dupes_skipped']}")
    print(f"final_count={stats['final_count']}")
