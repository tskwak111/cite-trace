#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        records[record["case_id"]] = record
    return records


def set_f1(gold: set[str], predicted: set[str]) -> float:
    if not gold and not predicted:
        return 1.0
    if not gold or not predicted:
        return 0.0
    true_positive = len(gold & predicted)
    precision = true_positive / len(predicted)
    recall = true_positive / len(gold)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def score(gold: dict[str, dict[str, Any]], predictions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    missing = sorted(set(gold) - set(predictions))
    extra = sorted(set(predictions) - set(gold))
    relation_hits = 0
    intent_scores: list[float] = []
    transformation_scores: list[float] = []
    unsupported_material_statements = 0
    material_statements = 0

    for case_id, gold_case in gold.items():
        prediction = predictions.get(case_id)
        if prediction is None:
            intent_scores.append(0.0)
            transformation_scores.append(0.0)
            continue
        gold_labels = gold_case["gold"]
        relation_hits += prediction.get("relation") == gold_labels["relation"]
        intent_scores.append(
            set_f1(set(gold_labels["citation_intents"]), set(prediction.get("citation_intents", [])))
        )
        transformation_scores.append(
            set_f1(set(gold_labels["transformations"]), set(prediction.get("transformations", [])))
        )
        inaccessible = gold_labels["relation"] == "inaccessible_source"
        for statement in prediction.get("material_statements", []):
            material_statements += 1
            if not statement.get("supporting_source_span_ids") and not inaccessible:
                unsupported_material_statements += 1

    count = len(gold)
    return {
        "case_count": count,
        "missing_case_ids": missing,
        "extra_case_ids": extra,
        "relation_accuracy": relation_hits / count if count else 0.0,
        "citation_intent_set_f1": sum(intent_scores) / count if count else 0.0,
        "transformation_set_f1": sum(transformation_scores) / count if count else 0.0,
        "unsupported_material_statement_rate": (
            unsupported_material_statements / material_statements if material_statements else 0.0
        ),
        "note": "Synthetic contract samples; do not report as scientific model performance.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    args = parser.parse_args()
    metrics = score(read_jsonl(args.gold), read_jsonl(args.predictions))
    print(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
