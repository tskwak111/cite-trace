#!/usr/bin/env python3
"""Adjudicate two annotation files into a single adjudicated file.

The adjudicator file (if supplied) is the source of truth for
every case. Where the adjudicator file omits a case, the
majority vote between annotator A and annotator B is used;
ties are surfaced as a separate list for human review.

This is the human-in-the-loop step of the gold-set pipeline.
The script does not adjudicate; it merges. The adjudicator is
typically a senior domain expert who reviews the per-case
disagreements the IAA script surfaced and writes a
judgement file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = REPO_ROOT / "contracts" / "schemas" / "goldset-annotation.v1.schema.json"


def _read_jsonl(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        out[record["case_id"]] = record
    return out


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _majority(a: Any, b: Any) -> tuple[Any, bool]:
    """Return (value, was_tie) for a non-set dimension."""
    if a == b:
        return a, False
    return a, True


def _set_majority(a: Any, b: Any) -> tuple[Any, bool]:
    if isinstance(a, list):
        a = set(a)
    if isinstance(b, list):
        b = set(b)
    if a == b:
        return sorted(a), False
    return sorted(a | b), a != b


SET_DIMENSIONS = {"gold_citation_intents_json", "gold_transformations_json", "gold_source_span_ids_json", "gold_scope_observations_json", "claim_qualifiers_json"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--a", type=Path, required=True, help="annotator A JSONL")
    parser.add_argument("--b", type=Path, required=True, help="annotator B JSONL")
    parser.add_argument(
        "--adjudicator",
        type=Path,
        default=None,
        help="adjudicator JSONL; if supplied, it overrides A and B for cases it covers",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--ties",
        type=Path,
        default=None,
        help="write the list of case_ids that ended in a tie to this path",
    )
    args = parser.parse_args()

    a = _read_jsonl(args.a)
    b = _read_jsonl(args.b)
    adjudicator = _read_jsonl(args.adjudicator) if args.adjudicator else {}

    case_ids = sorted(set(a) | set(b))
    merged: list[dict] = []
    ties: list[str] = []
    for case_id in case_ids:
        if case_id in adjudicator:
            record = dict(adjudicator[case_id])
            record["annotation_status"] = "adjudicated"
            merged.append(record)
            continue
        left = a.get(case_id, {})
        right = b.get(case_id, {})
        base = dict(left or right)
        tie_here = False
        for dim in (
            "gold_evidence_relation",
            "resolution_status",
            "source_access_level",
            "expected_abstention_code",
            "claim_text",
            "claim_start_offset",
            "claim_end_offset",
            "gold_work_id",
            "gold_work_version_id",
            "domain",
            "split",
        ):
            lv = left.get(dim)
            rv = right.get(dim)
            if lv is None:
                base[dim] = rv
                continue
            if rv is None:
                base[dim] = lv
                continue
            value, was_tie = _majority(lv, rv)
            base[dim] = value
            tie_here = tie_here or was_tie
        for dim in SET_DIMENSIONS:
            lv = left.get(dim, []) or []
            rv = right.get(dim, []) or []
            value, was_tie = _set_majority(lv, rv)
            base[dim] = value
            tie_here = tie_here or was_tie
        base["annotation_status"] = "adjudicated"
        merged.append(base)
        if tie_here:
            ties.append(case_id)

    _write_jsonl(args.output, merged)
    if args.ties is not None:
        _write_jsonl(args.ties, [{"case_id": c, "reason": "no adjudicator override"} for c in ties])
    print(f"merged {len(merged)} cases; ties={len(ties)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
