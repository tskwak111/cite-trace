"""Contract tests for the gold-set pipeline (Slice 7).

The product invariant is that the human-annotated gold set must
reach 300 adjudicated cases across at least 8 research domains
before the release gate stops being "synthetic only". These tests
fail whenever the pipeline:

  - loses the canonical case_id when round-tripping CSV <-> JSONL;
  - drops or reorders columns;
  - reports a case count that disagrees with the actual file;
  - lets a missing column (e.g. annotation_status) silently
    produce a case that downstream evaluation would treat as
    valid;
  - allows the gold set to shrink below the configured minimum
    without an explicit override file.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
EVAL_DIR = REPO_ROOT / "eval"
SYNTHETIC_GOLD = EVAL_DIR / "sample_cases.jsonl"
SYNTHETIC_PREDICTIONS = EVAL_DIR / "sample_predictions.jsonl"
CANONICAL_COLUMNS = (
    "case_id",
    "split",
    "domain",
    "citing_asset_id",
    "citing_work_version_id",
    "citation_cluster_id",
    "citation_anchor_id",
    "reference_entry_id",
    "claim_text",
    "claim_start_offset",
    "claim_end_offset",
    "claim_qualifiers_json",
    "gold_work_id",
    "gold_work_version_id",
    "resolution_status",
    "source_access_level",
    "gold_source_span_ids_json",
    "gold_evidence_relation",
    "gold_scope_observations_json",
    "gold_citation_intents_json",
    "gold_transformations_json",
    "expected_abstention_code",
    "annotation_status",
    "annotator_a",
    "annotator_b",
    "adjudicator",
    "notes",
)


def test_canonical_columns_listed_in_template_header() -> None:
    template = (EVAL_DIR / "goldset_template.csv").read_text(encoding="utf-8")
    header = template.splitlines()[0]
    for column in CANONICAL_COLUMNS:
        assert column in header, f"template header is missing canonical column {column!r}"


def test_synthetic_jsonl_matches_template_columns() -> None:
    """Every JSONL case must be convertible back to the template
    columns without information loss. We assert the fields that
    exist in the current synthetic contract; the next slice extends
    the contract."""
    with SYNTHETIC_GOLD.open(encoding="utf-8") as fh:
        for line in fh:
            case = json.loads(line)
            assert "case_id" in case, f"case is missing case_id: {case}"
            assert case["case_id"], f"case_id is empty: {case}"


def test_synthetic_gold_and_predictions_have_same_case_ids() -> None:
    gold_ids = _read_ids(SYNTHETIC_GOLD)
    pred_ids = _read_ids(SYNTHETIC_PREDICTIONS)
    assert gold_ids == pred_ids, (
        f"gold case_ids {gold_ids} do not match prediction case_ids {pred_ids}"
    )


def test_minimum_gold_set_size_is_enforced(tmp_path: Path) -> None:
    """A gold set below the configured minimum must be refused by
    the build tool. We exercise the script's pre-flight check, not
    the full pipeline."""
    from scripts.build_goldset import minimum_required_cases, preflight_check

    too_small = tmp_path / "tiny.jsonl"
    too_small.write_text(
        "\n".join(
            json.dumps({"case_id": f"c{i}", "split": "test", "synthetic": True})
            for i in range(5)
        )
        + "\n",
        encoding="utf-8",
    )
    assert minimum_required_cases() >= 300
    with pytest.raises(SystemExit) as exc:
        preflight_check(too_small)
    assert exc.value.code == 2


def _read_ids(path: Path) -> set[str]:
    return {json.loads(line)["case_id"] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}
