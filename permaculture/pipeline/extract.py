"""
Step 1 — extract.py
Entry point: extract_all(project_root: str) -> dict
Writes: output/raw_extracted.json
"""
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


# ── JS → JSON conversion ─────────────────────────────────────────────────────

def _strip_js_comments(s: str) -> str:
    """Remove // line comments and /* block comments */ from JS text."""
    # block comments
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.DOTALL)
    # line comments (but not inside strings — heuristic: skip if inside "...")
    lines = []
    for line in s.splitlines():
        # remove // comment unless inside a string (rough heuristic)
        stripped = re.sub(r'(?<!:)//.*$', '', line)
        lines.append(stripped)
    return '\n'.join(lines)


def _remove_trailing_commas(s: str) -> str:
    """Remove trailing commas before ] or } (JSON doesn't allow them)."""
    return re.sub(r',\s*([}\]])', r'\1', s)


def _js_to_json(s: str) -> str:
    """Best-effort JS object literal → JSON: quote bare keys, fix strings."""
    s = _strip_js_comments(s)
    s = _remove_trailing_commas(s)
    # quote unquoted object keys: {key: → {"key":
    s = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', s)
    # replace single-quoted strings with double-quoted (naïve but works for this data)
    # Only do this when not already inside double quotes
    s = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", lambda m: json.dumps(m.group(1)), s)
    return s


def _parse_js_array(js_text: str) -> list:
    """Parse a JS array literal to Python list."""
    js_text = js_text.strip()

    # Pass 1: strip comments + trailing commas only (no quote conversion)
    pass1 = _remove_trailing_commas(_strip_js_comments(js_text))
    try:
        return json.loads(pass1)
    except json.JSONDecodeError:
        pass

    # Pass 2: also quote bare object keys
    pass2 = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', pass1)
    try:
        return json.loads(pass2)
    except json.JSONDecodeError:
        pass

    # Pass 3: full conversion including single-quote strings (risky for data with apostrophes)
    try:
        return json.loads(_js_to_json(js_text))
    except json.JSONDecodeError:
        return []


def _extract_named_array(html: str, name: str) -> list:
    """Extract const NAME = [...]; from HTML/JS source."""
    # Match: const NAME=[ or const NAME = [
    pattern = r'\bconst\s+' + re.escape(name) + r'\s*=\s*(\[[\s\S]*?\n\s*\]);'
    m = re.search(pattern, html)
    if not m:
        # try without trailing semicolon, greedier — find matching bracket
        idx = re.search(r'\bconst\s+' + re.escape(name) + r'\s*=\s*\[', html)
        if not idx:
            return []
        start = idx.end() - 1  # position of [
        depth = 0
        end = start
        for i, ch in enumerate(html[start:], start):
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        raw = html[start:end]
        return _parse_js_array(raw)
    return _parse_js_array(m.group(1))


# ── Node/Edge normalizers per format ─────────────────────────────────────────

def _node_from_tuple2(row, source_file) -> dict:
    """[id, cat] format."""
    if not isinstance(row, (list, tuple)) or len(row) < 2:
        return None
    return {"id": str(row[0]).strip(), "cat": str(row[1]).strip(),
            "source_file": source_file}


def _node_from_tuple7(row, source_file) -> dict:
    """[name, name_ar, sci, cat, role, sources, evidence] format (const D)."""
    if not isinstance(row, (list, tuple)) or len(row) < 4:
        return None
    return {
        "id": str(row[0]).strip(),
        "name_ar": str(row[1]).strip() if len(row) > 1 else None,
        "name_sci": str(row[2]).strip() if len(row) > 2 else None,
        "cat": str(row[3]).strip() if len(row) > 3 else None,
        "notes": str(row[4]).strip() if len(row) > 4 else None,
        "sources": [s.strip() for s in str(row[5]).split(',')] if len(row) > 5 else [],
        "evidence_level": str(row[6]).strip() if len(row) > 6 else "Uncertain",
        "source_file": source_file,
    }


def _node_from_obj(obj, source_file) -> dict:
    """Generic dict/object node."""
    if not isinstance(obj, dict):
        return None
    node = {"source_file": source_file}
    # id
    node["id"] = str(obj.get("id") or obj.get("name") or "").strip()
    if not node["id"]:
        return None
    node["cat"] = str(obj.get("cat") or obj.get("category") or "").strip() or None
    node["name_ar"] = str(obj.get("name_ar") or obj.get("arabic") or "").strip() or None
    node["name_sci"] = str(obj.get("sci") or obj.get("name_sci") or obj.get("scientific") or "").strip() or None
    node["notes"] = str(obj.get("note") or obj.get("notes") or obj.get("role") or "").strip() or None
    node["evidence_level"] = str(obj.get("evidence_level") or obj.get("evidence") or "Uncertain").strip()
    return node


def _edge_from_tuple4(row, source_file, default_type=None) -> dict:
    """[source, target, type, note] or [source, target, note] format."""
    if not isinstance(row, (list, tuple)) or len(row) < 2:
        return None
    edge = {
        "source": str(row[0]).strip(),
        "target": str(row[1]).strip(),
        "source_file": source_file,
    }
    if len(row) >= 3 and default_type is None:
        edge["type"] = str(row[2]).strip()
    elif default_type:
        edge["type"] = default_type
    else:
        edge["type"] = "unknown"
    edge["note"] = str(row[3]).strip() if len(row) >= 4 else (str(row[2]).strip() if len(row) >= 3 and default_type else "")
    return edge


def _edge_from_obj(obj, source_file) -> dict:
    """Generic dict/object edge."""
    if not isinstance(obj, dict):
        return None
    source = str(obj.get("source") or obj.get("s") or "").strip()
    target = str(obj.get("target") or obj.get("t") or "").strip()
    if not source or not target:
        return None
    etype = str(obj.get("type") or obj.get("r") or obj.get("rel") or "").strip()
    note = str(obj.get("note") or obj.get("n") or obj.get("notes") or "").strip() or None
    conf_raw = obj.get("conf") or obj.get("confidence")
    confidence = None
    if conf_raw is not None:
        if isinstance(conf_raw, (int, float)):
            confidence = float(conf_raw)
        elif str(conf_raw).upper() == 'H':
            confidence = 0.9
        elif str(conf_raw).upper() == 'M':
            confidence = 0.7
        elif str(conf_raw).upper() == 'L':
            confidence = 0.4
    edge = {
        "source": source,
        "target": target,
        "type": etype,
        "source_file": source_file,
    }
    if note:
        edge["note"] = note
    if confidence is not None:
        edge["confidence"] = confidence
    return edge


# ── HTML file parsers ─────────────────────────────────────────────────────────

class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self._cur_table = []
        self._cur_row = []
        self._cur_cell = ''
        self._in_cell = False
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self._depth += 1
            if self._depth == 1:
                self._cur_table = []
        elif tag == 'tr':
            self._cur_row = []
        elif tag in ('td', 'th'):
            self._in_cell = True
            self._cur_cell = ''

    def handle_endtag(self, tag):
        if tag == 'table':
            if self._depth == 1:
                self.tables.append(self._cur_table)
            self._depth -= 1
        elif tag == 'tr':
            if self._cur_row:
                self._cur_table.append(self._cur_row[:])
        elif tag in ('td', 'th'):
            self._in_cell = False
            self._cur_row.append(re.sub(r'\s+', ' ', self._cur_cell).strip())

    def handle_data(self, data):
        if self._in_cell:
            self._cur_cell += data


def _parse_html_tables(html: str, source_file: str):
    """Extract nodes+edges from HTML tables in verified_reference format."""
    p = _TableParser()
    p.feed(html)
    nodes = []
    edges = []

    for table in p.tables:
        if len(table) < 2:
            continue
        headers = [h.lower().strip() for h in table[0]]
        rows = table[1:]

        # Companion / friendship tables: Plant A, Plant B
        if 'plant a' in headers and 'plant b' in headers:
            ia = headers.index('plant a')
            ib = headers.index('plant b')
            isrc = next((i for i, h in enumerate(headers) if 'source' in h), None)
            iev = next((i for i, h in enumerate(headers) if 'evidence' in h), None)
            imech = next((i for i, h in enumerate(headers) if 'mechanism' in h), None)
            for row in rows:
                if len(row) <= max(ia, ib):
                    continue
                edges.append({
                    "source": row[ia], "target": row[ib],
                    "type": "companion",
                    "note": row[imech] if imech and imech < len(row) else None,
                    "evidence_level": row[iev] if iev and iev < len(row) else "Uncertain",
                    "source_file": source_file,
                })

        # Succession / rotation tables: Predecessor, Successor
        elif 'predecessor' in headers and 'successor' in headers:
            ia = headers.index('predecessor')
            ib = headers.index('successor')
            iev = next((i for i, h in enumerate(headers) if 'evidence' in h), None)
            imech = next((i for i, h in enumerate(headers) if 'mechanism' in h), None)
            for row in rows:
                if len(row) <= max(ia, ib):
                    continue
                edges.append({
                    "source": row[ia], "target": row[ib],
                    "type": "succession",
                    "note": row[imech] if imech and imech < len(row) else None,
                    "evidence_level": row[iev] if iev and iev < len(row) else "Uncertain",
                    "source_file": source_file,
                })

        # Hostility / allelopathy: Aggressor, Target
        elif 'aggressor' in headers and 'target' in headers:
            ia = headers.index('aggressor')
            ib = headers.index('target')
            iev = next((i for i, h in enumerate(headers) if 'evidence' in h), None)
            imech = next((i for i, h in enumerate(headers) if 'mechanism' in h), None)
            for row in rows:
                if len(row) <= max(ia, ib):
                    continue
                edges.append({
                    "source": row[ia], "target": row[ib],
                    "type": "hostile",
                    "note": row[imech] if imech and imech < len(row) else None,
                    "evidence_level": row[iev] if iev and iev < len(row) else "Uncertain",
                    "source_file": source_file,
                })

        # Soil restorers: Plant, Category, Mechanism (single-plant table)
        elif 'plant' in headers and any('exhaust' in h or 'restor' in h or 'category' in h for h in headers):
            ipl = headers.index('plant')
            iev = next((i for i, h in enumerate(headers) if 'evidence' in h), None)
            imech = next((i for i, h in enumerate(headers) if 'mechanism' in h or 'exhaust' in h), None)
            icat = next((i for i, h in enumerate(headers) if 'category' in h), None)
            for row in rows:
                if ipl >= len(row):
                    continue
                plant = row[ipl].strip()
                if not plant:
                    continue
                nodes.append({
                    "id": plant,
                    "cat": row[icat] if icat and icat < len(row) else None,
                    "notes": row[imech] if imech and imech < len(row) else None,
                    "evidence_level": row[iev] if iev and iev < len(row) else "Uncertain",
                    "source_file": source_file,
                })

        # Grafting: Rootstock, Scion
        elif 'rootstock' in headers and 'scion' in headers:
            ia = headers.index('rootstock')
            ib = headers.index('scion')
            iev = next((i for i, h in enumerate(headers) if 'evidence' in h), None)
            inote = next((i for i, h in enumerate(headers) if 'note' in h), None)
            for row in rows:
                if len(row) <= max(ia, ib):
                    continue
                edges.append({
                    "source": row[ia], "target": row[ib],
                    "type": "grafting",
                    "note": row[inote] if inote and inote < len(row) else None,
                    "evidence_level": row[iev] if iev and iev < len(row) else "Uncertain",
                    "source_file": source_file,
                })

        # Windbreak / structural: Tool plant, Protected crop
        elif any('tool' in h for h in headers) or ('structural' in ' '.join(headers)):
            itool = next((i for i, h in enumerate(headers) if 'tool' in h or 'structural' in h), None)
            iprot = next((i for i, h in enumerate(headers) if 'protect' in h or 'crop' in h), None)
            iev = next((i for i, h in enumerate(headers) if 'evidence' in h), None)
            if itool is not None and iprot is not None:
                for row in rows:
                    if len(row) <= max(itool, iprot):
                        continue
                    edges.append({
                        "source": row[itool], "target": row[iprot],
                        "type": "windbreak",
                        "evidence_level": row[iev] if iev and iev < len(row) else "Uncertain",
                        "source_file": source_file,
                    })

    return nodes, edges


def _extract_hakim_plants(html: str, source_file: str) -> list:
    """Extract plant names from AILMENTS structure."""
    idx = html.find('AILMENTS=[') if 'AILMENTS=[' in html else html.find('AILMENTS = [')
    if idx < 0:
        idx = html.find('AILMENTS')
    if idx < 0:
        return []

    # Find the opening bracket
    bracket_idx = html.find('[', idx)
    if bracket_idx < 0:
        return []

    # Extract the whole array by bracket matching
    depth = 0
    end = bracket_idx
    for i, ch in enumerate(html[bracket_idx:], bracket_idx):
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    raw = html[bracket_idx:end]

    # Extract plant names from entries: first element of each entry tuple is plant name
    # entries look like: ["Plant name","arabic",...] inside arrays
    plants = []
    seen = set()
    for m in re.finditer(r'\[(?:"([^"]+)"|\'([^\']+)\')', raw):
        name = m.group(1) or m.group(2)
        if name and name not in seen and len(name) > 1 and not name.startswith('FEV') and not name.startswith('Q ') and len(name) < 60:
            seen.add(name)
            plants.append({
                "id": name,
                "cat": "Medicinal",
                "source_file": source_file,
            })
    return plants


# ── Per-file extraction ───────────────────────────────────────────────────────

def _extract_html_file(path: Path, fname: str):
    """Dispatch to correct parser based on JS array names present."""
    html = path.read_text(encoding='utf-8', errors='replace')
    nodes = []
    edges = []

    # RAW_NODES / RAW_LINKS (chat1/network, may be tuples or objects)
    raw_nodes = _extract_named_array(html, 'RAW_NODES')
    if raw_nodes:
        for r in raw_nodes:
            if isinstance(r, (list, tuple)):
                n = _node_from_tuple2(r, fname)
            else:
                n = _node_from_obj(r, fname)
            if n and n.get('id'):
                nodes.append(n)

    raw_links = _extract_named_array(html, 'RAW_LINKS')
    if raw_links:
        for r in raw_links:
            if isinstance(r, (list, tuple)):
                e = _edge_from_tuple4(r, fname)
            else:
                e = _edge_from_obj(r, fname)
            if e:
                edges.append(e)

    # RAW_EDGES (chat3/plant_network)
    raw_edges = _extract_named_array(html, 'RAW_EDGES')
    for r in raw_edges:
        e = _edge_from_obj(r, fname) if isinstance(r, dict) else _edge_from_tuple4(r, fname)
        if e:
            edges.append(e)

    # RN / RL (chat1/network_corrected)
    rn = _extract_named_array(html, 'RN')
    for r in rn:
        n = _node_from_tuple2(r, fname) if isinstance(r, (list, tuple)) else _node_from_obj(r, fname)
        if n and n.get('id'):
            nodes.append(n)

    rl = _extract_named_array(html, 'RL')
    for r in rl:
        e = _edge_from_tuple4(r, fname) if isinstance(r, (list, tuple)) else _edge_from_obj(r, fname)
        if e:
            edges.append(e)

    # const D (catalog format — 7-tuple)
    d_arr = _extract_named_array(html, 'D')
    for r in d_arr:
        if isinstance(r, (list, tuple)):
            n = _node_from_tuple7(r, fname)
        else:
            n = _node_from_obj(r, fname)
        if n and n.get('id'):
            nodes.append(n)

    # ND / LD (chat3/plant_network)
    nd = _extract_named_array(html, 'ND')
    for r in nd:
        n = _node_from_obj(r, fname) if isinstance(r, dict) else _node_from_tuple2(r, fname)
        if n and n.get('id'):
            nodes.append(n)

    ld = _extract_named_array(html, 'LD')
    for r in ld:
        e = _edge_from_obj(r, fname) if isinstance(r, dict) else _edge_from_tuple4(r, fname)
        if e:
            edges.append(e)

    # NODES / LINKS (chat3/permaculture_network)
    nodes_arr = _extract_named_array(html, 'NODES')
    for r in nodes_arr:
        n = _node_from_obj(r, fname) if isinstance(r, dict) else _node_from_tuple2(r, fname)
        if n and n.get('id'):
            nodes.append(n)

    links_arr = _extract_named_array(html, 'LINKS')
    for r in links_arr:
        e = _edge_from_obj(r, fname) if isinstance(r, dict) else _edge_from_tuple4(r, fname)
        if e:
            edges.append(e)

    # HTML tables (verified_reference)
    tn, te = _parse_html_tables(html, fname)
    nodes.extend(tn)
    edges.extend(te)

    # Hakim catalog — medicinal plants
    if 'AILMENTS' in html:
        nodes.extend(_extract_hakim_plants(html, fname))

    return nodes, edges


def _extract_conversation(path: Path, fname: str):
    """Extract from conversation.json — assistant html_widget blocks."""
    data = json.loads(path.read_text(encoding='utf-8', errors='replace'))
    nodes = []
    edges = []
    source_file = fname

    for msg in data:
        if msg.get('role') != 'assistant':
            continue
        for content in msg.get('contents', []):
            if content.get('type') != 'html_widget':
                continue
            html = str(content['content'])

            # DATA (large catalog 7-tuple)
            d_arr = _extract_named_array(html, 'DATA')
            for r in d_arr:
                n = _node_from_tuple7(r, source_file) if isinstance(r, (list, tuple)) else _node_from_obj(r, source_file)
                if n and n.get('id'):
                    nodes.append(n)

            # rawNodes / rawLinks
            rn = _extract_named_array(html, 'rawNodes')
            for r in rn:
                n = _node_from_obj(r, source_file) if isinstance(r, dict) else _node_from_tuple2(r, source_file)
                if n and n.get('id'):
                    nodes.append(n)

            rl = _extract_named_array(html, 'rawLinks')
            for r in rl:
                e = _edge_from_obj(r, source_file) if isinstance(r, dict) else _edge_from_tuple4(r, source_file)
                if e:
                    edges.append(e)

            # const D
            d2 = _extract_named_array(html, 'D')
            for r in d2:
                n = _node_from_tuple7(r, source_file) if isinstance(r, (list, tuple)) else _node_from_obj(r, source_file)
                if n and n.get('id'):
                    nodes.append(n)

    return nodes, edges


# ── Main entry point ──────────────────────────────────────────────────────────

def _find_chat_dirs(root: Path) -> list:
    """Find conv_N or 'chat N' directories in root, or sibling directories."""
    def _matches(d):
        return d.is_dir() and (re.match(r'conv_\d+', d.name) or re.match(r'chat \d+', d.name))

    dirs = sorted([d for d in root.iterdir() if _matches(d)])
    if dirs:
        return dirs

    # Search sibling directories (handles 'permaculture ' vs 'permaculture' split)
    for sibling in sorted(root.parent.iterdir()):
        if sibling.is_dir() and sibling != root:
            candidates = sorted([d for d in sibling.iterdir() if _matches(d)])
            if candidates:
                return candidates

    return []


def extract_all(project_root: str) -> dict:
    root = Path(project_root).resolve()
    all_nodes = []
    all_edges = []
    files_read = []

    chat_dirs = _find_chat_dirs(root)

    for chat_dir in chat_dirs:
        # artifacts/*.html
        artifacts_dir = chat_dir / 'artifacts'
        if artifacts_dir.exists():
            for html_file in sorted(artifacts_dir.glob('*.html')):
                fname = html_file.name
                files_read.append(str(html_file))
                try:
                    n, e = _extract_html_file(html_file, fname)
                    all_nodes.extend(n)
                    all_edges.extend(e)
                except Exception as ex:
                    print(f"  WARN: {fname}: {ex}", file=sys.stderr)

        # conversation.json
        conv_file = chat_dir / 'conversation.json'
        if conv_file.exists():
            files_read.append(str(conv_file))
            try:
                n, e = _extract_conversation(conv_file, 'conversation.json')
                all_nodes.extend(n)
                all_edges.extend(e)
            except Exception as ex:
                print(f"  WARN: conversation.json in {chat_dir.name}: {ex}", file=sys.stderr)

        # files/*.md / *.txt (skip binary)
        files_dir = chat_dir / 'files'
        if files_dir.exists():
            for txt_file in sorted(files_dir.glob('*.md')) + sorted(files_dir.glob('*.txt')):
                files_read.append(str(txt_file))
                # parse markdown tables
                try:
                    text = txt_file.read_text(encoding='utf-8', errors='replace')
                    n, e = _parse_md_tables(text, txt_file.name)
                    all_nodes.extend(n)
                    all_edges.extend(e)
                except Exception as ex:
                    print(f"  WARN: {txt_file.name}: {ex}", file=sys.stderr)

    # Clean nulls
    all_nodes = [n for n in all_nodes if n and n.get('id')]
    all_edges = [e for e in all_edges if e and e.get('source') and e.get('target')]

    result = {"nodes": all_nodes, "edges": all_edges}

    out_dir = root / 'output'
    out_dir.mkdir(exist_ok=True)
    (out_dir / 'raw_extracted.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8'
    )

    return result


def _parse_md_tables(text: str, source_file: str):
    """Parse markdown tables with plant/relationship columns."""
    nodes = []
    edges = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('|') and '|' in line[1:]:
            header_cells = [c.strip() for c in line.strip('|').split('|')]
            headers = [h.lower() for h in header_cells]
            # skip separator line
            i += 1
            if i < len(lines) and re.match(r'\|[-| :]+\|', lines[i].strip()):
                i += 1
            # read rows
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip('|').split('|')]
                row = dict(zip(header_cells, cells))
                # detect edge table
                src_key = next((k for k in row if k.lower() in ('plant a', 'source', 'plant')), None)
                tgt_key = next((k for k in row if k.lower() in ('plant b', 'target')), None)
                typ_key = next((k for k in row if k.lower() in ('type', 'relationship', 'category', 'cat')), None)
                if src_key and tgt_key:
                    edges.append({
                        "source": row[src_key],
                        "target": row[tgt_key],
                        "type": row.get(typ_key, 'companion') if typ_key else 'companion',
                        "source_file": source_file,
                    })
                elif src_key and typ_key:
                    nodes.append({
                        "id": row[src_key],
                        "cat": row.get(typ_key),
                        "source_file": source_file,
                    })
                i += 1
            continue
        i += 1
    return nodes, edges


if __name__ == '__main__':
    project_root = sys.argv[1] if len(sys.argv) > 1 else '.'
    result = extract_all(project_root)
    node_count = len(result['nodes'])
    edge_count = len(result['edges'])
    print(f"node_count={node_count}  edge_count={edge_count}")
    if node_count > 100 and edge_count > 50:
        print("PASS")
    else:
        print(f"FAIL — node_count={node_count} (need >100), edge_count={edge_count} (need >50)")
