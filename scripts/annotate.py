#!/usr/bin/env python3
"""Human-annotated gold-set helper.

Three sub-commands:

  init     write a starter JSONL from a list of case_ids
  validate check every row against the JSON Schema
  summary  print per-domain and per-relation counts

The pipeline accepts JSONL (one row per case) and
validates against
`contracts/schemas/goldset-annotation.v1.schema.json`.
The intent is to be small enough to fit in a shared
spreadsheet workflow: an annotator can edit the JSONL
in any text editor, or convert to CSV with
`scripts/build_goldset.py jsonl-to-csv` and edit in a
spreadsheet, then convert back.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("jsonschema is required; install with: uv pip install jsonschema", file=sys.stderr)
    raise

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = REPO_ROOT / "contracts" / "schemas" / "goldset-annotation.v1.schema.json"


def _load_schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _starter_row(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "split": "development",
        "domain": "machine_learning",
        "citing_asset_id": "",
        "citing_work_version_id": "",
        "citation_cluster_id": "",
        "citation_anchor_id": "",
        "reference_entry_id": "",
        "claim_text": "",
        "claim_start_offset": 0,
        "claim_end_offset": 0,
        "claim_qualifiers_json": [],
        "gold_work_id": "",
        "gold_work_version_id": "",
        "resolution_status": "ambiguous",
        "source_access_level": "open_access_full_text",
        "gold_source_span_ids_json": [],
        "gold_evidence_relation": "direct_support",
        "gold_scope_observations_json": [],
        "gold_citation_intents_json": ["result_support"],
        "gold_transformations_json": [],
        "expected_abstention_code": None,
        "annotation_status": "pending",
        "annotator_a": "",
        "annotator_b": "",
        "adjudicator": "",
        "notes": "",
    }


def cmd_init(args: argparse.Namespace) -> int:
    if args.case_ids_file.exists():
        case_ids = [
            line.strip() for line in args.case_ids_file.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
    else:
        case_ids = [c.strip() for c in args.case_ids.split(",") if c.strip()]
    if not case_ids:
        print("no case_ids supplied; use --case-ids or --case-ids-file", file=sys.stderr)
        return 2
    rows = [_starter_row(case_id) for case_id in case_ids]
    _write_jsonl(args.output, rows)
    print(f"wrote {len(rows)} starter rows to {args.output}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    schema = _load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    rows = _read_jsonl(args.input)
    valid = 0
    invalid = 0
    errors: list[tuple[int, str, str]] = []
    for index, row in enumerate(rows, start=1):
        errors_for_row = sorted(validator.iter_errors(row), key=lambda e: e.path)
        if not errors_for_row:
            valid += 1
            continue
        invalid += 1
        for err in errors_for_row:
            path = ".".join(str(p) for p in err.absolute_path) or "<root>"
            errors.append((index, path, err.message))
    for index, path, message in errors[: args.max_errors]:
        print(f"row {index}: {path}: {message}", file=sys.stderr)
    print(f"validated {len(rows)} rows: {valid} valid, {invalid} invalid")
    return 0 if invalid == 0 else 1


def cmd_summary(args: argparse.Namespace) -> int:
    rows = _read_jsonl(args.input)
    domains = Counter(r.get("domain", "<missing>") for r in rows)
    relations = Counter(r.get("gold_evidence_relation", "<missing>") for r in rows)
    statuses = Counter(r.get("annotation_status", "<missing>") for r in rows)
    print(json.dumps({
        "case_count": len(rows),
        "domain_count": len(domains),
        "domains": dict(domains),
        "evidence_relations": dict(relations),
        "annotation_statuses": dict(statuses),
    }, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="write a starter JSONL from a list of case_ids")
    init.add_argument("--case-ids", default="", help="comma-separated case_ids")
    init.add_argument("--case-ids-file", type=Path, default=Path("-"), help="file with one case_id per line; - for stdin")
    init.add_argument("--output", type=Path, required=True)
    init.set_defaults(func=cmd_init)

    validate = sub.add_parser("validate", help="validate every row against the JSON Schema")
    validate.add_argument("--input", type=Path, required=True)
    validate.add_argument("--max-errors", type=int, default=20)
    validate.set_defaults(func=cmd_validate)

    summary = sub.add_parser("summary", help="print per-domain and per-relation counts")
    summary.add_argument("--input", type=Path, required=True)
    summary.set_defaults(func=cmd_summary)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
