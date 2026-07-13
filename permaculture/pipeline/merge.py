"""
Step 3 — merge.py
Entry point: merge(normalized: dict) -> dict
Reads:  output/normalized.json
Writes: output/merged.json
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from pipeline.schemas import EDGE_TYPES

# Evidence strength ordering (higher index = stronger)
_EV_RANK = {
    "Uncertain": 0,
    "Modern reconstruction": 1,
    "Strongly implied": 2,
    "Explicit": 3,
}

# Source files considered "Islamic agronomy dataset" — authoritative for form conflicts
_ISLAMIC_SOURCES = {
    "islamic_agronomy_network.html",
    "islamic_agronomy_network_corrected.html",
    "islamic_agronomy_plant_catalog.html",
    "islamic_agronomy_verified_reference.html",
    "islamic_plant_catalog_v2.html",
    "conversation.json",
}


def _ev_strength(ev: str) -> int:
    return _EV_RANK.get(ev, 0)


def _strongest_ev(*evs):
    return max(evs, key=_ev_strength)


def _is_islamic_source(node: dict) -> bool:
    return node.get("source_file", "") in _ISLAMIC_SOURCES


# ── Union-Find for grouping duplicate nodes ────────────────────────────────────

class _UF:
    def __init__(self):
        self._parent = {}

    def find(self, x):
        self._parent.setdefault(x, x)
        if self._parent[x] != x:
            self._parent[x] = self.find(self._parent[x])
        return self._parent[x]

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._parent[rb] = ra


def _merge_two_nodes(a: dict, b: dict) -> dict:
    """Merge node b into node a, returning the merged result."""
    merged = dict(a)
    flags = list(dict.fromkeys(a.get("_flags", []) + b.get("_flags", [])))

    # id: keep most frequent (handled at group level); no action here

    # form conflict
    fa, fb = a.get("form"), b.get("form")
    if fa and fb and fa != fb:
        if "INC-09" not in flags:
            flags.append("INC-09")
        # keep the one from the Islamic agronomy dataset
        if _is_islamic_source(b) and not _is_islamic_source(a):
            merged["form"] = fb
        # else keep a's form (already in merged)
    elif fb and not fa:
        merged["form"] = fb

    # function / use → union (preserve order)
    merged["function"] = list(dict.fromkeys(
        (a.get("function") or []) + (b.get("function") or [])
    ))
    merged["use"] = list(dict.fromkeys(
        (a.get("use") or []) + (b.get("use") or [])
    ))

    # sources → union
    merged["sources"] = list(dict.fromkeys(
        (a.get("sources") or []) + (b.get("sources") or [])
    ))

    # evidence_level → strongest
    merged["evidence_level"] = _strongest_ev(
        a.get("evidence_level", "Uncertain"),
        b.get("evidence_level", "Uncertain"),
    )

    # name_ar / name_sci → keep non-null; flag conflict
    for field in ("name_ar", "name_sci"):
        va, vb = a.get(field), b.get(field)
        if va and vb and va != vb:
            flag = "INC-13"
            if flag not in flags:
                flags.append(flag)
            # keep a's value (first encountered)
        elif vb and not va:
            merged[field] = vb

    # kind — prefer non-plant if either is hub/animal
    if b.get("kind") in ("hub", "animal"):
        merged["kind"] = b["kind"]

    # notes — keep non-null
    if not merged.get("notes") and b.get("notes"):
        merged["notes"] = b["notes"]

    merged["_flags"] = flags
    return merged


def merge(normalized: dict) -> dict:
    nodes_in = normalized.get("nodes", [])
    edges_in = normalized.get("edges", [])

    nodes_before = len(nodes_in)
    edges_before = len(edges_in)

    # ── Build lookup indices ───────────────────────────────────────────────────
    # Assign each node an integer index
    uf = _UF()

    # Index by id (case-insensitive)
    id_to_idx: dict[str, int] = {}       # lower(id) → first node index
    sci_to_idx: dict[str, int] = {}      # name_sci → first node index
    ar_to_idx: dict[str, int] = {}       # name_ar  → first node index

    for i, node in enumerate(nodes_in):
        node_id = str(node.get("id") or "").strip()
        if not node_id:
            continue
        uf.find(i)

        lid = node_id.lower()
        if lid in id_to_idx:
            uf.union(id_to_idx[lid], i)
        else:
            id_to_idx[lid] = i

        sci = str(node.get("name_sci") or "").strip()
        if sci:
            if sci in sci_to_idx:
                uf.union(sci_to_idx[sci], i)
            else:
                sci_to_idx[sci] = i

        ar = str(node.get("name_ar") or "").strip()
        if ar:
            if ar in ar_to_idx:
                uf.union(ar_to_idx[ar], i)
            else:
                ar_to_idx[ar] = i

    # ── Group nodes by root ────────────────────────────────────────────────────
    groups: dict[int, list] = defaultdict(list)
    for i, node in enumerate(nodes_in):
        if not str(node.get("id") or "").strip():
            continue
        groups[uf.find(i)].append(node)

    # ── Merge each group into one canonical node ───────────────────────────────
    merged_nodes = []
    canonical_id_map: dict[str, str] = {}   # any lower(id) → canonical id

    for group in groups.values():
        if not group:
            continue
        if len(group) == 1:
            merged = dict(group[0])
            merged.setdefault("isolated", False)
            merged_nodes.append(merged)
            canonical_id_map[merged["id"].lower()] = merged["id"]
            continue

        # Pick canonical id: most frequent across the group; tie → alphabetical
        id_freq: Counter = Counter()
        for n in group:
            nid = str(n.get("id") or "").strip()
            if nid:
                id_freq[nid] += 1
        canonical_id = min(
            id_freq,
            key=lambda x: (-id_freq[x], x.lower())
        )

        # Register all variant ids → canonical
        for n in group:
            nid = str(n.get("id") or "").strip()
            if nid:
                canonical_id_map[nid.lower()] = canonical_id

        # Sort: Islamic sources first (most authoritative)
        group_sorted = sorted(group, key=lambda n: (0 if _is_islamic_source(n) else 1))
        base = dict(group_sorted[0])
        base["id"] = canonical_id
        base.setdefault("isolated", False)

        for other in group_sorted[1:]:
            base = _merge_two_nodes(base, other)

        base["id"] = canonical_id
        base.setdefault("isolated", False)
        merged_nodes.append(base)

    # ── Edge dedup and remapping ───────────────────────────────────────────────
    def _resolve_id(raw_id: str) -> str:
        return canonical_id_map.get(raw_id.lower(), raw_id)

    # Group edges by (source, target, type)
    edge_groups: dict[tuple, list] = defaultdict(list)
    for edge in edges_in:
        src = _resolve_id(str(edge.get("source") or ""))
        tgt = _resolve_id(str(edge.get("target") or ""))
        etype = edge.get("type", "unknown")
        key = (src, tgt, etype)
        edge_groups[key].append(edge)

    merged_edges = []
    for (src, tgt, etype), group in edge_groups.items():
        if len(group) == 1:
            e = dict(group[0])
            e["source"] = src
            e["target"] = tgt
            merged_edges.append(e)
            continue
        # Merge: highest confidence, union context + flags
        best = max(group, key=lambda e: e.get("confidence", 0.5))
        merged_e = dict(best)
        merged_e["source"] = src
        merged_e["target"] = tgt
        # union context
        ctx = []
        for e in group:
            ctx.extend(e.get("context", []))
        merged_e["context"] = list(dict.fromkeys(ctx))
        # union flags
        flags = []
        for e in group:
            flags.extend(e.get("_flags", []))
        merged_e["_flags"] = list(dict.fromkeys(flags))
        # strongest evidence
        evs = [e.get("evidence_level", "Uncertain") for e in group]
        merged_e["evidence_level"] = max(evs, key=_ev_strength)
        merged_edges.append(merged_e)

    # ── Isolated node detection ────────────────────────────────────────────────
    connected_ids: set[str] = set()
    for e in merged_edges:
        connected_ids.add(e["source"])
        connected_ids.add(e["target"])

    isolated_count = 0
    for node in merged_nodes:
        if node["id"] not in connected_ids:
            node["isolated"] = True
            isolated_count += 1
        else:
            node["isolated"] = False

    result = {"nodes": merged_nodes, "edges": merged_edges}

    out_path = Path("output/merged.json")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    return result, nodes_before, edges_before, isolated_count


if __name__ == "__main__":
    norm_path = Path("output/normalized.json")
    normalized = json.loads(norm_path.read_text(encoding="utf-8"))

    result, nodes_before, edges_before, isolated_count = merge(normalized)

    nodes_after = len(result["nodes"])
    edges_after = len(result["edges"])

    # Verify no duplicate (source, target, type) triples
    triples = [(e["source"], e["target"], e["type"]) for e in result["edges"]]
    dup_triples = len(triples) - len(set(triples))

    print(f"nodes_before={nodes_before}")
    print(f"nodes_after={nodes_after}")
    print(f"edges_before={edges_before}")
    print(f"edges_after={edges_after}")
    print(f"isolated_count={isolated_count}")
    print(f"duplicate_triples={dup_triples}")

    ok_dedup = nodes_after < nodes_before
    ok_triples = dup_triples == 0

    if ok_dedup and ok_triples:
        print("PASS")
    else:
        if not ok_dedup:
            print(f"FAIL — nodes_after ({nodes_after}) not < nodes_before ({nodes_before})")
        if not ok_triples:
            print(f"FAIL — {dup_triples} duplicate (source,target,type) triples remain")
