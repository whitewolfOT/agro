# CATEGORIZATION MASTER — Plant / Agronomy Node Graph

**Purpose:** single source of truth for how plants, organisms, hubs, and their relationships are categorized across every dataset we've built. Written as a locked schema (invariant-numbered) so node data can be generated against it later without drift.

**Status:** schema + audit only. Actual node/edge rows are NOT reproduced here — the source files live in prior chat outputs and were not re-uploaded to this session. Re-upload them and this document becomes the contract they get normalized against.

---

## 1. What was analyzed

Five bodies of work were reviewed across past conversations:

| # | Artifact | Output file | Scale | Category system used | Edge system used |
|---|---|---|---|---|---|
| 1 | Permaculture / 300-video notes | `permaculture_network.html` | 130 nodes · 148 links · 34 isolated | 13 categories (morphology-led) | 8 types: N M F H S W C A |
| 2 | Islamic agronomy plants | `islamic_agronomy_network.html` + cleaned V1 table | 248 plants + SOIL hub · ~180 links · ~140 isolated | 14 categories | 6 types: companion, hostility, restores-soil, exhausts-soil, grafting, windbreak |
| 3 | Hakim medicine catalog | `hakim_master_catalog.html` + `islamic_plant_catalog_v2.html` | 373 remedy entries; plant catalog 278 entries · 14 categories · 4 use-types | 14 categories + use-type axis (Food/Medical/Both/Agronomic) | n/a (remedy table, not a graph) |
| 4 | Plant-relationship cleanup pass | (consolidation attempt) | — | — | user's original 6-type spec |
| 5 | Tunisia yield database | `khdra_yield_reference_filled.xlsx` | 37 cultures + 15 livestock | crop/livestock rows | n/a (value table) |

These share a plant universe (heavy overlap between #1, #2, #3) but three different, non-reconciled taxonomies. That is the core problem this document fixes.

---

## 2. Root cause of the inconsistencies

Every legacy dataset overloaded **one** `cat` field with **three orthogonal axes** at once:

- **Axis A — Growth form / morphology:** canopy tree, mid-layer tree, shrub, groundcover, climber, grass & grain, aquatic & wetland
- **Axis B — Ecological function:** nitrogen fixer, pioneer species, allelopath, soil-restorer, soil-exhauster
- **Axis C — Human use:** food, medicinal, industrial & fiber, aromatic, agronomic

"Nitrogen fixer" (function) sat in the same dropdown as "Shrub" (form) and "Medicinal" (use). A plant is usually all three at once, so forcing one label loses information and makes the same plant land in different categories across datasets. **The fix: split `cat` into three independent fields.** This is the single most important change for clean node data.

---

## 3. CANONICAL SCHEMA (locked)

### 3.1 Node contract

```json
{
  "id": "string — canonical common name, Title Case, unique",
  "name_ar": "string | null — Arabic/historical name",
  "name_sci": "string | null — Latin binomial, best match",
  "kind": "plant | animal | hub",
  "form": "one of NODE_FORMS (plants only, else null)",
  "function": ["zero+ of NODE_FUNCTIONS"],
  "use": ["zero+ of NODE_USES"],
  "sources": ["source_id"],
  "evidence_level": "Explicit | Strongly implied | Modern reconstruction | Uncertain",
  "notes": "string | null"
}
```

### 3.2 Edge contract

```json
{
  "source": "node id",
  "target": "node id",
  "type": "one of EDGE_TYPES",
  "direction": "directed | undirected",
  "context": ["zero+ of: young_stage, mature_stage, arid, temperate, high_density"],
  "source_id": "string",
  "evidence_level": "Explicit | Strongly implied | Modern reconstruction | Uncertain",
  "evidence_quote": "string | null",
  "confidence": "0.0–1.0"
}
```

### 3.3 Controlled vocabularies

**NODE_FORMS** (Axis A — morphology, exactly one per plant)
`canopy_tree · mid_tree · shrub · groundcover · climber · grass_grain · aquatic_wetland · palm · succulent`

**NODE_FUNCTIONS** (Axis B — ecological role, many allowed)
`nitrogen_fixer · pioneer · soil_restorer · soil_exhauster · allelopath · dynamic_accumulator · windbreak · rootstock`

**NODE_USES** (Axis C — human use, many allowed)
`food · medicinal · fiber_industrial · aromatic · fodder · agronomic_service`

**KIND = hub** reserved for non-organisms: `SOIL · WATER · CANOPY · PIONEER_ZONE · CLIMAX_ZONE`. Hubs carry `form/function/use = null`.

**EDGE_TYPES** (unified — 8 types, superset of both legacy sets)

| Canonical | Legacy 8-set | Legacy 6-set | Direction | Meaning |
|---|---|---|---|---|
| `companion` | F | companion | undirected | mutually beneficial pairing |
| `hostile` | H | hostile/allelopathic | directed | suppression / allelopathy |
| `nitrogen_fix` | N | (folded into restores-soil) | directed → SOIL | N fixation |
| `mulch_biomass` | M | (folded into restores-soil) | directed → SOIL | organic matter contribution |
| `soil_exhaust` | *(missing)* | soil_exhaust | directed → SOIL | heavy feeder depletion |
| `succession` | S | *(missing)* | directed | pioneer → climax |
| `water` | W | *(missing)* | directed → WATER | moisture / harvesting |
| `canopy_shade` | C | *(missing)* | directed | tall → understory shade |
| `animal` | A | *(missing)* | undirected | plant ↔ animal integration |
| `grafting` | *(missing)* | grafting/rootstock | directed | scion ↔ rootstock |
| `windbreak` | *(missing → now Axis-B function)* | support/windbreak | see note | structural shelter |

> Note: `windbreak` and `rootstock` were legacy **edge** types but are really **node functions** (a property of the plant, not a pairing). They move to Axis B. Keep an edge only when a specific *pair* is documented (e.g. "quince is rootstock **for** pear" → `grafting` edge). Standalone "X is a windbreak" → `function: [windbreak]`, no edge.

---

## 4. INCONSISTENCY REGISTER

Severity: **S** = structural (breaks a merge), **N** = naming/format, **P** = provenance/evidence, **V** = value accuracy.

| ID | Sev | Where | Problem | Resolution |
|---|---|---|---|---|
| INC-01 | S | all datasets | Single `cat` field mixes morphology + function + use | Split into `form` / `function[]` / `use[]` (§2, §3.3) |
| INC-02 | S | #1 vs #2 | Two different edge taxonomies (8-type N/M/F/H/S/W/C/A vs 6-type soil-restore/exhaust/graft/windbreak) | Adopt unified 11-row EDGE_TYPES (§3.3) |
| INC-03 | S | #2 internal | The delivered Islamic network used the **6-type** scheme, but the "reproduce-it" prompt handed to you specifies the **8-type** scheme — running that prompt yields a *different* graph (no grafting, no windbreak, no soil-exhaust; adds succession/water/canopy/animal) | Regenerate against unified set; retire the mismatched prompt |
| INC-04 | S | #1, #2 | `soil_restore` (6-set) vs `nitrogen_fix` + `mulch_biomass` (8-set) describe the same physical flow at different granularities | Canonical keeps the fine-grained pair; map legacy `soil_restore` → both or to `mulch_biomass` if N-fixation not stated |
| INC-05 | S | #1, #2 | `soil_exhaust` exists in the 6-set but was **dropped entirely** from the 8-set permaculture graph | Restore as canonical `soil_exhaust`; audit permaculture nodes for missing exhauster edges |
| INC-06 | S | #1 | "Nitrogen fixer" is both a node category **and** edge type N → same fact double-encoded | Node carries `function:[nitrogen_fixer]`; the N-fixation relationship is the edge. Never both as the categorical identity |
| INC-07 | S | #1, #2 | Hubs (SOIL/WATER/…) are nodes in the same set as real taxa; #2 used only SOIL, #1 used SOIL+WATER+more | Standardize hub set via `kind:hub`; declare which hubs each graph instantiates |
| INC-08 | N | all | Three edge-naming conventions: single-letter (`N`), snake_case (`soil_restore`), prose (`friendship / companion`) | Canonical = snake_case ids; letters are display aliases only |
| INC-09 | S | #1 vs #2 vs #3 | Category **counts differ** (13 vs 14 vs 14) with no crosswalk; same plant lands in different buckets | Crosswalk each legacy label to `form/function/use` before any merge (§5) |
| INC-10 | P | #1 | Grafting data was **filled from external sources** (Ibn al-Awwam, East Malling, UC Davis, ICARDA), i.e. Modern reconstruction, mixed in with in-text edges | Every edge must carry `evidence_level`; tag these `Modern reconstruction` |
| INC-11 | P | all graphs | Extraction schema had `confidence`+`evidence_quote`; the agronomy skill mandates a 4-level evidence label — unclear both were applied | Enforce both `evidence_level` (enum) and `confidence` (0–1) on every node/edge |
| INC-12 | S | #3 vs #1/#2 | Hakim uses a 4th "use-type" axis (Food/Medical/Both/Agronomic) absent from the graph datasets | Fold "use-type" into canonical `use[]`; "Both" = `[food, medicinal]` |
| INC-13 | S | cross-dataset | Same plant keyed by common name in one set, Arabic/scientific in another → duplicate nodes on merge | Canonical `id` = common name; `name_ar`/`name_sci` as attributes; dedup on all three |
| INC-14 | P | #2 | "restores 16 / exhausts 12" counts asserted but isolated-node share is ~140/248 — most plants have no documented edge | Keep `isolated` flag; do not infer edges to fill gaps |
| INC-15 | V | #5 | Yield values mix Tunisia-local and global ranges (tomate min 50 vs 16; orge/sorgho global vs local; olive oil ~350 vs ~100 L/ha typical) | If yields become node attributes, tag each `scope: local | global` and pick one basis |
| INC-16 | V | #3 corrections | Known prior errors already fixed (nutmeg temperament, wormwood duplicate, anesthetic sponge components, gum ammoniacum vs galbanum) — ensure the *graph* datasets inherit these fixes, not stale copies | Re-derive #3-linked plant nodes from the corrected v2 catalog |

---

## 5. CROSSWALK — legacy category → canonical axes

Apply before merging any two datasets. (Representative; extend per full legacy list once files are re-uploaded.)

| Legacy label | → form | → function[] | → use[] |
|---|---|---|---|
| Canopy tree | canopy_tree | — | — |
| Mid-layer tree | mid_tree | — | — |
| Shrub | shrub | — | — |
| Groundcover | groundcover | — | — |
| Climber | climber | — | — |
| Grass & grain | grass_grain | — | food/fodder |
| Aquatic & wetland | aquatic_wetland | — | — |
| **Nitrogen fixer** | *(its real form, e.g. shrub/tree)* | **nitrogen_fixer** | — |
| **Pioneer species** | *(its real form)* | **pioneer** | — |
| Medicinal | *(its real form)* | — | **medicinal** |
| Industrial & fiber | *(its real form)* | — | **fiber_industrial** |
| Animal integration | *(kind=animal)* | — | — |
| Ecosystem hub | *(kind=hub, form=null)* | — | — |
| Hakim use-type: Food | *(real form)* | — | food |
| Hakim use-type: Medical | *(real form)* | — | medicinal |
| Hakim use-type: Both | *(real form)* | — | food, medicinal |
| Hakim use-type: Agronomic | *(real form)* | agronomic_service (if applicable) | agronomic_service |

The bolded rows are where legacy data **loses** its true morphology — those need the plant's real growth form back-filled during normalization.

---

## 6. Locked invariants (for whatever builds the nodes next)

- **INV#1** — `cat` is forbidden. Only `form` (single), `function[]`, `use[]` exist.
- **INV#2** — `nitrogen_fixer` / `pioneer` / `windbreak` / `rootstock` are functions, never node categories and never a plant's sole identity.
- **INV#3** — Every edge type comes from EDGE_TYPES (§3.3). No single-letter ids in the data; letters are display-only.
- **INV#4** — Every node and edge carries `evidence_level` ∈ {Explicit, Strongly implied, Modern reconstruction, Uncertain} **and** `confidence` ∈ [0,1].
- **INV#5** — Externally-sourced edges (not in the source document) are `Modern reconstruction`, never `Explicit`.
- **INV#6** — `id` is the canonical common name; Arabic and scientific names are attributes. Dedup across all three before merge.
- **INV#7** — Hubs are `kind:hub` with null form/function/use; each graph declares which hubs it uses.
- **INV#8** — Isolated nodes are kept and flagged, never given inferred edges to reduce the isolate count.
- **INV#9** — Yield/quantitative attributes carry `scope: local | global`; one basis per graph.

---

## 7. Open decisions (need your call)

1. **Merge or federate?** One unified graph across all datasets, or keep per-source graphs that share the canonical schema? (Merge maximizes cross-links but forces dedup on ~600 plants.)
2. **Grafting/windbreak** — confirm the move from edge-type to node-function is what you want, keeping edges only for documented *specific pairs*.
3. **Yield basis** — Tunisia-local vs global for the crop attributes (INC-15).
4. **Evidence floor** — minimum `confidence` to include an edge in the visual (e.g. drop < 0.3, or show greyed).

Re-upload the network HTML files (and the cleaned V1 table + v2 catalog) and I'll normalize every row against this contract and emit clean `nodes.json` + `edges.json`.
