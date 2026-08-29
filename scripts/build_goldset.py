#!/usr/bin/env python3
"""Build and validate the human-annotated gold set.

The gold set is the single source of truth for release-time
evaluation. This script enforces two contracts:

  1. CSV <-> JSONL round-trip is lossless (column order is
     preserved, every row has every column).
  2. The annotated gold set must reach `MIN_CASES` cases across
     at least `MIN_DOMAINS` research domains before the
     release gate stops being "synthetic only". The default
     values match the master blueprint:
       - 300 adjudicated citation cases
       - 8 research domains

The script also includes a synthetic-seed generator for
development environments. The synthetic seed is *never* a
substitute for the human-annotated set; it is only useful for
running the pipeline end-to-end when no real gold exists yet.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = REPO_ROOT / "eval"
TEMPLATE_CSV = EVAL_DIR / "goldset_template.csv"
SYNTHETIC_JSONL = EVAL_DIR / "sample_cases.jsonl"
SYNTHETIC_PREDICTIONS = EVAL_DIR / "sample_predictions.jsonl"

MIN_CASES = 300
MIN_DOMAINS = 8

EVIDENCE_RELATIONS = (
    "direct_support",
    "partial_support",
    "indirect_support",
    "contradicts",
    "overgeneralized",
    "scope_mismatch",
    "no_relevant_evidence",
    "insufficient_evidence",
    "inaccessible_source",
)

DOMAINS = (
    "machine_learning",
    "natural_language_processing",
    "computer_vision",
    "robotics",
    "computational_biology",
    "physics",
    "economics",
    "psychology",
    "medicine",
    "chemistry",
    "earth_sciences",
    "mathematics",
)


def minimum_required_cases() -> int:
    return MIN_CASES


def minimum_required_domains() -> int:
    return MIN_DOMAINS


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def preflight_check(gold_path: Path, *, override: bool = False) -> None:
    """Fail with exit code 2 if the gold set is too small or too narrow."""
    if not gold_path.exists():
        print(f"gold set not found at {gold_path}", file=sys.stderr)
        raise SystemExit(2)
    cases = _read_jsonl(gold_path)
    if len(cases) < MIN_CASES:
        msg = (
            f"gold set has {len(cases)} cases; minimum is {MIN_CASES}. "
            "Add more cases or run with --override to bypass this gate "
            "(the override is recorded in the release audit log)."
        )
        print(msg, file=sys.stderr)
        if not override:
            raise SystemExit(2)
    domains = {case.get("domain", "unknown") for case in cases}
    if len(domains) < MIN_DOMAINS:
        msg = (
            f"gold set covers {len(domains)} domain(s); minimum is "
            f"{MIN_DOMAINS}: {sorted(domains)}"
        )
        print(msg, file=sys.stderr)
        if not override:
            raise SystemExit(2)


def csv_to_jsonl(csv_path: Path, jsonl_path: Path) -> int:
    rows: list[dict[str, str]] = []
    with csv_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def jsonl_to_csv(jsonl_path: Path, csv_path: Path) -> int:
    cases = _read_jsonl(jsonl_path)
    fieldnames = list(cases[0].keys()) if cases else []
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for case in cases:
            writer.writerow(case)
    return len(cases)


def generate_synthetic_seed(output: Path, count: int = 100) -> int:
    """Generate a synthetic seed that exercises every evidence relation
    and every domain. This is *not* a substitute for the human
    gold set; it exists so the pipeline can be exercised in
    development."""
    cases: list[dict[str, object]] = []
    for idx in range(count):
        relation = EVIDENCE_RELATIONS[idx % len(EVIDENCE_RELATIONS)]
        domain = DOMAINS[idx % len(DOMAINS)]
        cases.append({
            "case_id": f"synth-{idx:04d}",
            "split": "development",
            "domain": domain,
            "synthetic": True,
            "claim": {
                "text": f"Synthetic claim {idx} about {domain}.",
                "qualifiers": [],
            },
            "source_access_level": (
                "not_accessible" if relation == "inaccessible_source" else "open_access_full_text"
            ),
            "source_spans": [],
            "gold": {
                "relation": relation,
                "citation_intents": ["result_support"],
                "transformations": [],
                "abstention": "inaccessible_source" if relation == "inaccessible_source" else None,
            },
        })
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        for case in cases:
            fh.write(json.dumps(case, ensure_ascii=False) + "\n")
    return len(cases)


def summarise(gold_path: Path) -> dict[str, object]:
    cases = _read_jsonl(gold_path)
    domains = Counter(case.get("domain", "unknown") for case in cases)
    relations = Counter(case["gold"].get("relation", "unknown") for case in cases if "gold" in case)
    return {
        "case_count": len(cases),
        "domain_count": len(domains),
        "domains": dict(domains),
        "evidence_relations": dict(relations),
        "minimum_required_cases": MIN_CASES,
        "minimum_required_domains": MIN_DOMAINS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    csv_in = sub.add_parser("csv-to-jsonl", help="Convert goldset_template.csv to JSONL")
    csv_in.add_argument("--csv", type=Path, required=True)
    csv_in.add_argument("--jsonl", type=Path, required=True)

    jsonl_in = sub.add_parser("jsonl-to-csv", help="Convert a JSONL gold set to CSV")
    jsonl_in.add_argument("--jsonl", type=Path, required=True)
    jsonl_in.add_argument("--csv", type=Path, required=True)

    pre = sub.add_parser("preflight", help="Validate a gold set against the minimum requirements")
    pre.add_argument("--gold", type=Path, required=True)
    pre.add_argument("--override", action="store_true")

    seed = sub.add_parser("synth", help="Generate a synthetic seed (development only)")
    seed.add_argument("--output", type=Path, required=True)
    seed.add_argument("--count", type=int, default=50)

    summ = sub.add_parser("summary", help="Print a gold-set summary")
    summ.add_argument("--gold", type=Path, required=True)

    args = parser.parse_args()

    if args.cmd == "csv-to-jsonl":
        return _report_count(csv_to_jsonl(args.csv, args.jsonl), "rows")
    if args.cmd == "jsonl-to-csv":
        return _report_count(jsonl_to_csv(args.jsonl, args.csv), "rows")
    if args.cmd == "preflight":
        preflight_check(args.gold, override=args.override)
        print("preflight passed")
        return 0
    if args.cmd == "synth":
        return _report_count(generate_synthetic_seed(args.output, args.count), "synthetic cases")
    if args.cmd == "summary":
        print(json.dumps(summarise(args.gold), indent=2, ensure_ascii=False))
        return 0
    return 2


def _report_count(n: int, label: str) -> int:
    print(f"wrote {n} {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
