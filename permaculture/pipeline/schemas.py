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
