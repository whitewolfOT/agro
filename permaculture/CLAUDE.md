Token-efficient mode. No prose, code and results only.

# Plant Agronomy — Master Node Pipeline

Reads 3 conversation exports + their artifacts, normalizes all plant/edge data against a locked schema, merges into one clean graph, fact-checks edges, adds missing links (tagged), outputs master_nodes.json + master_edges.json + inconsistencies.csv.

---

## Repo structure

```
project/
├── CLAUDE.md                        ← this file
├── CATEGORIZATION_MASTER.md         ← locked schema + invariants (law — never override)
├── conv_1/
│   ├── conversation.json
│   ├── files/                       ← source docs (.docx etc)
│   └── artifacts/                   ← .html + .md outputs
├── conv_2/
│   ├── conversation.json
│   ├── files/
│   └── artifacts/
├── conv_3/
│   ├── conversation.json
│   ├── files/
│   └── artifacts/
├── pipeline/
│   ├── schemas.py                   ← Step 0-A (build first)
│   ├── extract.py                   ← Step 1
│   ├── normalize.py                 ← Step 2
│   ├── merge.py                     ← Step 3
│   ├── factcheck.py                 ← Step 4
│   └── emit.py                      ← Step 5
└── output/
    ├── master_nodes.json
    ├── master_edges.json
    └── inconsistencies.csv
```

---

## Shared data contracts (schemas.py — build first, nothing else imports before this)

```python
from dataclasses import dataclass, field
from typing import List, Optional, Literal

EvidenceLevel = Literal["Explicit", "Strongly implied", "Modern reconstruction", "Uncertain"]
NodeKind = Literal["plant", "animal", "hub"]

NODE_FORMS = {
    "canopy_tree","mid_tree","shrub","groundcover",
    "climber","grass_grain","aquatic_wetland","palm","succulent"
}
NODE_FUNCTIONS = {
    "nitrogen_fixer","pioneer","soil_restorer","soil_exhauster",
    "allelopath","dynamic_accumulator","windbreak","rootstock"
}
NODE_USES = {"food","medicinal","fiber_industrial","aromatic","fodder","agronomic_service"}

EDGE_TYPES = {
    "companion","hostile","nitrogen_fix","mulch_biomass",
    "soil_exhaust","succession","water","canopy_shade",
    "animal","grafting","windbreak"
}

LEGACY_CAT_MAP = {
    # morphology → form
    "Canopy tree": {"form": "canopy_tree"},
    "Mid-layer tree": {"form": "mid_tree"},
    "Shrub": {"form": "shrub"},
    "Groundcover": {"form": "groundcover"},
    "Climber": {"form": "climber"},
    "Grass & grain": {"form": "grass_grain", "use": ["food","fodder"]},
    "Aquatic & wetland": {"form": "aquatic_wetland"},
    "Palm": {"form": "palm"},
    # function-as-category → real form unknown, flag it
    "Nitrogen fixer": {"function": ["nitrogen_fixer"], "form": "UNKNOWN"},
    "Pioneer species": {"function": ["pioneer"], "form": "UNKNOWN"},
    # use-as-category
    "Medicinal": {"use": ["medicinal"], "form": "UNKNOWN"},
    "Industrial & fiber": {"use": ["fiber_industrial"], "form": "UNKNOWN"},
    # special kinds
    "Animal integration": {"kind": "animal"},
    "Ecosystem hub": {"kind": "hub"},
    # hakim use-type axis
    "Food": {"use": ["food"]},
    "Medical": {"use": ["medicinal"]},
    "Both": {"use": ["food","medicinal"]},
    "Agronomic": {"use": ["agronomic_service"]},
}

LEGACY_EDGE_MAP = {
    # 8-type set
    "N": "nitrogen_fix", "M": "mulch_biomass", "F": "companion",
    "H": "hostile", "S": "succession", "W": "water",
    "C": "canopy_shade", "A": "animal",
    # 6-type set
    "companion": "companion",
    "hostile/allelopathic": "hostile",
    "soil_restore": "mulch_biomass",   # split: nitrogen_fix only if N-fixation stated
    "soil_exhaust": "soil_exhaust",
    "grafting/rootstock": "grafting",
    "support/windbreak": "windbreak",
    # prose variants
    "friendship / companion": "companion",
    "hostility / allelopathy": "hostile",
    "restores soil": "mulch_biomass",
    "exhausts soil": "soil_exhaust",
}

@dataclass
class Node:
    id: str                                    # canonical common name, Title Case
    kind: NodeKind = "plant"
    name_ar: Optional[str] = None
    name_sci: Optional[str] = None
    form: Optional[str] = None                 # one of NODE_FORMS or None for hub/animal
    function: List[str] = field(default_factory=list)
    use: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    evidence_level: EvidenceLevel = "Uncertain"
    isolated: bool = False
    notes: Optional[str] = None
    _flags: List[str] = field(default_factory=list)  # INC-xx tags

@dataclass
class Edge:
    source: str
    target: str
    type: str                                  # one of EDGE_TYPES
    direction: Literal["directed","undirected"] = "directed"
    context: List[str] = field(default_factory=list)
    source_id: str = ""
    evidence_level: EvidenceLevel = "Uncertain"
    evidence_quote: Optional[str] = None
    confidence: float = 0.5
    added: bool = False                        # True = inferred/added, not in source data
    _flags: List[str] = field(default_factory=list)
```

---

## Pipeline order

```
extract.py → normalize.py → merge.py → factcheck.py → emit.py
```

Each step reads from the previous step's JSON output. Never skip a step.

---

## Build order

### Step 0-A — schemas.py
Write `pipeline/schemas.py` exactly as above. No logic, no imports beyond stdlib + dataclasses.
Done when: `python -c "from pipeline.schemas import Node, Edge, LEGACY_CAT_MAP"` exits 0.
Report: PASS/FAIL. Stop.

---

### Step 1 — extract.py
Write `pipeline/extract.py`. Entry point: `extract_all(project_root: str) -> dict`.

**Reads (in order):**

1. `conv_*/artifacts/*.html` — extract JS arrays:
   - Find `const nodes = [` ... `];` → parse as JSON5/JS (use `js2py` or regex-strip trailing commas)
   - Find `const edges = [` or `const links = [` ... `];` → same
   - Tag each record with `source_file: <filename>`

2. `conv_*/artifacts/*.md` — extract any markdown tables with columns matching: name/plant/id + category/cat + relationship/type
   - Parse table rows → dicts
   - Tag with `source_file: <filename>`

3. `conv_*/conversation.json` — scan `assistant` messages only for:
   - JSON blocks inside code fences labeled `json` or `javascript`
   - Any line matching `{id:` or `{source:` patterns (inline node/edge objects)
   - Do NOT parse human messages (noise)
   - Tag with `source_file: conversation.json`

4. `conv_*/files/*` — skip binary; for `.md`/`.txt` parse same as #2

**Output:** `output/raw_extracted.json`
```json
{
  "nodes": [ {"id": "...", "cat": "...", "source_file": "...", ...} ],
  "edges": [ {"source": "...", "target": "...", "type": "...", "source_file": "...", ...} ]
}
```

Done when: node count > 100, edge count > 50 (sanity floor).
Report: PASS/FAIL + node_count + edge_count + files_read. Stop.

---

### Step 2 — normalize.py
Write `pipeline/normalize.py`. Entry point: `normalize(raw: dict) -> dict`.

**Node normalization (apply in order):**

1. `id` → Title Case, strip extra whitespace
2. `cat` → apply `LEGACY_CAT_MAP`:
   - If `cat` maps to `form` → set `node.form`
   - If `cat` maps to `function` → append to `node.function`
   - If `cat` maps to `use` → append to `node.use`
   - If `form` == "UNKNOWN" → flag `INC-01` on node
3. If node has `name_sci` that is empty string → set to None
4. If node has `kind == "hub"` → set `form/function/use = null/[]/[]`
5. If node has no `evidence_level` → set "Uncertain"
6. Deduplicate `function` and `use` lists

**Edge normalization:**

1. `type` → apply `LEGACY_EDGE_MAP` → canonical snake_case
2. If type not in `EDGE_TYPES` after mapping → flag `INC-03` + set type = "unknown"
3. `soil_restore` → map to `mulch_biomass`; if source text contains "nitrogen" or "legume" → also emit a second `nitrogen_fix` edge (same source/target)
4. If `source_file` contains "external" or note contains "Ibn al-Awwam" / "East Malling" / "UC Davis" / "ICARDA" / "modern reconstruction" → set `evidence_level = "Modern reconstruction"`, `added = False` (it was in the data, just mislabeled)
5. If no `confidence` → set 0.5

**Output:** `output/normalized.json` (same shape as raw, fields now canonical)
Done when: zero edges with `type == "unknown"` or all flagged.
Report: PASS/FAIL + INC flags fired + edge type distribution. Stop.

---

### Step 3 — merge.py
Write `pipeline/merge.py`. Entry point: `merge(normalized: dict) -> dict`.

**Node dedup — match on ANY of these (in priority order):**
1. `id` exact match (case-insensitive)
2. `name_sci` exact match (non-null)
3. `name_ar` exact match (non-null)

When merging two records for the same plant:
- `id` → keep the most common name across sources (frequency wins; tie → alphabetical)
- `form` → if both non-null and differ → flag `INC-09`, keep the one from the Islamic agronomy dataset (most authoritative for this domain)
- `function` / `use` → union
- `sources` → union
- `evidence_level` → take the strongest (Explicit > Strongly implied > Modern reconstruction > Uncertain)
- `name_ar` / `name_sci` → keep non-null; if conflict flag `INC-13`
- `_flags` → union all flags

**Edge dedup:**
- Same (source, target, type) = duplicate; merge by taking highest confidence, union context tags

**Isolated node detection:**
- Any node with zero edges after merge → set `isolated = True`

**Output:** `output/merged.json`
Done when: node count < raw node count (dedup happened), zero duplicate (source,target,type) triples.
Report: PASS/FAIL + nodes_before + nodes_after + edges_before + edges_after + isolated_count. Stop.

---

### Step 4 — factcheck.py
Write `pipeline/factcheck.py`. Entry point: `factcheck(merged: dict) -> dict`.

**4-A: Known-bad edge list — flag these (do not delete, set confidence=0.1 + flag "FACTCHECK_FAIL"):**
```python
KNOWN_ERRORS = [
    # format: (source_pattern, target_pattern, type, reason)
    ("Corn", "Carrot", "hostile", "allelopathy claim weak — no confirmed juglone-class compound in maize"),
    ("Bamboo", "Vetiver", "hostile", "competitive not allelopathic — reclassify to soil_exhaust"),
    ("Walnut", "*", "hostile", "confirm juglone target — only affects specific species, not all"),
]
```
For each edge: if (source, target, type) matches a pattern → add flag `FACTCHECK_FLAGGED` + note reason.

**4-B: Known-missing edges — add these if not already present (set `added=True`, `evidence_level="Modern reconstruction"`, `confidence=0.7`):**
```python
KNOWN_ADDITIONS = [
    # Islamic agronomy — grafting pairs from Ibn al-Awwam
    ("Quince", "Pear", "grafting", "Ibn al-Awwam explicit — quince rootstock for pear"),
    ("Wild Olive", "Cultivated Olive", "grafting", "Ibn al-Awwam explicit"),
    ("Almond", "Peach", "grafting", "Ibn al-Awwam explicit"),
    # Nitrogen fixers missing soil edge
    ("Fava Bean", "SOIL", "nitrogen_fix", "Vicia faba — well-documented N-fixer, modern reconstruction"),
    ("Lentil", "SOIL", "nitrogen_fix", "Lens culinaris — well-documented N-fixer, modern reconstruction"),
    ("Chickpea", "SOIL", "nitrogen_fix", "Cicer arietinum — well-documented N-fixer, modern reconstruction"),
    ("Lupin", "SOIL", "nitrogen_fix", "Lupinus spp. — Ibn al-Awwam describes as soil restorer, modern reconstruction"),
    # Allelopathy — confirmed juglone targets
    ("Walnut", "Apple", "hostile", "juglone — confirmed susceptible, Explicit from literature"),
    ("Walnut", "Tomato", "hostile", "juglone — confirmed susceptible, Explicit from literature"),
    ("Walnut", "Alfalfa", "hostile", "juglone — confirmed susceptible, Explicit from literature"),
    # Companion pairs from Islamic texts missing from graph
    ("Basil", "Vine", "companion", "Ibn al-Awwam — plant basil at vine base, Explicit"),
    ("Rue", "Fig", "companion", "Ibn al-Awwam — rue under fig deters pests, Explicit"),
    ("Garlic", "Rose", "companion", "Ibn al-Awwam — garlic improves rose scent, Explicit"),
    # Soil exhausters missing
    ("Cotton", "SOIL", "soil_exhaust", "heavy N/K feeder — well documented, Modern reconstruction"),
    ("Sugar Cane", "SOIL", "soil_exhaust", "heavy feeder — well documented, Modern reconstruction"),
]
```
For each addition: check if (source, target, type) already exists → skip. Else add with `added=True`.

**4-C: Form back-fill — nodes still flagged INC-01 (form=UNKNOWN):**
```python
FORM_BACKFILL = {
    "Nitrogen fixer": None,   # handled by function tag — leave form as actual plant form
    # Add any known plants that came in with only a function category:
    "Acacia": "mid_tree",
    "Leucaena": "mid_tree",
    "Casuarina": "canopy_tree",
    "Clover": "groundcover",
    "Alfalfa": "groundcover",
    "Lupin": "groundcover",
    "Fava Bean": "groundcover",
    "Lentil": "groundcover",
    "Chickpea": "groundcover",
    "Wormwood": "shrub",
    "Rue": "shrub",
}
```
Apply backfill → clear INC-01 flag if resolved.

**Output:** `output/factchecked.json`
Done when: KNOWN_ADDITIONS all processed, KNOWN_ERRORS all flagged.
Report: PASS/FAIL + edges_added + edges_flagged + INC-01_remaining. Stop.

---

### Step 5 — emit.py
Write `pipeline/emit.py`. Entry point: `emit(factchecked: dict)`.

**Writes:**

`output/master_nodes.json`
```json
[
  {
    "id": "Garlic",
    "kind": "plant",
    "name_ar": "ثوم",
    "name_sci": "Allium sativum",
    "form": "groundcover",
    "function": [],
    "use": ["food", "medicinal"],
    "sources": ["islamic_agronomy_network.html", "islamic_plant_catalog_v2.html"],
    "evidence_level": "Explicit",
    "isolated": false,
    "added": false,
    "flags": [],
    "notes": null
  }
]
```

`output/master_edges.json`
```json
[
  {
    "source": "Garlic",
    "target": "Rose",
    "type": "companion",
    "direction": "undirected",
    "context": [],
    "source_id": "islamic_agronomy_network.html",
    "evidence_level": "Explicit",
    "evidence_quote": null,
    "confidence": 0.9,
    "added": true,
    "flags": []
  }
]
```

`output/inconsistencies.csv`
Columns: `node_or_edge_id, flag_id, description, resolution_applied, requires_human_review`
One row per flag fired. `requires_human_review = TRUE` for INC-01 remaining, INC-09 form conflicts, FACTCHECK_FLAGGED.

**Validation before writing:**
- Every edge source and target exists in master_nodes → crash if not
- Every node form is in NODE_FORMS or null → crash if not
- Every edge type is in EDGE_TYPES → crash if not
- Zero duplicate node ids → crash if not
- Zero duplicate (source, target, type) edge triples → crash if not

Done when: all 3 files written, all validations pass.
Report: PASS/FAIL + final_node_count + final_edge_count + added_edge_count + flagged_edge_count + inconsistencies_row_count. Stop.

---

## How to run

```bash
cd project/
pip install js2py   # for JS array parsing in extract.py

python -m pipeline.schemas          # Step 0 check
python -m pipeline.extract .        # Step 1
python -m pipeline.normalize        # Step 2
python -m pipeline.merge            # Step 3
python -m pipeline.factcheck        # Step 4
python -m pipeline.emit             # Step 5
```

Each script reads `output/<previous_step>.json`, writes `output/<this_step>.json`.
Run sequentially. Each stops and reports before the next begins.

---

## Non-negotiable rules

- NEVER delete a node or edge — flag it, lower confidence, mark it. Deletion = data loss.
- NEVER infer a form for a hub node — hubs have form=null always.
- NEVER mark an in-source edge as `added=True` — `added` is only for KNOWN_ADDITIONS.
- NEVER merge two nodes unless at least one of (id, name_sci, name_ar) matches exactly.
- CATEGORIZATION_MASTER.md is law. If any instruction here conflicts with it, amend this file first.
- Do not install packages beyond `js2py` and stdlib without confirming with human.
- Report PASS/FAIL after every step. Never chain two steps without stopping.
