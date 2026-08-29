"""Contract tests for the human-annotated gold-set pipeline
(Slice 14, ADR-0012).

These tests pin the four-script + one-schema pipeline that
drives the human-in-the-loop annotation flow. The 300
human-annotated cases themselves are out of scope (the
ADRs acknowledge this is human labour, not an AI task);
the tests verify the *infrastructure* is correct.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
ANNOTATE = REPO_ROOT / "scripts" / "annotate.py"
COMPUTE_IAA = REPO_ROOT / "scripts" / "compute_iaa.py"
ADJUDICATE = REPO_ROOT / "scripts" / "adjudicate.py"
SCHEMA = REPO_ROOT / "contracts" / "schemas" / "goldset-annotation.v1.schema.json"


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed (rc={result.returncode}): {' '.join(cmd)}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def test_schema_is_valid_json_schema() -> None:
    """The annotation schema must itself be a valid JSON
    Schema 2020-12 document. A broken schema would silently
    accept malformed rows."""
    import jsonschema

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)


def test_annotate_init_writes_starter_rows(tmp_path: Path) -> None:
    output = tmp_path / "starter.jsonl"
    _run([
        sys.executable, str(ANNOTATE), "init",
        "--case-ids", "case-001,case-002,case-003",
        "--output", str(output),
    ])
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 3
    assert {r["case_id"] for r in rows} == {"case-001", "case-002", "case-003"}


def test_annotate_validate_accepts_valid_row(tmp_path: Path) -> None:
    starter = tmp_path / "valid.jsonl"
    rows = [_starter_row("good-case")]
    starter.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    result = _run([
        sys.executable, str(ANNOTATE), "validate",
        "--input", str(starter),
    ], check=False)
    assert result.returncode == 0
    assert "1 valid" in result.stdout


def test_annotate_validate_rejects_invalid_row(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.jsonl"
    invalid.write_text(
        json.dumps({"case_id": "bad-case", "split": "this-is-not-a-valid-split"}) + "\n",
        encoding="utf-8",
    )
    result = _run([
        sys.executable, str(ANNOTATE), "validate",
        "--input", str(invalid),
    ], check=False)
    assert result.returncode == 1
    assert "0 valid" in result.stdout
    assert "1 invalid" in result.stdout


def test_annotate_summary_reports_per_domain_counts(tmp_path: Path) -> None:
    output = tmp_path / "summary.jsonl"
    _run([
        sys.executable, str(ANNOTATE), "init",
        "--case-ids", "a,b,c",
        "--output", str(output),
    ])
    result = _run([
        sys.executable, str(ANNOTATE), "summary",
        "--input", str(output),
    ])
    payload = json.loads(result.stdout)
    assert payload["case_count"] == 3
    assert payload["domain_count"] >= 1
    assert "evidence_relations" in payload


def test_compute_iaa_returns_perfect_agreement_for_identical_files(tmp_path: Path) -> None:
    same = tmp_path / "same.jsonl"
    rows = [_starter_row("a"), _starter_row("b")]
    same.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    result = _run([
        sys.executable, str(COMPUTE_IAA),
        "--a", str(same),
        "--b", str(same),
    ])
    payload = json.loads(result.stdout)
    for dim, info in payload["dimensions"].items():
        score = info.get("kappa", info.get("jaccard"))
        assert score == 1.0, f"{dim} must be 1.0 for identical files; got {score}"
        assert not info["below_threshold"]


def test_compute_iaa_flags_disagreement(tmp_path: Path) -> None:
    a_rows = [_starter_row("a"), _starter_row("b")]
    b_rows = [_starter_row("a"), _starter_row("b")]
    b_rows[1]["gold_evidence_relation"] = "contradicts"
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    a.write_text("\n".join(json.dumps(r) for r in a_rows) + "\n", encoding="utf-8")
    b.write_text("\n".join(json.dumps(r) for r in b_rows) + "\n", encoding="utf-8")
    result = _run([
        sys.executable, str(COMPUTE_IAA),
        "--a", str(a),
        "--b", str(b),
    ], check=False)
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    relation = payload["dimensions"]["gold_evidence_relation"]
    assert relation["kappa"] < 1.0
    assert relation["below_threshold"]


def test_adjudicate_prefers_adjudicator_override(tmp_path: Path) -> None:
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    adjudicator = tmp_path / "adj.jsonl"
    a_rows = [_starter_row("x")]
    b_rows = [_starter_row("x")]
    a_rows[0]["gold_evidence_relation"] = "direct_support"
    b_rows[0]["gold_evidence_relation"] = "contradicts"
    adjudicator_rows = [_starter_row("x")]
    adjudicator_rows[0]["gold_evidence_relation"] = "partial_support"
    a.write_text("\n".join(json.dumps(r) for r in a_rows) + "\n", encoding="utf-8")
    b.write_text("\n".join(json.dumps(r) for r in b_rows) + "\n", encoding="utf-8")
    adjudicator.write_text(
        "\n".join(json.dumps(r) for r in adjudicator_rows) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "merged.jsonl"
    _run([
        sys.executable, str(ADJUDICATE),
        "--a", str(a),
        "--b", str(b),
        "--adjudicator", str(adjudicator),
        "--output", str(output),
    ])
    merged = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert merged[0]["gold_evidence_relation"] == "partial_support"
    assert merged[0]["annotation_status"] == "adjudicated"


def test_adjudicate_marks_ties_for_human_review(tmp_path: Path) -> None:
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    a_rows = [_starter_row("x")]
    b_rows = [_starter_row("x")]
    a_rows[0]["gold_evidence_relation"] = "direct_support"
    b_rows[0]["gold_evidence_relation"] = "contradicts"
    a.write_text("\n".join(json.dumps(r) for r in a_rows) + "\n", encoding="utf-8")
    b.write_text("\n".join(json.dumps(r) for r in b_rows) + "\n", encoding="utf-8")
    output = tmp_path / "merged.jsonl"
    ties = tmp_path / "ties.jsonl"
    result = _run([
        sys.executable, str(ADJUDICATE),
        "--a", str(a),
        "--b", str(b),
        "--output", str(output),
        "--ties", str(ties),
    ])
    assert "ties=1" in result.stdout
    tied = [json.loads(line) for line in ties.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert tied[0]["case_id"] == "x"


def _starter_row(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "split": "development",
        "domain": "machine_learning",
        "citing_asset_id": "asset-1",
        "citing_work_version_id": "v-1",
        "citation_cluster_id": "cluster-1",
        "citation_anchor_id": "anchor-1",
        "reference_entry_id": "ref-1",
        "claim_text": "Method A improved accuracy.",
        "claim_start_offset": 0,
        "claim_end_offset": 26,
        "claim_qualifiers_json": [],
        "gold_work_id": "w-1",
        "gold_work_version_id": "wv-1",
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
