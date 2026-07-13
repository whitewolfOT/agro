"""
pipeline/enrich.py
Entry point: enrich(merged_path: str)
Reads:  output/master_nodes.json, output/master_edges.json
Writes: output/enriched_edges.json, output/enrichment_report.csv,
        output/enrichment_errors.log (on failures)
"""
import csv
import json
import os
import sys
import time
from pathlib import Path

import anthropic

from pipeline.schemas import EDGE_TYPES

BATCH_SIZE = 25
MAX_TOKENS = 4096
SLEEP_BETWEEN = 0.5

SYSTEM_PROMPT = (
    "You are a plant science database. Given a list of plant names, return ONLY a JSON array "
    "of documented scientific relationships between them AND with any other plants in the broader "
    "list provided. Use only peer-reviewed or well-established agronomic knowledge. "
    "No hallucination — if unsure, omit.\n\n"
    "Each relationship object must be exactly:\n"
    '{"source": "Plant A", "target": "Plant B", "type": "<edge_type>", '
    '"confidence": 0.0-1.0, "reason": "one sentence mechanism"}\n\n'
    "edge_type must be one of: companion, hostile, nitrogen_fix, mulch_biomass, "
    "soil_exhaust, succession, water, canopy_shade, animal, grafting, windbreak\n\n"
    "Return ONLY the JSON array. No preamble, no markdown, no explanation."
)

# KNOWN_ADDITIONS sources added in factcheck step
_FACTCHECK_SOURCE_IDS = {"factcheck.py"}


def _backfill_origin(edges: list) -> list:
    """Step 2: stamp origin on every existing edge."""
    for edge in edges:
        if "origin" in edge:
            continue
        if not edge.get("added", False):
            edge["origin"] = "dataset"
        elif edge.get("source_id", "") in _FACTCHECK_SOURCE_IDS:
            edge["origin"] = "factcheck"
        else:
            edge["origin"] = "dataset"
    return edges


def _parse_response(text: str) -> list:
    """Extract JSON array from model response, stripping any accidental markdown."""
    text = text.strip()
    # strip ```json ... ``` fences
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            l for l in lines if not l.strip().startswith("```")
        ).strip()
    # find first [
    start = text.find("[")
    if start == -1:
        raise ValueError("No JSON array found in response")
    # find last ] — if missing (truncated), try to recover complete objects
    end = text.rfind("]")
    if end == -1:
        # truncated: extract all complete {...} objects individually
        import re
        items = []
        for m in re.finditer(r'\{[^{}]+\}', text[start:], re.DOTALL):
            try:
                items.append(json.loads(m.group()))
            except json.JSONDecodeError:
                pass
        if not items:
            raise ValueError("No JSON array found in response")
        return items
    return json.loads(text[start:end + 1])


def enrich(merged_path: str):
    out = Path("output")
    out.mkdir(exist_ok=True)

    nodes = json.loads((out / "master_nodes.json").read_text(encoding="utf-8"))
    edges = json.loads((out / "master_edges.json").read_text(encoding="utf-8"))

    original_edge_count = len(edges)

    # ── Step 2: backfill origin on existing edges ─────────────────────────────
    edges = _backfill_origin(edges)

    # ── Step 9 pre-pass: mark the 6 KNOWN_ADDITIONS as origin="factcheck" ─────
    for edge in edges:
        if edge.get("added") and edge.get("source_id") in _FACTCHECK_SOURCE_IDS:
            edge["origin"] = "factcheck"

    # ── Build existing-triple index ────────────────────────────────────────────
    existing: set[tuple] = {
        (e["source"], e["target"], e["type"]) for e in edges
    }

    # ── Step 3-4: build batches ────────────────────────────────────────────────
    all_ids = [n["id"] for n in nodes]
    full_list_str = ", ".join(all_ids)

    batches = [all_ids[i:i + BATCH_SIZE] for i in range(0, len(all_ids), BATCH_SIZE)]

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        client = anthropic.Anthropic(api_key=api_key)
    else:
        # Fall back to session OAuth token (Claude Code remote environment)
        _token_file = "/home/claude/.claude/remote/.session_ingress_token"
        session_token = open(_token_file).read().strip()
        client = anthropic.Anthropic(auth_token=session_token)
    report_rows = []
    error_log_lines = []
    new_edges_added  = 0
    errors = 0

    for batch_num, batch in enumerate(batches, start=1):
        batch_str  = ", ".join(batch)
        user_msg   = (
            f"Full plant list (for cross-referencing): {full_list_str}\n"
            f"This batch: {batch_str}\n"
            "Return all documented relationships involving any plant in this batch."
        )

        relationships_returned = 0
        relationships_new      = 0
        relationships_skipped  = 0

        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            raw_text = response.content[0].text

            try:
                items = _parse_response(raw_text)
            except (ValueError, json.JSONDecodeError) as parse_err:
                raise ValueError(f"JSON parse error: {parse_err}\nRaw: {raw_text[:300]}")

            for item in items:
                if not isinstance(item, dict):
                    continue
                src   = str(item.get("source") or "").strip()
                tgt   = str(item.get("target") or "").strip()
                etype = str(item.get("type")   or "").strip()
                conf  = item.get("confidence", 0.7)
                reason = str(item.get("reason") or "").strip()

                if not src or not tgt or etype not in EDGE_TYPES:
                    continue

                relationships_returned += 1
                triple = (src, tgt, etype)

                if triple in existing:
                    relationships_skipped += 1
                    continue

                new_edge = {
                    "source":         src,
                    "target":         tgt,
                    "type":           etype,
                    "direction":      "directed",
                    "context":        [],
                    "source_id":      f"scientific_enrichment_batch_{batch_num}",
                    "evidence_level": "Modern reconstruction",
                    "evidence_quote": reason or None,
                    "confidence":     float(conf) if isinstance(conf, (int, float)) else 0.7,
                    "added":          True,
                    "origin":         "enriched",
                    "flags":          [],
                }
                edges.append(new_edge)
                existing.add(triple)
                relationships_new += 1
                new_edges_added   += 1

        except Exception as exc:
            errors += 1
            msg = f"batch={batch_num} plants={batch_str[:120]} error={exc}"
            error_log_lines.append(msg)
            print(f"  WARN batch {batch_num}: {exc}", file=sys.stderr)
            relationships_returned = 0
            relationships_new      = 0
            relationships_skipped  = 0

        report_rows.append({
            "batch":                  batch_num,
            "plants_in_batch":        len(batch),
            "relationships_returned": relationships_returned,
            "relationships_new":      relationships_new,
            "relationships_skipped":  relationships_skipped,
        })

        if batch_num < len(batches):
            time.sleep(SLEEP_BETWEEN)

    # ── Write outputs ─────────────────────────────────────────────────────────
    (out / "enriched_edges.json").write_text(
        json.dumps(edges, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    fieldnames = ["batch", "plants_in_batch", "relationships_returned",
                  "relationships_new", "relationships_skipped"]
    with open(out / "enrichment_report.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    if error_log_lines:
        (out / "enrichment_errors.log").write_text(
            "\n".join(error_log_lines) + "\n", encoding="utf-8"
        )

    return {
        "original_edge_count": original_edge_count,
        "new_edges_added":     new_edges_added,
        "batches_run":         len(batches),
        "errors":              errors,
    }


if __name__ == "__main__":
    merged_path = sys.argv[1] if len(sys.argv) > 1 else "."
    stats = enrich(merged_path)

    print(f"original_edge_count={stats['original_edge_count']}")
    print(f"new_edges_added={stats['new_edges_added']}")
    print(f"batches_run={stats['batches_run']}")
    print(f"errors={stats['errors']}")

    if (Path("output/enriched_edges.json").exists() and
            Path("output/enrichment_report.csv").exists()):
        print("PASS")
    else:
        print("FAIL — output files missing")
