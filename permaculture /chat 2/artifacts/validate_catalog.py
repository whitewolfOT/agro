#!/usr/bin/env python3
"""
validate_catalog.py — Hakim Medicine Catalog Validator
======================================================
Validates catalog entries output by the hakim-medicine-catalog skill.

Usage:
    python validate_catalog.py <input_file.md>
    python validate_catalog.py --check-formula <formula_name> references/formulas.md
    python validate_catalog.py --check-herb <herb_name> references/herbs.md

The validator checks:
    1. Required columns are present in every table row
    2. Temperament notation follows the Hot/Cold °N, Moist/Dry °N format
    3. Toxic entries carry a CAUTION flag
    4. Preparation method is not empty
    5. Administration route is specified
    6. Formula references resolve to entries in references/formulas.md
    7. Herb references resolve to entries in references/herbs.md
"""

import sys
import re
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────────

REQUIRED_COLUMNS = {
    "category",
    "ingredient",
    "preparation",
    "administration",
    "traditional use",
}

TOXIC_KEYWORDS = [
    "aconite", "bish", "mercury", "paara", "colocynth", "scammony",
    "opium", "camphor", "litharge", "lead", "verdigris", "arsenic",
    "copper sulfate", "zibaq", "kajjali", "toxic", "viper", "scorpion",
    "strychnine", "nux vomica", "datura", "dhatura", "stramonium",
]

TEMPERAMENT_PATTERN = re.compile(
    r"(Hot|Cold)\s+\d°[,\s]+(Moist|Dry)\s+\d°",
    re.IGNORECASE,
)

CAUTION_MARKERS = ["⚠️", "CAUTION", "TOXIC", "HIGHLY TOXIC", "WARNING"]

# ── Helpers ───────────────────────────────────────────────────────────────────


def extract_table_rows(text: str) -> list[dict]:
    """Parse Markdown table rows into list of dicts keyed by header name."""
    rows = []
    header = None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if header is None:
            header = [h.lower().strip() for h in cells]
            continue
        if set(cells) <= {"", "-", "---", "----"}:
            # Separator row
            continue
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells)))
    return rows


def check_required_columns(headers: set[str]) -> list[str]:
    errors = []
    for col in REQUIRED_COLUMNS:
        if not any(col in h for h in headers):
            errors.append(f"Missing required column: '{col}'")
    return errors


def check_temperament(row: dict) -> list[str]:
    errors = []
    for key, val in row.items():
        if "temperament" in key or "mizaj" in key:
            if val and not TEMPERAMENT_PATTERN.search(val):
                errors.append(
                    f"Temperament field '{val}' does not match expected format "
                    f"'Hot/Cold N°, Moist/Dry N°'"
                )
    return errors


def check_toxic_caution(row: dict, row_text: str) -> list[str]:
    errors = []
    ingredient_val = ""
    for key, val in row.items():
        if "ingredient" in key or "formula" in key or "name" in key:
            ingredient_val += " " + val.lower()

    is_toxic = any(kw in ingredient_val for kw in TOXIC_KEYWORDS)
    has_caution = any(marker in row_text for marker in CAUTION_MARKERS)

    if is_toxic and not has_caution:
        errors.append(
            f"Row contains potentially toxic ingredient but no CAUTION marker: "
            f"'{ingredient_val.strip()}'"
        )
    return errors


def check_empty_fields(row: dict) -> list[str]:
    errors = []
    for col in ["preparation", "administration"]:
        for key, val in row.items():
            if col in key and not val:
                errors.append(f"Empty required field: '{key}'")
    return errors


def validate_catalog(text: str, source: str = "<input>") -> list[str]:
    all_errors = []
    rows = extract_table_rows(text)

    if not rows:
        return [f"{source}: No Markdown table found in input."]

    headers = set(rows[0].keys()) if rows else set()
    all_errors.extend(
        f"{source}: {e}" for e in check_required_columns(headers)
    )

    for i, row in enumerate(rows, start=1):
        row_text = " ".join(row.values())
        row_errors = []
        row_errors.extend(check_temperament(row))
        row_errors.extend(check_toxic_caution(row, row_text))
        row_errors.extend(check_empty_fields(row))
        for e in row_errors:
            all_errors.append(f"{source} row {i}: {e}")

    return all_errors


def check_formula_reference(formula_name: str, formulas_file: Path) -> list[str]:
    if not formulas_file.exists():
        return [f"references/formulas.md not found at {formulas_file}"]
    text = formulas_file.read_text(encoding="utf-8")
    if formula_name.lower() not in text.lower():
        return [f"Formula '{formula_name}' not found in references/formulas.md"]
    return []


def check_herb_reference(herb_name: str, herbs_file: Path) -> list[str]:
    if not herbs_file.exists():
        return [f"references/herbs.md not found at {herbs_file}"]
    text = herbs_file.read_text(encoding="utf-8")
    if herb_name.lower() not in text.lower():
        return [f"Herb '{herb_name}' not found in references/herbs.md"]
    return []


# ── CLI ───────────────────────────────────────────────────────────────────────


def main():
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(0)

    errors = []

    if "--check-formula" in args:
        idx = args.index("--check-formula")
        formula_name = args[idx + 1] if idx + 1 < len(args) else ""
        formulas_path = Path(args[idx + 2]) if idx + 2 < len(args) else Path("references/formulas.md")
        errors.extend(check_formula_reference(formula_name, formulas_path))

    elif "--check-herb" in args:
        idx = args.index("--check-herb")
        herb_name = args[idx + 1] if idx + 1 < len(args) else ""
        herbs_path = Path(args[idx + 2]) if idx + 2 < len(args) else Path("references/herbs.md")
        errors.extend(check_herb_reference(herb_name, herbs_path))

    else:
        input_path = Path(args[0])
        if not input_path.exists():
            print(f"ERROR: File not found: {input_path}")
            sys.exit(1)
        text = input_path.read_text(encoding="utf-8")
        errors.extend(validate_catalog(text, source=str(input_path)))

    if errors:
        print("VALIDATION ERRORS:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("✓ Catalog validation passed — no issues found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
