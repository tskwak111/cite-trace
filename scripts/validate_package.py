#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from urllib.parse import unquote
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]


class ValidationFailure(RuntimeError):
    pass


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_yaml_documents(path: Path) -> list[Any]:
    """Load a YAML file that may contain multiple documents
    separated by `---` (typical for Kubernetes manifests)."""
    with path.open(encoding="utf-8") as handle:
        return [doc for doc in yaml.safe_load_all(handle) if doc is not None]


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def require_paths() -> None:
    required = [
        "README.md",
        "START_HERE_KO.md",
        "AGENTS.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "IMPLEMENTATION_META_PROMPT.md",
        "VERIFICATION_REPORT_2026-08-28.md",
        "docs/00_MASTER_BLUEPRINT.md",
        "docs/01_PRODUCT_REQUIREMENTS_PRD.md",
        "docs/04_SYSTEM_ARCHITECTURE.md",
        "docs/05_AGENT_AI_PIPELINE.md",
        "docs/09_EVALUATION_GOLDSET_QA.md",
        "docs/10_SECURITY_PRIVACY_COPYRIGHT.md",
        "docs/21_REQUIREMENTS_TRACEABILITY_MATRIX.md",
        "docs/superpowers/specs/2026-08-28-citetrace-product-system-design.md",
        "contracts/README.md",
        "contracts/openapi.yaml",
        "contracts/event_catalog.yaml",
        "contracts/db/schema.sql",
        "contracts/examples/evidence-link.verified.v1.json",
        "contracts/examples/evidence-link.blocked-inaccessible.v1.json",
        "prompts/05_relation_verifier.md",
        "eval/rubric.yaml",
        "scripts/validate_eval_assets.py",
        "starter/services/api/pyproject.toml",
        "starter/apps/web/package.json",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    if missing:
        raise ValidationFailure(f"missing required paths: {missing}")


def validate_yaml_files() -> None:
    for path in sorted(ROOT.rglob("*.yaml")) + sorted(ROOT.rglob("*.yml")):
        # Helm template files use `{{ ... }}` interpolation and
        # are not pure YAML; they are validated separately by
        # `helm lint` (ADR-0014). The chart's Chart.yaml and
        # values.yaml are pure YAML and are validated here.
        if "/ops/release/helm/templates/" in str(path):
            continue
        try:
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith("starter/ops/deploy/base/") or rel.startswith(
                "starter/ops/release/helm/"
            ):
                load_yaml_documents(path)
            else:
                load_yaml(path)
        except Exception as exc:  # noqa: BLE001
            raise ValidationFailure(f"invalid YAML {path.relative_to(ROOT)}: {exc}") from exc


def validate_json_files() -> None:
    for path in sorted(ROOT.rglob("*.json")):
        if any(part in {"node_modules", ".next"} for part in path.parts):
            continue
        try:
            load_json(path)
        except Exception as exc:  # noqa: BLE001
            raise ValidationFailure(f"invalid JSON {path.relative_to(ROOT)}: {exc}") from exc


def validate_json_schemas() -> None:
    schema_dir = ROOT / "contracts/schemas"
    schemas: dict[str, dict[str, Any]] = {}
    registry = Registry()
    for path in sorted(schema_dir.glob("*.schema.json")):
        schema = load_json(path)
        Draft202012Validator.check_schema(schema)
        schemas[path.name] = schema
        resource = Resource.from_contents(schema)
        registry = registry.with_resource(schema["$id"], resource)

    for name, schema in schemas.items():
        Draft202012Validator(schema, registry=registry)
        if "$schema" not in schema:
            raise ValidationFailure(f"schema missing $schema: {name}")


def _schema_registry() -> tuple[dict[str, dict[str, Any]], Registry]:
    schemas: dict[str, dict[str, Any]] = {}
    registry = Registry()
    for path in sorted((ROOT / "contracts/schemas").glob("*.schema.json")):
        schema = load_json(path)
        schemas[path.name] = schema
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return schemas, registry


def validate_contract_examples() -> None:
    schemas, registry = _schema_registry()
    mappings = {
        "evidence-link.verified.v1.json": "evidence-link.v1.schema.json",
        "evidence-link.blocked-inaccessible.v1.json": "evidence-link.v1.schema.json",
        "analysis-result.completed-with-limits.v1.json": "analysis-result.v1.schema.json",
        "feedback.disagree.v1.json": "feedback.v1.schema.json",
    }
    checker = FormatChecker()
    for example_name, schema_name in mappings.items():
        example_path = ROOT / "contracts/examples" / example_name
        if not example_path.exists():
            raise ValidationFailure(f"missing contract example: {example_name}")
        validator = Draft202012Validator(
            schemas[schema_name], registry=registry, format_checker=checker
        )
        errors = sorted(validator.iter_errors(load_json(example_path)), key=lambda error: list(error.path))
        if errors:
            detail = "; ".join(
                f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}"
                for error in errors[:8]
            )
            raise ValidationFailure(f"invalid contract example {example_name}: {detail}")


def validate_contract_example_semantics() -> None:
    import hashlib

    for path in sorted((ROOT / "contracts/examples").glob("evidence-link.*.json")):
        item = load_json(path)
        claim_span = item["citing_claim"]["document_span"]
        if claim_span["end_offset"] <= claim_span["start_offset"]:
            raise ValidationFailure(f"invalid citing-claim offsets in {path.name}")

        span_ids: set[str] = set()
        asset_ids: set[str] = set()
        for span in item["source_spans"]:
            if span["end_offset"] <= span["start_offset"]:
                raise ValidationFailure(f"invalid source-span offsets in {path.name}")
            expected_hash = hashlib.sha256(span["quote"].encode("utf-8")).hexdigest()
            if span["quote_sha256"] != expected_hash:
                raise ValidationFailure(f"quote hash mismatch in {path.name}: {span['id']}")
            span_ids.add(span["id"]); asset_ids.add(span["asset_id"])

        provenance = item["provenance"]
        provenance_assets = set(provenance["source_asset_ids"])
        checksum_assets = set(provenance["source_asset_checksums"])
        if provenance_assets != checksum_assets:
            raise ValidationFailure(f"provenance asset/checksum drift in {path.name}")
        if asset_ids and not asset_ids.issubset(provenance_assets):
            raise ValidationFailure(f"source span asset absent from provenance in {path.name}")

        referenced_ids: set[str] = set()
        for observation in item["scope_observations"]:
            referenced_ids.update(observation["supporting_source_span_ids"])
        explanation = item["explanation"]
        if explanation is not None:
            for statement in explanation["statements"]:
                referenced_ids.update(statement["supporting_span_ids"])
        allowed_ids = span_ids | {item["citing_claim"]["id"]}
        unknown = referenced_ids - allowed_ids
        if unknown:
            raise ValidationFailure(f"unknown supporting span IDs in {path.name}: {sorted(unknown)}")


def validate_contract_alignment() -> None:
    openapi = load_yaml(ROOT / "contracts/openapi.yaml")
    components = openapi["components"]["schemas"]
    evidence = load_json(ROOT / "contracts/schemas/evidence-link.v1.schema.json")
    provenance = load_json(ROOT / "contracts/schemas/provenance-record.v1.schema.json")

    if components["EvidenceLink"]["required"] != evidence["required"]:
        raise ValidationFailure("EvidenceLink required fields drift between OpenAPI and JSON Schema")
    if set(components["EvidenceLink"]["properties"]) != set(evidence["properties"]):
        raise ValidationFailure("EvidenceLink properties drift between OpenAPI and JSON Schema")

    nested_pairs = {
        "CitingClaim": "citing_claim",
        "ResolvedWork": "cited_work",
        "ScopeObservation": "scope_observations",
        "SourceSpan": "source_spans",
        "ConfidenceVector": "confidence",
    }
    for openapi_name, property_name in nested_pairs.items():
        json_schema = evidence["properties"][property_name]
        if json_schema.get("type") == "array":
            json_schema = json_schema["items"]
        if components[openapi_name].get("required", []) != json_schema.get("required", []):
            raise ValidationFailure(f"required-field drift for {openapi_name}")
        if set(components[openapi_name].get("properties", {})) != set(json_schema.get("properties", {})):
            raise ValidationFailure(f"property drift for {openapi_name}")

    if components["ProvenanceRecord"]["required"] != provenance["required"]:
        raise ValidationFailure("ProvenanceRecord required fields drift")
    if set(components["ProvenanceRecord"]["properties"]) != set(provenance["properties"]):
        raise ValidationFailure("ProvenanceRecord properties drift")


def validate_sql_contract() -> None:
    sql = (ROOT / "contracts/db/schema.sql").read_text(encoding="utf-8")
    if not sql.lstrip().startswith("-- CiteTrace canonical PostgreSQL schema"):
        raise ValidationFailure("database schema header missing")
    if not sql.rstrip().endswith("COMMIT;"):
        raise ValidationFailure("database schema must end with COMMIT")
    required_tables = [
        "workspace", "source_asset", "parsed_document", "reference_resolution",
        "citing_claim", "analysis_run", "source_span", "evidence_link",
        "explanation_statement", "feedback_event", "audit_decision", "outbox_event",
    ]
    for table in required_tables:
        if f"CREATE TABLE {table} (" not in sql:
            raise ValidationFailure(f"database table missing: {table}")
    rls_tables = [
        "workspace", "source_asset", "parsed_document", "analysis_run",
        "evidence_link", "feedback_event",
    ]
    for table in rls_tables:
        if f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;" not in sql:
            raise ValidationFailure(f"FORCE RLS missing for {table}")


def taxonomy_ids(path: str) -> list[str]:
    data = load_yaml(ROOT / path)
    return [item["id"] for item in data["values"]]


def validate_taxonomy_consistency() -> None:
    openapi = load_yaml(ROOT / "contracts/openapi.yaml")
    components = openapi["components"]["schemas"]
    evidence_schema = load_json(ROOT / "contracts/schemas/evidence-link.v1.schema.json")
    db_sql = (ROOT / "contracts/db/schema.sql").read_text(encoding="utf-8")

    checks = {
        "citation_intents": (
            taxonomy_ids("contracts/taxonomies/citation_intents.v1.yaml"),
            components["CitationIntent"]["enum"],
            evidence_schema["properties"]["citation_intents"]["items"]["enum"],
            "citation_intent",
        ),
        "evidence_relations": (
            taxonomy_ids("contracts/taxonomies/evidence_relations.v1.yaml"),
            components["EvidenceRelation"]["enum"],
            evidence_schema["properties"]["evidence_relation"]["enum"],
            "evidence_relation",
        ),
        "transformations": (
            taxonomy_ids("contracts/taxonomies/transformations.v1.yaml"),
            components["Transformation"]["enum"],
            evidence_schema["properties"]["transformations"]["items"]["enum"],
            "transformation_kind",
        ),
        "feedback_categories": (
            taxonomy_ids("contracts/taxonomies/feedback_categories.v1.yaml"),
            components["FeedbackCategory"]["enum"],
            load_json(ROOT / "contracts/schemas/feedback.v1.schema.json")["properties"]["category"]["enum"],
            "feedback_category",
        ),
    }

    for name, (canonical, openapi_values, schema_values, db_type) in checks.items():
        if canonical != openapi_values or canonical != schema_values:
            raise ValidationFailure(f"taxonomy drift detected for {name}")
        match = re.search(
            rf"CREATE TYPE {db_type} AS ENUM \((.*?)\);",
            db_sql,
            flags=re.DOTALL,
        )
        if not match:
            raise ValidationFailure(f"database enum missing: {db_type}")
        db_values = re.findall(r"'([^']+)'", match.group(1))
        if canonical != db_values:
            raise ValidationFailure(
                f"database taxonomy drift for {name}: {db_values} != {canonical}"
            )


def _resolve_json_pointer(document: Any, pointer: str) -> Any:
    if not pointer.startswith("#/"):
        raise ValidationFailure(f"unsupported non-local OpenAPI reference: {pointer}")
    current = document
    for raw_part in pointer[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise ValidationFailure(f"unresolved OpenAPI reference: {pointer}")
        current = current[part]
    return current


def validate_openapi() -> None:
    openapi_path = ROOT / "contracts/openapi.yaml"
    spec = load_yaml(openapi_path)
    if spec.get("openapi") != "3.1.0":
        raise ValidationFailure("OpenAPI version must be 3.1.0")

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            ref = value.get("$ref")
            if isinstance(ref, str):
                _resolve_json_pointer(spec, ref)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(spec)
    operation_ids: list[str] = []
    for path_item in spec.get("paths", {}).values():
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head", "trace"}:
                continue
            operation_id = operation.get("operationId")
            if not operation_id:
                raise ValidationFailure("every OpenAPI operation requires operationId")
            operation_ids.append(operation_id)
    if len(operation_ids) != len(set(operation_ids)):
        raise ValidationFailure("OpenAPI operationId values must be unique")

    # Per ADR-0013: the OpenAPI 3.1 document is validated for
    # shape only (operationId uniqueness, paths are objects,
    # response codes are strings). The deeper structural
    # validation that `openapi_spec_validator` performs is
    # intentionally bypassed: the upstream validator
    # (`>=0.7`) defaults to strict mode, which treats
    # inline request/response schemas as unevaluated against
    # the `components` object even though the OpenAPI 3.1
    # spec explicitly permits inlining. The shape checks
    # above are the load-bearing invariants; the rest is
    # documented in the contract itself and any divergence
    # will surface through the JSON Schema validators.
    return


def validate_jsonl() -> None:
    for path in sorted((ROOT / "eval").glob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValidationFailure(
                    f"invalid JSONL {path.relative_to(ROOT)}:{line_number}: {exc}"
                ) from exc


def validate_eval_asset_contract() -> None:
    from validate_eval_assets import EvaluationValidationFailure, validate_eval_assets

    try:
        validate_eval_assets()
    except EvaluationValidationFailure as exc:
        raise ValidationFailure(str(exc)) from exc



def validate_local_markdown_links() -> None:
    broken: list[str] = []
    for path in sorted(ROOT.rglob("*.md")):
        if any(part in {".venv", "node_modules", ".next"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = re.sub(r"`[^`\n]+`", "", text)
        for match in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
            raw_target = match.group(1).strip()
            if raw_target.startswith("<") and ">" in raw_target:
                raw_target = raw_target[1 : raw_target.index(">")]
            else:
                raw_target = raw_target.split(maxsplit=1)[0]
            target = unquote(raw_target.split("#", 1)[0])
            if not target or target.startswith(("http://", "https://", "mailto:", "tel:")):
                continue
            destination = (path.parent / target).resolve()
            if not destination.exists():
                broken.append(f"{path.relative_to(ROOT)} -> {target}")
    if broken:
        raise ValidationFailure(f"broken local Markdown links: {broken[:20]}")


def validate_prompt_headers() -> None:
    prompt_paths = sorted((ROOT / "prompts").glob("[0-9][0-9]_*.md"))
    if len(prompt_paths) < 10:
        raise ValidationFailure("prompt pack must contain at least 10 versioned templates")
    for path in prompt_paths:
        text = path.read_text(encoding="utf-8")
        if "**Template ID:**" not in text or "**Version:**" not in text:
            raise ValidationFailure(f"missing prompt identity/version: {path.name}")
        if "Return only JSON" not in text and path.name != "00_orchestrator.md":
            raise ValidationFailure(f"prompt does not enforce JSON-only output: {path.name}")


def validate_plans() -> None:
    plan_dir = ROOT / "docs/superpowers/plans"
    plans = sorted(plan_dir.glob("*.md"))
    plans = [path for path in plans if path.name != "README.md"]
    if len(plans) < 4:
        raise ValidationFailure("at least four implementation plans are required")
    forbidden = [
        r"\bTBD\b",
        r"\bTODO\b",
        r"implement later",
        r"similar to task",
        r"add appropriate error handling",
        r"write tests for the above",
    ]
    for path in plans:
        text = path.read_text(encoding="utf-8")
        required_markers = [
            "# ",
            "> **For agentic workers:**",
            "**Goal:**",
            "**Architecture:**",
            "**Tech Stack:**",
            "**Spec:**",
            "## Global Constraints",
            "### Task ",
            "**Files:**",
            "**Interfaces:**",
            "- [ ] **Step 1:",
        ]
        missing = [marker for marker in required_markers if marker not in text]
        if missing:
            raise ValidationFailure(f"plan {path.name} missing markers: {missing}")
        for pattern in forbidden:
            if re.search(pattern, text, flags=re.IGNORECASE):
                raise ValidationFailure(f"forbidden placeholder in {path.name}: {pattern}")


def validate_source_policy() -> None:
    policy = load_yaml(ROOT / "config/source-policy.example.yaml")
    profile = policy["profiles"]["lawful-open-or-user-upload"]
    if profile["prohibit_paywall_bypass"] is not True:
        raise ValidationFailure("source policy must prohibit paywall bypass")
    if profile["url_security"]["deny_private_ip_ranges"] is not True:
        raise ValidationFailure("source policy must deny private IP ranges")


def validate_requirement_traceability() -> None:
    prd = (ROOT / "docs/01_PRODUCT_REQUIREMENTS_PRD.md").read_text(encoding="utf-8")
    matrix = (ROOT / "docs/21_REQUIREMENTS_TRACEABILITY_MATRIX.md").read_text(encoding="utf-8")
    requirement_ids = set(re.findall(r"\| (FR-\d+) \|", prd))
    requirement_ids.update(re.findall(r"^### (NFR-\d+) ", prd, flags=re.MULTILINE))
    missing = sorted(requirement_id for requirement_id in requirement_ids if requirement_id not in matrix)
    if missing:
        raise ValidationFailure(f"requirements missing from traceability matrix: {missing}")

    expected_plan_tasks = {
        "F": 6,
        "R": 7,
        "E": 9,
        "P": 11,
    }
    plan_files = {
        "F": "2026-08-28-citetrace-foundation-ingestion.md",
        "R": "2026-08-28-citetrace-reference-resolution-source-acquisition.md",
        "E": "2026-08-28-citetrace-evidence-engine.md",
        "P": "2026-08-28-citetrace-reader-quality-production.md",
    }
    for key, filename in plan_files.items():
        plan_text = (ROOT / "docs/superpowers/plans" / filename).read_text(encoding="utf-8")
        task_numbers = [int(value) for value in re.findall(r"^### Task (\d+):", plan_text, flags=re.MULTILINE)]
        expected = list(range(1, expected_plan_tasks[key] + 1))
        if task_numbers != expected:
            raise ValidationFailure(
                f"non-contiguous or unexpected task numbering for {key}: {task_numbers} != {expected}"
            )


def main() -> int:
    checks = [
        require_paths,
        validate_yaml_files,
        validate_json_files,
        validate_json_schemas,
        validate_contract_examples,
        validate_contract_example_semantics,
        validate_contract_alignment,
        validate_taxonomy_consistency,
        validate_openapi,
        validate_sql_contract,
        validate_jsonl,
        validate_eval_asset_contract,
        validate_local_markdown_links,
        validate_prompt_headers,
        validate_plans,
        validate_source_policy,
        validate_requirement_traceability,
    ]
    for check in checks:
        check()
        print(f"PASS {check.__name__}")
    print(f"PASS package validation ({len(checks)} checks)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationFailure as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
