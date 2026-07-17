"""
pipeline/restructure_hubs.py
Restructures hub nodes in master_nodes.json + final_edges.json:
  1. Rename PIONEER ZONE / CLIMAX ZONE
  2. Create SALINE SOIL hub + halophyte edges
  3. Rename WATER → FRESHWATER, move halophyte water edges
  4. Rename SOIL → SOIL FERTILITY
  5. Enforce succession direction for BARE GROUND / MATURE CANOPY
  6. Dissolve non-canonical hubs
  7. Tag pest-deterrent plants
  8. Dedup + validate, write
"""
import copy, json, sys
from pathlib import Path

# ── constants ────────────────────────────────────────────────────────────────

CANONICAL_HUBS = {"SOIL FERTILITY", "FRESHWATER", "SALINE SOIL", "BARE GROUND", "MATURE CANOPY"}

HALOPHYTES = [
    "Tamarisk", "Tamarisk Tree", "Glasswort Ash", "Glasswort Saline",
    "Glasswort (ash Source)", "Glasswort (saline)", "Sea Blite", "Orach",
    "Samphire", "Date Palm", "Doum Palm", "Barley", "Chard / Beet",
    "Asparagus", "Mangroves", "Sea Purslane", "Ice Plant",
]
HALOPHYTE_SET = set(HALOPHYTES)
HALOPHYTE_KEEP_FRESHWATER = {"Mangroves", "Date Palm"}

PEST_DETERRENT = [
    "Rue", "Wormwood", "Southernwood", "Elecampane", "Pennyroyal",
    "Basil", "Garlic", "Onion", "Nasturtium", "Marigold", "Castor", "Colocynth",
    "Squill", "Squill / Sea Onion", "Oleander", "Henbane", "Datura",
    "Datura / Thorn Apple", "Stavesacre", "White Hellebore", "Black Hellebore",
    "Asafoetida", "Euphorbia", "Neem", "Lemongrass", "Costus Root", "Sweet Flag",
    "Bay / Laurel", "Bay Laurel", "Juniper", "Sage", "Thyme",
]

DISSOLVE = {
    "Waterways":                       "FRESHWATER",
    "Irrigation Canals / Wet Crops":   "FRESHWATER",
    "Date Palm Gardens; Saline Areas": "SALINE SOIL",
    "Field Crops (general)":           "SOIL FERTILITY",
    "Storage General":                 "SOIL FERTILITY",
    "Stored Grain":                    "SOIL FERTILITY",
    "Grain Stores":                    "SOIL FERTILITY",
    "Nearby Annuals":                  "SOIL FERTILITY",
    "General Aromatic Windbreak":      "SOIL FERTILITY",
    "General Garden / Orchard":        "SOIL FERTILITY",
    "Most Plants (general)":           "SOIL FERTILITY",
}

REAL_CEREALS = ["Wheat", "Barley", "Oats", "Rye", "Sorghum", "Rice",
                "Emmer Wheat", "Einkorn", "Spelt"]

EV_ORDER = {"Explicit": 0, "Strongly implied": 1, "Modern reconstruction": 2, "Uncertain": 3}


# ── helpers ───────────────────────────────────────────────────────────────────

def ev_stronger(a, b):
    return a if EV_ORDER.get(a, 99) <= EV_ORDER.get(b, 99) else b


def rename_everywhere(nodes, edges, old_id, new_id):
    """Rename a node id and patch every edge referencing it."""
    for n in nodes:
        if n["id"] == old_id:
            n["id"] = new_id
    for e in edges:
        if e["source"] == old_id:
            e["source"] = new_id
        if e["target"] == old_id:
            e["target"] = new_id


def make_edge(src, tgt, etype, **kw):
    return {
        "source": src, "target": tgt, "type": etype,
        "direction":      kw.get("direction", "directed"),
        "context":        kw.get("context", []),
        "source_id":      kw.get("source_id", ""),
        "evidence_level": kw.get("evidence_level", "Modern reconstruction"),
        "evidence_quote": kw.get("evidence_quote", None),
        "confidence":     kw.get("confidence", 0.8),
        "added":          kw.get("added", True),
        "flags":          kw.get("flags", []),
        "origin":         kw.get("origin", "restructure"),
        **({} if "note" not in kw else {"note": kw["note"]}),
    }


def dissolve_hub(nodes, edges, old_hub, target, stats):
    """Replace every edge endpoint old_hub → target, remove node."""
    nids = {n["id"] for n in nodes}
    if old_hub not in nids:
        return
    remapped = 0
    for e in edges:
        if e["source"] == old_hub:
            e["source"] = target
            remapped += 1
        if e["target"] == old_hub:
            e["target"] = target
            remapped += 1
    nodes[:] = [n for n in nodes if n["id"] != old_hub]
    stats["hubs_dissolved"] += 1
    stats["edges_remapped"] += remapped


def expand_hub(nodes, edges, hub_id, targets, stats, label=""):
    """
    For each edge touching hub_id, replicate it once per target node that
    exists, then delete the original edges and the hub node.
    """
    nids = {n["id"] for n in nodes}
    real_targets = [t for t in targets if t in nids]
    if not real_targets:
        print(f"  EXPAND '{hub_id}': no target nodes exist in graph — skipping", file=sys.stderr)
        return

    hub_edges = [e for e in edges if e["source"] == hub_id or e["target"] == hub_id]
    keep_edges = [e for e in edges if e["source"] != hub_id and e["target"] != hub_id]
    new_edges = []
    for e_orig in hub_edges:
        for t in real_targets:
            new_e = copy.deepcopy(e_orig)
            if new_e["source"] == hub_id:
                new_e["source"] = t
            if new_e["target"] == hub_id:
                new_e["target"] = t
            new_e["origin"] = "restructure"
            new_edges.append(new_e)
            if label == "cereal":
                stats["cereals_expanded"] += 1

    edges[:] = keep_edges + new_edges
    nodes[:] = [n for n in nodes if n["id"] != hub_id]
    stats["hubs_dissolved"] += 1
    print(f"  EXPANDED '{hub_id}' → {real_targets} ({len(hub_edges)} edges × {len(real_targets)} targets = {len(new_edges)} new edges)", file=sys.stderr)


# ── main ──────────────────────────────────────────────────────────────────────

def run(out_dir="output"):
    out = Path(out_dir)
    nodes = json.loads((out / "master_nodes.json").read_text(encoding="utf-8"))
    edges = json.loads((out / "final_edges.json").read_text(encoding="utf-8"))

    stats = dict(
        hubs_renamed=0, halophyte_edges_added=0, hubs_dissolved=0,
        cereals_expanded=0, succession_edges_fixed=0, pest_tagged=0,
        edges_remapped=0, dupes_removed=0, self_edges_removed=0,
        final_node_count=0, final_edge_count=0, isolated_count=0,
        any_unhandled_hubs=[],
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 1 — Rename succession hubs
    # ─────────────────────────────────────────────────────────────────────────
    for old, new in [("PIONEER ZONE", "BARE GROUND"), ("CLIMAX ZONE", "MATURE CANOPY")]:
        rename_everywhere(nodes, edges, old, new)
        stats["hubs_renamed"] += 1
        print(f"  RENAME '{old}' → '{new}'", file=sys.stderr)

    # ─────────────────────────────────────────────────────────────────────────
    # Step 2 — Create SALINE SOIL hub + halophyte companion edges
    # ─────────────────────────────────────────────────────────────────────────
    nodes.append({
        "id": "SALINE SOIL", "kind": "hub", "name_ar": None,
        "name_sci": "Salt-affected ground",
        "form": None, "function": [], "use": [], "sources": [],
        "evidence_level": "Modern reconstruction", "isolated": False,
        "added": True, "flags": [],
        "notes": "Halophyte tolerance and salt-land remediation",
        "water_need": "medium",
    })
    nids = {n["id"] for n in nodes}
    for plant in HALOPHYTES:
        if plant in nids:
            edges.append(make_edge(plant, "SALINE SOIL", "companion",
                                   confidence=0.8))
            stats["halophyte_edges_added"] += 1

    # ─────────────────────────────────────────────────────────────────────────
    # Step 3 — Rename WATER → FRESHWATER; move halophyte water edges
    # ─────────────────────────────────────────────────────────────────────────
    rename_everywhere(nodes, edges, "WATER", "FRESHWATER")
    stats["hubs_renamed"] += 1

    # Halophytes whose water→FRESHWATER edges should move to SALINE SOIL
    keep, moved = [], []
    for e in edges:
        if e["type"] == "water":
            src, tgt = e["source"], e["target"]
            if tgt == "FRESHWATER" and src in HALOPHYTE_SET and src not in HALOPHYTE_KEEP_FRESHWATER:
                new_e = copy.deepcopy(e)
                new_e["target"] = "SALINE SOIL"
                new_e["origin"] = "restructure"
                moved.append(new_e)
                continue  # drop original FRESHWATER edge
            if src == "FRESHWATER" and tgt in HALOPHYTE_SET and tgt not in HALOPHYTE_KEEP_FRESHWATER:
                new_e = copy.deepcopy(e)
                new_e["source"] = "SALINE SOIL"
                new_e["origin"] = "restructure"
                moved.append(new_e)
                continue
        keep.append(e)
    edges[:] = keep + moved
    print(f"  Moved {len(moved)} halophyte water edges FRESHWATER→SALINE SOIL", file=sys.stderr)

    # ─────────────────────────────────────────────────────────────────────────
    # Step 4 — Rename SOIL → SOIL FERTILITY
    # ─────────────────────────────────────────────────────────────────────────
    rename_everywhere(nodes, edges, "SOIL", "SOIL FERTILITY")
    stats["hubs_renamed"] += 1
    print("  RENAME 'SOIL' → 'SOIL FERTILITY'", file=sys.stderr)

    # ─────────────────────────────────────────────────────────────────────────
    # Step 5 — Enforce succession direction for BARE GROUND / MATURE CANOPY
    # ─────────────────────────────────────────────────────────────────────────
    BG, MC = "BARE GROUND", "MATURE CANOPY"
    succ_hubs = {BG, MC}
    keep, drop = [], []
    for e in edges:
        if e["type"] != "succession":
            keep.append(e)
            continue
        src, tgt = e["source"], e["target"]
        if src in succ_hubs and tgt in succ_hubs:
            # BG ↔ MC — drop entirely; we'll add the canonical one below
            drop.append(e)
        elif src in succ_hubs:
            # hub is source (e.g. "BARE GROUND → Plant") → flip to Plant → BARE GROUND
            e["source"], e["target"] = tgt, src
            e["direction"] = "directed"
            stats["succession_edges_fixed"] += 1
            keep.append(e)
        elif tgt in succ_hubs:
            # already [plant] → [hub] — correct
            e["direction"] = "directed"
            stats["succession_edges_fixed"] += 1
            keep.append(e)
        else:
            keep.append(e)

    edges[:] = keep
    print(f"  Dropped {len(drop)} BG↔MC succession edge(s)", file=sys.stderr)

    # Add exactly one canonical BG → MC edge
    edges.append(make_edge(BG, MC, "succession", confidence=0.9,
                           note="Ecological succession: disturbed ground matures into established canopy"))

    # ─────────────────────────────────────────────────────────────────────────
    # Step 6 — Dissolve non-canonical hubs
    # ─────────────────────────────────────────────────────────────────────────
    nids = {n["id"] for n in nodes}

    # 6a DISSOLVE mapping
    for old_hub, target in DISSOLVE.items():
        if old_hub in nids:
            dissolve_hub(nodes, edges, old_hub, target, stats)
            nids.discard(old_hub)
            print(f"  DISSOLVE '{old_hub}' → '{target}'", file=sys.stderr)

    # 6b Expand Any Cereal / Cereal (general)
    nids = {n["id"] for n in nodes}
    real_cereals_exist = [c for c in REAL_CEREALS if c in nids]
    for hub_id in ["Any Cereal", "Cereal (general)"]:
        if hub_id in nids:
            expand_hub(nodes, edges, hub_id, real_cereals_exist, stats, label="cereal")
            nids.discard(hub_id)

    # 6c Wild Fig (caprifig) → Wild Fig
    nids = {n["id"] for n in nodes}
    if "Wild Fig (caprifig)" in nids:
        if "Wild Fig" in nids:
            dissolve_hub(nodes, edges, "Wild Fig (caprifig)", "Wild Fig", stats)
            nids.discard("Wild Fig (caprifig)")
            print("  DISSOLVE 'Wild Fig (caprifig)' → 'Wild Fig'", file=sys.stderr)
        else:
            print("  WARNING: 'Wild Fig' not found — leaving 'Wild Fig (caprifig)'", file=sys.stderr)
            stats["any_unhandled_hubs"].append("Wild Fig (caprifig)")

    # 6d Fish & Silkworms → expand to Fish + Silkworms
    nids = {n["id"] for n in nodes}
    if "Fish & Silkworms" in nids:
        expand_hub(nodes, edges, "Fish & Silkworms", ["Fish", "Silkworms"], stats)
        nids.discard("Fish & Silkworms")

    # 6e Remaining combo nodes (id contains ", " and kind == "hub")
    nids = {n["id"] for n in nodes}
    remaining_hubs = [n for n in nodes if n["kind"] == "hub" and n["id"] not in CANONICAL_HUBS]
    for h in remaining_hubs:
        hid = h["id"]
        if ", " in hid:
            parts = [p.strip() for p in hid.split(", ")]
            print(f"  COMBO DISSOLVE: '{hid}' → parts {parts}", file=sys.stderr)
            expand_hub(nodes, edges, hid, parts, stats)
            nids.discard(hid)
        else:
            stats["any_unhandled_hubs"].append(hid)
            print(f"  UNHANDLED HUB (leaving): '{hid}'", file=sys.stderr)

    # ─────────────────────────────────────────────────────────────────────────
    # Step 7 — Tag pest-deterrent plants
    # ─────────────────────────────────────────────────────────────────────────
    nmap = {n["id"]: n for n in nodes}
    for plant in PEST_DETERRENT:
        if plant in nmap:
            fn = nmap[plant].setdefault("function", [])
            if "pest_deterrent" not in fn:
                fn.append("pest_deterrent")
                stats["pest_tagged"] += 1

    # ─────────────────────────────────────────────────────────────────────────
    # Step 8 — Dedup + validate
    # ─────────────────────────────────────────────────────────────────────────
    nids_final = {n["id"] for n in nodes}

    # Self-edges
    before = len(edges)
    edges = [e for e in edges if e["source"] != e["target"]]
    stats["self_edges_removed"] = before - len(edges)

    # Dangling endpoints
    before = len(edges)
    edges = [e for e in edges if e["source"] in nids_final and e["target"] in nids_final]
    dangling = before - len(edges)
    if dangling:
        print(f"  Removed {dangling} dangling edges", file=sys.stderr)

    # Dedup on (source, target, type) — merge duplicates
    seen: dict = {}
    for e in edges:
        key = (e["source"], e["target"], e["type"])
        if key not in seen:
            seen[key] = copy.deepcopy(e)
        else:
            ex = seen[key]
            ex["context"] = list(set((ex.get("context") or []) + (e.get("context") or [])))
            ex["flags"]   = list(set((ex.get("flags")   or []) + (e.get("flags")   or [])))
            ex["evidence_level"] = ev_stronger(
                ex.get("evidence_level", "Uncertain"), e.get("evidence_level", "Uncertain"))
            ex["confidence"] = max(ex.get("confidence", 0.5), e.get("confidence", 0.5))
            if not e.get("added", True):          # false beats true
                ex["added"] = False

    deduped = list(seen.values())
    stats["dupes_removed"] = len(edges) - len(deduped)
    edges = deduped

    # Recompute isolated
    has_edge: set = set()
    for e in edges:
        has_edge.add(e["source"])
        has_edge.add(e["target"])
    for n in nodes:
        n["isolated"] = n["id"] not in has_edge

    # ── Validation ────────────────────────────────────────────────────────────
    hub_ids_actual = {n["id"] for n in nodes if n["kind"] == "hub"}
    assert hub_ids_actual == CANONICAL_HUBS, (
        f"Hub mismatch.\n  Expected: {sorted(CANONICAL_HUBS)}\n  Got:      {sorted(hub_ids_actual)}")

    nids_final = {n["id"] for n in nodes}
    for e in edges:
        assert e["source"] in nids_final, f"Missing source node: {e['source']}"
        assert e["target"] in nids_final, f"Missing target node: {e['target']}"
        assert e["source"] != e["target"], f"Self-edge survived: {e['source']}"

    triples = [(e["source"], e["target"], e["type"]) for e in edges]
    assert len(triples) == len(set(triples)), "Duplicate (source, target, type) triples found"

    bg_mc = [e for e in edges if e["source"] == BG and e["target"] == MC and e["type"] == "succession"]
    assert len(bg_mc) == 1, f"Expected exactly 1 BG→MC succession edge, got {len(bg_mc)}"

    print("  All validations PASS", file=sys.stderr)

    # ── Write ─────────────────────────────────────────────────────────────────
    (out / "master_nodes.json").write_text(
        json.dumps(nodes, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "final_edges.json").write_text(
        json.dumps(edges, ensure_ascii=False, indent=2), encoding="utf-8")

    stats["final_node_count"] = len(nodes)
    stats["final_edge_count"] = len(edges)
    stats["isolated_count"]   = sum(1 for n in nodes if n["isolated"])
    return stats


if __name__ == "__main__":
    stats = run()
    print(f"hubs_renamed={stats['hubs_renamed']}")
    print(f"halophyte_edges_added={stats['halophyte_edges_added']}")
    print(f"hubs_dissolved={stats['hubs_dissolved']}")
    print(f"cereals_expanded={stats['cereals_expanded']}")
    print(f"succession_edges_fixed={stats['succession_edges_fixed']}")
    print(f"pest_tagged={stats['pest_tagged']}")
    print(f"edges_remapped={stats['edges_remapped']}")
    print(f"dupes_removed={stats['dupes_removed']}")
    print(f"self_edges_removed={stats['self_edges_removed']}")
    print(f"final_node_count={stats['final_node_count']}")
    print(f"final_edge_count={stats['final_edge_count']}")
    print(f"isolated_count={stats['isolated_count']}")
    print(f"any_unhandled_hubs={stats['any_unhandled_hubs']}")
    print("PASS")
