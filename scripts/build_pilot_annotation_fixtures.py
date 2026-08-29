#!/usr/bin/env python3
"""Build the annotation-pilot fixtures for the v1.7 verification.

The pilot is five citation cases that two domain experts
(labeled "alice" and "bob") annotate independently. A senior
adjudicator (labeled "ada") then writes the adjudicated file.

The case contents are public, simplified claims whose
correct labels are uncontroversial so the IAA exercise can
demonstrate the pipeline mechanics without needing
external domain expertise.

  case_id            claim summary
  pilot-001          direct_support      "Method A improved accuracy..."
  pilot-002          partial_support     "Method B scales to 1M examples..."
  pilot-003          overgeneralized     "All neural networks overfit..."
  pilot-004          inaccessible_source "According to Smith (private comm.)..."
  pilot-005          contradicts         "Our results show 50% improvement..."
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "eval" / "pilot_annotation"
OUT.mkdir(parents=True, exist_ok=True)


def _row(case_id: str, **overrides) -> dict:
    base = {
        "case_id": case_id,
        "split": "development",
        "domain": "machine_learning",
        "citing_asset_id": f"asset-{case_id}",
        "citing_work_version_id": "v-1",
        "citation_cluster_id": f"cluster-{case_id}",
        "citation_anchor_id": "anchor-1",
        "reference_entry_id": f"ref-{case_id}",
        "claim_text": "",
        "claim_start_offset": 0,
        "claim_end_offset": 0,
        "claim_qualifiers_json": [],
        "gold_work_id": "",
        "gold_work_version_id": "",
        "resolution_status": "exact_version",
        "source_access_level": "open_access_full_text",
        "gold_source_span_ids_json": ["span-1"],
        "gold_evidence_relation": "direct_support",
        "gold_scope_observations_json": [],
        "gold_citation_intents_json": ["result_support"],
        "gold_transformations_json": [],
        "expected_abstention_code": None,
        "annotation_status": "pending",
        "annotator_a": "alice",
        "annotator_b": "bob",
        "adjudicator": "",
        "notes": "",
    }
    base.update(overrides)
    return base


CASES = {
    "pilot-001": {
        "claim_text": "Method A improved accuracy from 70% to 78% on Dataset Q.",
        "claim_end_offset": 56,
        "gold_evidence_relation": "direct_support",
    },
    "pilot-002": {
        "claim_text": "Method B scales to 1M examples on a single GPU.",
        "claim_end_offset": 51,
        "gold_evidence_relation": "partial_support",
    },
    "pilot-003": {
        "claim_text": "All neural networks overfit on small datasets.",
        "claim_end_offset": 51,
        "gold_evidence_relation": "overgeneralized",
    },
    "pilot-004": {
        "claim_text": "According to Smith (private communication, 2024), the dataset is biased.",
        "claim_end_offset": 75,
        "source_access_level": "not_accessible",
        "gold_evidence_relation": "inaccessible_source",
        "expected_abstention_code": "inaccessible_source",
    },
    "pilot-005": {
        "claim_text": "Our results show a 50% improvement over the prior art.",
        "claim_end_offset": 56,
        "gold_evidence_relation": "contradicts",
    },
}


def _annotator_a() -> list[dict]:
    """Alice's annotations: agrees with the gold for all 5 cases
    so her IAA with the gold is 1.0. The annotation_status is
    'annotated_a' because she is annotator A."""
    rows = []
    for case_id, fields in CASES.items():
        row = _row(case_id, **fields)
        row["annotation_status"] = "annotated_a"
        row["notes"] = "alice: confident"
        rows.append(row)
    return rows


def _annotator_b() -> list[dict]:
    """Bob disagrees on pilot-002 and pilot-003 to demonstrate
    the IAA and adjudicator paths. His annotation_status is
    'annotated_b'."""
    rows = []
    overrides_per_case = {
        "pilot-001": {},
        "pilot-002": {"gold_evidence_relation": "direct_support"},
        "pilot-003": {"gold_evidence_relation": "scope_mismatch"},
        "pilot-004": {},
        "pilot-005": {},
    }
    for case_id, fields in CASES.items():
        merged = dict(fields)
        merged.update(overrides_per_case[case_id])
        row = _row(case_id, **merged)
        row["annotation_status"] = "annotated_b"
        row["notes"] = "bob: pilot-002 / 003 disagree"
        rows.append(row)
    return rows


def _adjudicator(a: list[dict], b: list[dict]) -> list[dict]:
    """Ada: agrees with alice on pilot-002 (direct_support is too
    strong for a scaling claim; partial_support is correct).
    On pilot-003 she agrees with bob (scope_mismatch: the
    cited work only shows overfitting on one dataset, so
    'all neural networks' is a scope mismatch). She marks every
    row 'adjudicated'."""
    a_by_id = {r["case_id"]: r for r in a}
    b_by_id = {r["case_id"]: r for r in b}
    overrides = {
        "pilot-001": a_by_id["pilot-001"]["gold_evidence_relation"],
        "pilot-002": a_by_id["pilot-002"]["gold_evidence_relation"],
        "pilot-003": b_by_id["pilot-003"]["gold_evidence_relation"],
        "pilot-004": a_by_id["pilot-004"]["gold_evidence_relation"],
        "pilot-005": a_by_id["pilot-005"]["gold_evidence_relation"],
    }
    out = []
    for case_id, fields in CASES.items():
        merged = dict(fields)
        merged["gold_evidence_relation"] = overrides[case_id]
        row = _row(case_id, **merged)
        row["annotation_status"] = "adjudicated"
        row["adjudicator"] = "ada"
        row["notes"] = "ada: adjudicated"
        out.append(row)
    return out


def _write(name: str, rows: list[dict]) -> None:
    path = OUT / name
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {path.relative_to(REPO_ROOT)} ({len(rows)} rows)")


def main() -> int:
    a = _annotator_a()
    b = _annotator_b()
    adjudicated = _adjudicator(a, b)
    _write("annotator_a.jsonl", a)
    _write("annotator_b.jsonl", b)
    _write("adjudicator.jsonl", adjudicated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
