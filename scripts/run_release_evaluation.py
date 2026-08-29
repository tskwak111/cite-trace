#!/usr/bin/env python3
"""Run the release-time evidence-quality evaluation.

This script is the single entry point that a release pipeline should
invoke to decide whether a candidate build can ship. It must never
hard-code its verdict; every metric is computed from the gold set
and the predictions file.

Exit codes:
  0 — all blocking metrics pass and all quality targets are met
  1 — at least one blocking metric failed
  2 — the gold set is empty (cannot evaluate)

The output JSON is written to the path given by --output and is the
authoritative record that the release pipeline should archive with
the build artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "PyYAML is required to read eval/rubric.yaml. "
        "Install it with: uv pip install pyyaml\n"
    )
    raise

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from score_sample_predictions import read_jsonl, score  # noqa: E402

PIPELINE_VERSION = "v1.0"
DATASET_VERSION = "v1.0"

OPERATORS = {
    "eq": lambda actual, threshold: actual == threshold,
    "gte": lambda actual, threshold: actual >= threshold,
    "lte": lambda actual, threshold: actual <= threshold,
}


def _load_rubric(rubric_path: Path) -> dict[str, Any]:
    return yaml.safe_load(rubric_path.read_text(encoding="utf-8"))


def _blocking_failures(metrics: dict[str, Any], rubric: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for name, spec in rubric.get("release_policy", {}).get("blocking_metrics", {}).items():
        op = OPERATORS.get(spec["operator"])
        if op is None:
            failures.append(f"unknown operator {spec['operator']} for blocking metric {name}")
            continue
        value = metrics.get(name)
        if value is None:
            failures.append(
                f"blocking metric {name} was not measured; "
                f"live pipeline must supply it before release"
            )
            continue
        if not op(value, spec["threshold"]):
            failures.append(
                f"blocking metric {name}={value} failed "
                f"{spec['operator']} {spec['threshold']}"
            )
    return failures


def _quality_target_failures(
    metrics: dict[str, Any],
    rubric: dict[str, Any],
    synthetic_only: bool,
) -> list[str]:
    failures: list[str] = []
    for name, spec in rubric.get("release_policy", {}).get("quality_targets", {}).items():
        op = OPERATORS.get(spec["operator"])
        if op is None:
            failures.append(f"unknown operator {spec['operator']} for quality target {name}")
            continue
        value = metrics.get(name)
        if value is None:
            if synthetic_only:
                continue
            failures.append(f"quality target {name} was not measured")
            continue
        if not op(value, spec["threshold"]):
            failures.append(
                f"quality target {name}={value} failed "
                f"{spec['operator']} {spec['threshold']}"
            )
    return failures


def _synthesize_blocking_metrics(
    predictions: dict[str, dict[str, Any]],
) -> dict[str, int | float | None]:
    """Compute the blocking-metric values the synthetic samples
    can measure directly. The remaining blocking metrics
    (cross-tenant access, schema validity, inaccessible_source
    false claims) require the live pipeline; the script reports
    `None` for them and `_blocking_failures` treats `None` as
    "not measured by the synthetic contract", not as zero.

    A real release build that lacks any of those measurements
    should not ship; that is enforced at the pipeline boundary
    in Slice 6, not by hard-coding zero here.
    """
    fabricated = sum(1 for r in predictions.values() if r.get("fabricated_quote"))
    return {
        "fabricated_quote_count": fabricated,
        "schema_valid_rate": None,
        "cross_tenant_access_failures": None,
        "inaccessible_source_false_full_text_claims": None,
    }


def evaluate(
    gold_path: Path,
    predictions_path: Path,
    rubric_path: Path,
    *,
    live_metrics_path: Path | None = None,
) -> dict[str, Any]:
    rubric = _load_rubric(rubric_path)
    gold = read_jsonl(gold_path)
    predictions = read_jsonl(predictions_path)

    if not gold:
        return {
            "dataset_version": DATASET_VERSION,
            "pipeline_version": PIPELINE_VERSION,
            "metrics": {
                "case_count": 0,
                "fabricated_quote_count": None,
                "schema_valid_rate": None,
                "cross_tenant_access_failures": None,
                "inaccessible_source_false_full_text_claims": None,
            },
            "blocking_failures": [
                "gold set is empty (no cases to evaluate); cannot release"
            ],
            "quality_target_failures": [],
            "passed": False,
        }
    # if gold is non-empty we already detected synthetic_only above;
    # an empty gold is always failing (not just "synthetic").

    metrics = score(gold, predictions)
    metrics.update(_synthesize_blocking_metrics(predictions))
    if live_metrics_path is not None:
        live = json.loads(live_metrics_path.read_text(encoding="utf-8"))
        for name in ("schema_valid_rate", "cross_tenant_access_failures", "inaccessible_source_false_full_text_claims"):
            if name in live and live[name] is not None:
                metrics[name] = live[name]

    synthetic_only = all(
        record.get("synthetic", False) for record in gold.values()
    )

    blocking = _blocking_failures(metrics, rubric)
    quality = _quality_target_failures(metrics, rubric, synthetic_only)

    return {
        "dataset_version": DATASET_VERSION,
        "pipeline_version": PIPELINE_VERSION,
        "metrics": metrics,
        "blocking_failures": blocking,
        "quality_target_failures": quality,
        "passed": not blocking,
        "note": metrics.get("note", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--rubric", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--live-metrics",
        type=Path,
        default=None,
        help="Optional JSON produced by collect_live_blocking_metrics.py; "
        "the three blocking metrics it supplies override the synthetic "
        "fallback when the live values are non-null.",
    )
    args = parser.parse_args()

    report = evaluate(
        args.gold,
        args.predictions,
        args.rubric,
        live_metrics_path=args.live_metrics,
    )
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not report["passed"]:
        if report["metrics"].get("case_count", 0) == 0:
            print(
                f"Evaluation cannot run: {report['blocking_failures'][0]}",
                file=sys.stderr,
            )
            return 2
        print(
            f"Evaluation failed: {len(report['blocking_failures'])} blocking, "
            f"{len(report['quality_target_failures'])} quality target failure(s). "
            f"See {args.output}.",
            file=sys.stderr,
        )
        return 1
    print(f"Evaluation passed. Results written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
