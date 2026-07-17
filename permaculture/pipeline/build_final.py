"""
pipeline/build_final.py
Build a self-contained plant network HTML visualisation.

Reads:   output/master_nodes.json, output/final_edges.json
Fetches: D3 v7 from cdnjs (inlined); falls back to npm install if CDN blocked
Uses:    pipeline/plant_network_template.html as layout
Writes:  output/plant_network_final.html
"""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

D3_URL     = "https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"
D3_VERSION = "7.8.5"
TEMPLATE   = Path(__file__).with_name("plant_network_template.html")

CDN_PATTERNS = [
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/',
    '<script src="https://d3js.org/',
    '<script src="https://unpkg.com/d3',
]


def _fetch_d3() -> str:
    # 1. Try CDN via urllib (respects HTTPS_PROXY if set)
    try:
        print(f"Downloading D3 from {D3_URL} …", file=sys.stderr)
        with urllib.request.urlopen(D3_URL, timeout=30) as r:
            src = r.read().decode("utf-8")
            print(f"CDN fetch OK ({len(src):,} bytes)", file=sys.stderr)
            return src
    except Exception as e:
        print(f"CDN fetch failed ({e}), falling back to npm …", file=sys.stderr)

    # 2. Fallback: npm install d3 into /tmp, then read dist file
    # Check common locations first (previous npm run may have used /tmp directly)
    candidates = [
        Path("/tmp/node_modules/d3/dist/d3.min.js"),
        Path("/tmp/d3_npm/node_modules/d3/dist/d3.min.js"),
    ]
    for candidate in candidates:
        if candidate.exists():
            src = candidate.read_text(encoding="utf-8")
            print(f"npm D3 read OK from {candidate} ({len(src):,} bytes)", file=sys.stderr)
            return src

    # Install fresh
    npm_dir = Path("/tmp")
    subprocess.run(
        ["npm", "install", f"d3@{D3_VERSION}"],
        cwd=str(npm_dir), check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    src = (npm_dir / "node_modules" / "d3" / "dist" / "d3.min.js").read_text(encoding="utf-8")
    print(f"npm D3 installed OK ({len(src):,} bytes)", file=sys.stderr)
    return src


def _strip_cdn_tag(html: str) -> str:
    """Remove any CDN <script …></script> line for D3."""
    lines = html.splitlines()
    out = []
    for line in lines:
        if any(pat in line for pat in CDN_PATTERNS):
            continue
        out.append(line)
    return "\n".join(out)


WATER_NEED = {
    "low": [
        "Olive","Date palm","Fig","Carob","Almond","Pistachio","Pomegranate","Lentisk",
        "Terebinth","Saffron","Lavender","Rosemary","Thyme","Sage","Southernwood",
        "Wormwood","Rue","Hyssop","Calamint","Cotton","Sorghum","Millet","Barley",
        "Chickpea","Lentil","Lupin","Fenugreek","Artichoke","Cardoon","Purslane",
        "Rocket","Caper","Aloe","Jujube","Doum palm",
    ],
    "medium": [
        "Wheat","Oats","Rye","Broad bean","Garden pea","Cowpea","Vetch","Fava Bean",
        "Onion","Garlic","Leek","Carrot","Parsnip","Turnip","Radish","Beetroot",
        "Lettuce","Chicory","Endive","Spinach","Chard","Mallow","Borage","Sorrel",
        "Parsley","Coriander","Dill","Fennel","Celery","Basil","Mint","Lemon balm",
        "Apple","Pear","Quince","Plum","Damson","Cherry","Hazel","Walnut","Vine",
        "Grapevine","Mulberry","Myrtle","Rose","Jasmine","Iris","Violet","Narcissus",
        "Flax","Hemp","Sesame","Sunflower","Maize","Corn",
    ],
    "high": [
        "Rice","Sugarcane","Sugar Cane","Banana","Cucumber","Melon","Watermelon",
        "Gourd","Bottle gourd","Eggplant","Cabbage","Cauliflower","Kohlrabi",
        "Lovage","Watercress","Asparagus",
        "Peach","Apricot","Lemon","Citron","Sour orange","Sweet orange","Lime",
        "Tamarind","Sycamore fig","Hackberry","Arbutus","Hawthorn","Medlar",
    ],
    "very_high": [
        "Water lily","Watercress","Aquatic mint","Reed","Papyrus","Cattail",
        "Lotus","Water chestnut",
    ],
}

_WATER_LOOKUP = {name.lower(): wn for wn, names in WATER_NEED.items() for name in names}


def run(out_dir: str = "output"):
    out = Path(out_dir)

    nodes = json.loads((out / "master_nodes.json").read_text(encoding="utf-8"))
    edges = json.loads((out / "final_edges.json").read_text(encoding="utf-8"))

    # ── Clean edges: drop any whose endpoints are missing from master_nodes ──
    node_ids = {n["id"] for n in nodes}
    edges_before = len(edges)
    edges = [e for e in edges if e["source"] in node_ids and e["target"] in node_ids]
    edges_removed = edges_before - len(edges)
    print(f"edges removed (dangling endpoints): {edges_removed}", file=sys.stderr)

    # ── Bake water_need into each node ──
    water_assigned = 0
    for node in nodes:
        wn = _WATER_LOOKUP.get(node["id"].lower(), "medium")
        node["water_need"] = wn
        if wn != "medium":
            water_assigned += 1
    print(f"water_need assigned (non-medium): {water_assigned}", file=sys.stderr)

    d3_src = _fetch_d3()
    print(f"D3 source: {len(d3_src):,} bytes", file=sys.stderr)

    template = TEMPLATE.read_text(encoding="utf-8")

    # Strip CDN script tag (template has none currently, but be safe)
    html = _strip_cdn_tag(template)

    # Inject inlined D3 before closing </head>
    d3_block = f"<script>{d3_src}</script>"
    if "</head>" in html:
        html = html.replace("</head>", d3_block + "\n</head>", 1)
    else:
        # Fallback: prepend before first <script>
        html = d3_block + "\n" + html

    # Bake data
    nodes_json = json.dumps(nodes, ensure_ascii=False, separators=(",", ":"))
    edges_json = json.dumps(edges, ensure_ascii=False, separators=(",", ":"))

    html = html.replace("PLACEHOLDER_NODES", nodes_json, 1)
    html = html.replace("PLACEHOLDER_EDGES", edges_json, 1)

    # Verify no stale placeholders
    if "PLACEHOLDER" in html:
        remaining = [l for l in html.splitlines() if "PLACEHOLDER" in l]
        raise RuntimeError(f"Unfilled PLACEHOLDER in output:\n" + "\n".join(remaining[:5]))

    out_path = out / "plant_network_final.html"
    out_path.write_text(html, encoding="utf-8")

    size_kb = out_path.stat().st_size / 1024
    if size_kb < 500:
        raise RuntimeError(f"Output too small: {size_kb:.1f} KB (expected > 500 KB)")

    return {
        "nodes_count":              len(nodes),
        "edges_before":             edges_before,
        "edges_after":              len(edges),
        "file_size_kb":             round(size_kb, 1),
        "water_need_assigned_count": water_assigned,
    }


if __name__ == "__main__":
    stats = run()
    print(f"nodes_count={stats['nodes_count']}")
    print(f"edges_before={stats['edges_before']}")
    print(f"edges_after={stats['edges_after']}")
    print(f"file_size_kb={stats['file_size_kb']}")
    print(f"water_need_assigned_count={stats['water_need_assigned_count']}")
    print("PASS")
