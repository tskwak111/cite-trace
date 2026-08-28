#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


class EvaluationValidationFailure(RuntimeError):
    pass


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvaluationValidationFailure(
                f"invalid JSONL {path.relative_to(ROOT)}:{line_number}: {exc}"
            ) from exc
        if not isinstance(record, dict):
            raise EvaluationValidationFailure(
                f"record must be an object: {path.relative_to(ROOT)}:{line_number}"
            )
        records.append(record)
    return records


def _taxonomy_ids(filename: str) -> set[str]:
    path = ROOT / "contracts" / "taxonomies" / filename
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {item["id"] for item in data["values"]}


def _require_keys(record: dict[str, Any], keys: set[str], label: str) -> None:
    missing = sorted(keys - set(record))
    if missing:
        raise EvaluationValidationFailure(f"{label} missing keys: {missing}")


def validate_eval_assets() -> dict[str, int]:
    eval_dir = ROOT / "eval"
    required_paths = [
        eval_dir / "README.md",
        eval_dir / "rubric.yaml",
        eval_dir / "annotation_handbook.md",
        eval_dir / "goldset_template.csv",
        eval_dir / "sample_cases.jsonl",
        eval_dir / "sample_predictions.jsonl",
    ]
    missing_paths = [str(path.relative_to(ROOT)) for path in required_paths if not path.exists()]
    if missing_paths:
        raise EvaluationValidationFailure(f"missing evaluation assets: {missing_paths}")

    relation_ids = _taxonomy_ids("evidence_relations.v1.yaml")
    intent_ids = _taxonomy_ids("citation_intents.v1.yaml")
    transformation_ids = _taxonomy_ids("transformations.v1.yaml")
    access_levels = {
        "user_private_full_text",
        "open_access_full_text",
        "repository_manuscript",
        "publisher_open_full_text",
        "abstract_only",
        "metadata_only",
        "not_accessible",
    }
    allowed_splits = {"development", "calibration", "test", "challenge"}

    cases = _read_jsonl(eval_dir / "sample_cases.jsonl")
    predictions = _read_jsonl(eval_dir / "sample_predictions.jsonl")
    if not cases:
        raise EvaluationValidationFailure("sample_cases.jsonl must contain at least one case")

    case_by_id: dict[str, dict[str, Any]] = {}
    source_ids_by_case: dict[str, set[str]] = {}
    for index, case in enumerate(cases, 1):
        label = f"sample case #{index}"
        _require_keys(
            case,
            {"case_id", "split", "synthetic", "claim", "source_access_level", "source_spans", "gold"},
            label,
        )
        case_id = case["case_id"]
        if not isinstance(case_id, str) or not case_id.strip():
            raise EvaluationValidationFailure(f"{label} has invalid case_id")
        if case_id in case_by_id:
            raise EvaluationValidationFailure(f"duplicate case_id: {case_id}")
        case_by_id[case_id] = case
        if case["split"] not in allowed_splits:
            raise EvaluationValidationFailure(f"{case_id} has invalid split: {case['split']}")
        if case["synthetic"] is not True:
            raise EvaluationValidationFailure(
                f"bundled sample case {case_id} must be explicitly marked synthetic=true"
            )
        if case["source_access_level"] not in access_levels:
            raise EvaluationValidationFailure(
                f"{case_id} has invalid source_access_level: {case['source_access_level']}"
            )
        claim = case["claim"]
        if not isinstance(claim, dict) or not isinstance(claim.get("text"), str) or not claim["text"].strip():
            raise EvaluationValidationFailure(f"{case_id} must contain a non-empty claim.text")

        spans = case["source_spans"]
        if not isinstance(spans, list):
            raise EvaluationValidationFailure(f"{case_id} source_spans must be an array")
        source_ids: set[str] = set()
        for span in spans:
            if not isinstance(span, dict):
                raise EvaluationValidationFailure(f"{case_id} source span must be an object")
            _require_keys(span, {"id", "quote", "evidence_type"}, f"{case_id} source span")
            if span["id"] in source_ids:
                raise EvaluationValidationFailure(f"{case_id} has duplicate source span ID: {span['id']}")
            if not isinstance(span["quote"], str) or not span["quote"].strip():
                raise EvaluationValidationFailure(f"{case_id} source span quote must be non-empty")
            source_ids.add(span["id"])
        source_ids_by_case[case_id] = source_ids

        gold = case["gold"]
        if not isinstance(gold, dict):
            raise EvaluationValidationFailure(f"{case_id} gold must be an object")
        _require_keys(
            gold,
            {"relation", "citation_intents", "transformations", "abstention"},
            f"{case_id} gold",
        )
        if gold["relation"] not in relation_ids:
            raise EvaluationValidationFailure(f"{case_id} has unknown gold relation: {gold['relation']}")
        unknown_intents = set(gold["citation_intents"]) - intent_ids
        if unknown_intents:
            raise EvaluationValidationFailure(
                f"{case_id} has unknown gold citation intents: {sorted(unknown_intents)}"
            )
        unknown_transformations = set(gold["transformations"]) - transformation_ids
        if unknown_transformations:
            raise EvaluationValidationFailure(
                f"{case_id} has unknown gold transformations: {sorted(unknown_transformations)}"
            )
        inaccessible = gold["relation"] == "inaccessible_source"
        if inaccessible:
            if case["source_access_level"] != "not_accessible" or spans:
                raise EvaluationValidationFailure(
                    f"{case_id} inaccessible_source requires not_accessible and zero source spans"
                )
            abstention = gold["abstention"]
            if not isinstance(abstention, dict) or not abstention.get("code"):
                raise EvaluationValidationFailure(
                    f"{case_id} inaccessible_source requires an abstention code"
                )
        elif case["source_access_level"] == "not_accessible":
            raise EvaluationValidationFailure(
                f"{case_id} not_accessible must use inaccessible_source relation"
            )

    prediction_by_id: dict[str, dict[str, Any]] = {}
    for index, prediction in enumerate(predictions, 1):
        label = f"sample prediction #{index}"
        _require_keys(
            prediction,
            {"case_id", "relation", "source_span_ids", "citation_intents", "transformations", "material_statements"},
            label,
        )
        case_id = prediction["case_id"]
        if case_id in prediction_by_id:
            raise EvaluationValidationFailure(f"duplicate prediction case_id: {case_id}")
        prediction_by_id[case_id] = prediction
        if prediction["relation"] not in relation_ids:
            raise EvaluationValidationFailure(
                f"{case_id} has unknown predicted relation: {prediction['relation']}"
            )
        unknown_intents = set(prediction["citation_intents"]) - intent_ids
        if unknown_intents:
            raise EvaluationValidationFailure(
                f"{case_id} has unknown predicted citation intents: {sorted(unknown_intents)}"
            )
        unknown_transformations = set(prediction["transformations"]) - transformation_ids
        if unknown_transformations:
            raise EvaluationValidationFailure(
                f"{case_id} has unknown predicted transformations: {sorted(unknown_transformations)}"
            )
        unknown_source_ids = set(prediction["source_span_ids"]) - source_ids_by_case.get(case_id, set())
        if unknown_source_ids:
            raise EvaluationValidationFailure(
                f"{case_id} prediction references unknown source spans: {sorted(unknown_source_ids)}"
            )
        statements = prediction["material_statements"]
        if not isinstance(statements, list) or not statements:
            raise EvaluationValidationFailure(
                f"{case_id} must contain at least one material statement"
            )
        for statement in statements:
            if not isinstance(statement, dict):
                raise EvaluationValidationFailure(f"{case_id} material statement must be an object")
            _require_keys(
                statement,
                {"text", "supporting_source_span_ids"},
                f"{case_id} material statement",
            )
            if not isinstance(statement["text"], str) or not statement["text"].strip():
                raise EvaluationValidationFailure(f"{case_id} material statement text must be non-empty")
            unknown_statement_ids = (
                set(statement["supporting_source_span_ids"]) - source_ids_by_case.get(case_id, set())
            )
            if unknown_statement_ids:
                raise EvaluationValidationFailure(
                    f"{case_id} statement references unknown source spans: {sorted(unknown_statement_ids)}"
                )

    case_ids = set(case_by_id)
    prediction_ids = set(prediction_by_id)
    if case_ids != prediction_ids:
        raise EvaluationValidationFailure(
            "sample case/prediction ID mismatch: "
            f"missing={sorted(case_ids - prediction_ids)}, extra={sorted(prediction_ids - case_ids)}"
        )

    expected_headers = [
        "case_id", "split", "domain", "citing_asset_id", "citing_work_version_id",
        "citation_cluster_id", "citation_anchor_id", "reference_entry_id", "claim_text",
        "claim_start_offset", "claim_end_offset", "claim_qualifiers_json", "gold_work_id",
        "gold_work_version_id", "resolution_status", "source_access_level",
        "gold_source_span_ids_json", "gold_evidence_relation", "gold_scope_observations_json",
        "gold_citation_intents_json", "gold_transformations_json", "expected_abstention_code",
        "annotation_status", "annotator_a", "annotator_b", "adjudicator", "notes",
    ]
    with (eval_dir / "goldset_template.csv").open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        actual_headers = next(reader, [])
    if actual_headers != expected_headers:
        raise EvaluationValidationFailure("goldset_template.csv headers drift from the canonical layout")

    rubric = yaml.safe_load((eval_dir / "rubric.yaml").read_text(encoding="utf-8"))
    blocking = rubric.get("release_policy", {}).get("blocking_metrics", {})
    required_blockers = {
        "fabricated_quote_count",
        "schema_valid_rate",
        "cross_tenant_access_failures",
        "inaccessible_source_false_full_text_claims",
        "unsupported_material_statement_rate",
    }
    missing_blockers = sorted(required_blockers - set(blocking))
    if missing_blockers:
        raise EvaluationValidationFailure(f"rubric missing blocking metrics: {missing_blockers}")

    return {
        "case_count": len(cases),
        "prediction_count": len(predictions),
        "taxonomy_relations": len(relation_ids),
        "taxonomy_intents": len(intent_ids),
        "taxonomy_transformations": len(transformation_ids),
    }


def main() -> int:
    result = validate_eval_assets()
    summary = ", ".join(f"{key}={value}" for key, value in result.items())
    print(f"PASS evaluation assets ({summary})")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EvaluationValidationFailure as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
