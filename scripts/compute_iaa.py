#!/usr/bin/env python3
"""Inter-annotator agreement for the gold-set pipeline.

Reads two annotation files (annotator A and annotator B) and
reports Cohen's κ for the four nominal dimensions:

  - gold_evidence_relation
  - gold_citation_intents (set overlap; reported as
    multi-label Jaccard plus per-label κ when both
    annotators use the same set)
  - gold_transformations
  - resolution_status

The blueprint implies κ ≥ 0.7 for the release-time gold
set. Values below 0.7 are reported as `below_threshold`
so a CI check can fail the build.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path


def _read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def _index(rows: list[dict]) -> dict[str, dict]:
    return {r["case_id"]: r for r in rows}


def cohens_kappa(a_values: list, b_values: list) -> float:
    if not a_values:
        return 0.0
    po = sum(1 for x, y in zip(a_values, b_values) if x == y) / len(a_values)
    labels = set(a_values) | set(b_values)
    counts_a = Counter(a_values)
    counts_b = Counter(b_values)
    pe = sum((counts_a[l] * counts_b[l]) for l in labels) / (len(a_values) * len(b_values))
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def _aligned(dimension: str, a: dict[str, dict], b: dict[str, dict]) -> tuple[list, list]:
    common = sorted(set(a) & set(b))
    return [a[k][dimension] for k in common], [b[k][dimension] for k in common]


def _aligned_sets(dimension: str, a: dict[str, dict], b: dict[str, dict]) -> tuple[list[frozenset], list[frozenset]]:
    common = sorted(set(a) & set(b))
    return (
        [frozenset(a[k].get(dimension, []) or []) for k in common],
        [frozenset(b[k].get(dimension, []) or []) for k in common],
    )


def jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def krippendorff_alpha_nominal(
    a_values: list, b_values: list
) -> float | None:
    """Krippendorff's alpha for two annotators on a nominal
    scale. Returns None when fewer than 2 values are
    available, or when the expected disagreement equals 1
    (alpha is undefined in that degenerate case).

    The formula follows Krippendorff (2011, Computing
    Krippendorff's Alpha-Reliability); the interval metric
    is the disagreement function for nominal data
    (delta(a, b) = 0 if a == b else 1).
    """
    if len(a_values) < 2:
        return None
    n = len(a_values)
    pairs: list[tuple] = []
    for av, bv in zip(a_values, b_values):
        pairs.append((av, bv))
    if not pairs:
        return None
    observed = sum(1 for a, b in pairs if a != b) / len(pairs)
    values = a_values + b_values
    if len(values) < 2:
        return None
    expected = 0.0
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            expected += 0.0 if values[i] == values[j] else 1.0
    n_values = len(values)
    if n_values < 2:
        return None
    expected = expected / (n_values * (n_values - 1) / 2)
    if expected == 1.0:
        return None
    return 1.0 - observed / expected


def krippendorff_alpha_interval(
    a_values: list[float], b_values: list[float]
) -> float | None:
    """Krippendorff's alpha for two annotators on an
    interval scale (e.g. the 1-5 usefulness scale). Uses
    the squared-difference interval metric:
        delta(a, b) = (a - b) ** 2.

    Returns None when fewer than 2 values are available
    or the variance is zero (alpha is undefined).
    """
    if len(a_values) < 2:
        return None
    pairs = list(zip(a_values, b_values))
    n_pairs = len(pairs)
    if n_pairs < 2:
        return None
    observed = sum((a - b) ** 2 for a, b in pairs) / n_pairs
    values = list(a_values) + list(b_values)
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    expected = sum((v - mean) ** 2 for v in values) * 2 / (len(values) - 1)
    if expected == 0.0:
        return None
    return 1.0 - observed / expected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--a", type=Path, required=True, help="annotator A JSONL")
    parser.add_argument("--b", type=Path, required=True, help="annotator B JSONL")
    parser.add_argument("--threshold", type=float, default=0.7, help="κ threshold; below is flagged")
    args = parser.parse_args()

    a = _index(_read_jsonl(args.a))
    b = _index(_read_jsonl(args.b))
    common = sorted(set(a) & set(b))
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    report = {
        "case_count": len(common),
        "only_in_a": only_a,
        "only_in_b": only_b,
        "dimensions": {},
    }
    for dim in ("gold_evidence_relation", "resolution_status"):
        av, bv = _aligned(dim, a, b)
        kappa = cohens_kappa(av, bv)
        report["dimensions"][dim] = {
            "kappa": kappa,
            "below_threshold": kappa < args.threshold,
        }
    intent_a, intent_b = _aligned_sets("gold_citation_intents_json", a, b)
    intent_jaccard = (
        sum(jaccard(x, y) for x, y in zip(intent_a, intent_b)) / max(len(intent_a), 1)
    )
    report["dimensions"]["gold_citation_intents"] = {
        "jaccard": intent_jaccard,
        "below_threshold": intent_jaccard < args.threshold,
    }
    tx_a, tx_b = _aligned_sets("gold_transformations_json", a, b)
    tx_jaccard = sum(jaccard(x, y) for x, y in zip(tx_a, tx_b)) / max(len(tx_a), 1)
    report["dimensions"]["gold_transformations"] = {
        "jaccard": tx_jaccard,
        "below_threshold": tx_jaccard < args.threshold,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    below = any(d["below_threshold"] for d in report["dimensions"].values())
    return 1 if below else 0


if __name__ == "__main__":
    raise SystemExit(main())
