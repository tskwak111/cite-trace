"""Contract tests for `scripts/run_release_evaluation.py`.

The release evaluation script must:
  - exit with code 2 when the gold set is empty (cannot evaluate);
  - exit with code 0 and report `passed: true` when the gold and
    prediction sets match the rubric thresholds on synthetic samples;
  - exit with code 1 and report `passed: false` when a blocking
    metric (e.g. fabricated quote count > 0) is violated;
  - never emit a hard-coded `passed: true` without reading the input.

These tests run the script as a subprocess so the contract is
checked end-to-end (the kind of gate a release pipeline will use).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPT = REPO_ROOT / "scripts" / "run_release_evaluation.py"
RUBRIC = REPO_ROOT / "eval" / "rubric.yaml"
SAMPLE_GOLD = REPO_ROOT / "eval" / "sample_cases.jsonl"
SAMPLE_PREDICTIONS = REPO_ROOT / "eval" / "sample_predictions.jsonl"


def _require_uv() -> str:
    uv = shutil.which("uv")
    if not uv:
        pytest.skip("uv not installed; release evaluation contract requires it")
    return uv


def _run_evaluation(
    gold_path: Path,
    predictions_path: Path,
    tmp_path: Path,
) -> subprocess.CompletedProcess[str]:
    output = tmp_path / "report.json"
    result = subprocess.run(
        [
            _require_uv(),
            "run",
            "--quiet",
            "--no-project",
            "--with",
            "pyyaml",
            "python",
            str(SCRIPT),
            "--gold",
            str(gold_path),
            "--predictions",
            str(predictions_path),
            "--rubric",
            str(RUBRIC),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def test_fails_on_empty_gold_set(tmp_path: Path) -> None:
    empty_gold = tmp_path / "empty.jsonl"
    empty_gold.write_text("", encoding="utf-8")
    empty_predictions = tmp_path / "empty_predictions.jsonl"
    empty_predictions.write_text("", encoding="utf-8")
    result = _run_evaluation(empty_gold, empty_predictions, tmp_path)
    assert result.returncode == 2, (
        f"empty gold set must fail with exit code 2, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["passed"] is False
    assert any(
        "empty" in failure.lower() or "no cases" in failure.lower()
        for failure in report.get("blocking_failures", [])
    ), f"report must explain why it failed: {report}"


def test_synthetic_samples_fail_until_live_blocking_metrics_supplied(tmp_path: Path) -> None:
    """The v1.0 synthetic samples exercise the gold/prediction scorer
    but cannot supply the live blocking metrics
    (schema_valid_rate, cross_tenant_access_failures,
    inaccessible_source_false_full_text_claims). The release gate
    must therefore refuse to pass on synthetic samples alone, so
    that no build can ship without the live pipeline supplying
    those numbers.

    This is the AGENTS.md invariant "never weaken evidence or
    security gates merely to make a demo pass" applied to the
    release pipeline.
    """
    if not SAMPLE_GOLD.exists() or not SAMPLE_PREDICTIONS.exists():
        pytest.skip("sample_cases.jsonl or sample_predictions.jsonl missing")
    result = _run_evaluation(SAMPLE_GOLD, SAMPLE_PREDICTIONS, tmp_path)
    assert result.returncode == 1, (
        f"synthetic samples must fail the release gate; got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["passed"] is False
    assert report["metrics"]["case_count"] == 4
    assert report["metrics"]["relation_accuracy"] == 1.0
    blocking = report["blocking_failures"]
    for metric in (
        "schema_valid_rate",
        "cross_tenant_access_failures",
        "inaccessible_source_false_full_text_claims",
    ):
        assert any(metric in failure for failure in blocking), (
            f"blocking failure for {metric} missing from report: {blocking}"
        )


def test_fails_when_fabricated_quote_detected(tmp_path: Path) -> None:
    if not SAMPLE_GOLD.exists():
        pytest.skip("sample_cases.jsonl missing")
    tampered_predictions = tmp_path / "tampered_predictions.jsonl"
    rewritten = []
    for line in SAMPLE_PREDICTIONS.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["case_id"] == "synthetic-direct-001":
            record = dict(record)
            record["fabricated_quote"] = True
        rewritten.append(json.dumps(record))
    tampered_predictions.write_text("\n".join(rewritten), encoding="utf-8")
    result = _run_evaluation(SAMPLE_GOLD, tampered_predictions, tmp_path)
    assert result.returncode == 1, (
        f"fabricated quote must trigger blocking failure, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["passed"] is False
    assert "fabricated_quote_count" in str(report.get("blocking_failures", []))
    assert report["metrics"]["fabricated_quote_count"] >= 1


def test_script_is_not_hardcoded(tmp_path: Path) -> None:
    """The source of `run_release_evaluation.py` must not be the
    34-line hard-coded `passed: True` stub that shipped in v1.0."""
    source = SCRIPT.read_text(encoding="utf-8")
    forbidden_markers = [
        '"fabricated_quote_count": 0,\n            "unsupported_statement_rate": 0.01',
        '"passed": True\n    }',
    ]
    for marker in forbidden_markers:
        assert marker not in source, (
            f"run_release_evaluation.py still contains the hard-coded "
            f"v1.0 stub fragment: {marker!r}"
        )
    assert "score_sample_predictions" in source, (
        "run_release_evaluation.py must delegate to score_sample_predictions.py"
    )
