"""Contract tests for the Streamlit annotator UI (Slice 18,
ADR-0016).

The UI is a Streamlit application that reads and writes
JSONL files that conform to `goldset-annotation.v1.schema.json`.
The contract test exercises the validation and IAA helper
functions without launching the Streamlit server. The
end-to-end UI smoke is left to a manual run; the offline
contract is the load-bearing assertion.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPT = REPO_ROOT / "scripts" / "annotate_ui.py"
SCHEMA = REPO_ROOT / "contracts" / "schemas" / "goldset-annotation.v1.schema.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("annotate_ui", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_module_is_importable() -> None:
    """The Streamlit script must be importable without
    launching the server. This is the offline contract;
    the on-screen UI is exercised by a human."""
    spec = importlib.util.spec_from_file_location("annotate_ui", SCRIPT)
    assert spec is not None
    assert spec.loader is not None


def test_schema_loads() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)


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
        "claim_text": "Method A improved accuracy from 70% to 78%.",
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


def test_validate_row_accepts_valid_record() -> None:
    module = _load_module()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = module.validate_row(_starter_row("good-case"), schema)
    assert errors == [], f"valid row produced errors: {errors}"


def test_validate_row_rejects_invalid_relation() -> None:
    module = _load_module()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    row = _starter_row("bad-case")
    row["gold_evidence_relation"] = "not-a-real-relation"
    errors = module.validate_row(row, schema)
    assert errors, "invalid row should produce at least one error"
    assert any("gold_evidence_relation" in e for e in errors), (
        f"errors must mention the failing field; got {errors}"
    )


def test_compute_per_row_agreement_highlights_disagreement() -> None:
    module = _load_module()
    a = _starter_row("c1")
    b = _starter_row("c1")
    b["gold_evidence_relation"] = "contradicts"
    disagreements = module.compute_per_row_agreement([a], [b])
    assert "c1" in disagreements
    assert "gold_evidence_relation" in disagreements["c1"]


def test_render_row_form_returns_streamlit_widgets() -> None:
    """Smoke test: the form-building function returns a
    mapping from field name to widget descriptor. The
    Streamlit server is not required."""
    module = _load_module()
    fields = module.fields_for_form()
    assert isinstance(fields, list) and fields, "field list must not be empty"
    for field in fields:
        assert "name" in field
        assert "label" in field
    names = {f["name"] for f in fields}
    for required in (
        "case_id",
        "split",
        "domain",
        "claim_text",
        "gold_evidence_relation",
        "annotation_status",
    ):
        assert required in names, f"form must include {required!r}"


def test_pilot_annotation_artifact_loads_through_schema() -> None:
    """The committed pilot fixture (alice/bob/ada) must
    validate against the JSON Schema end-to-end. This is
    the offline version of the UI's row-by-row
    validation; if a future change breaks the schema
    or the pilot data, this test fails first."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    module = _load_module()
    pilot_dir = REPO_ROOT / "eval" / "pilot_annotation"
    for name in ("annotator_a.jsonl", "annotator_b.jsonl", "adjudicator.jsonl"):
        path = pilot_dir / name
        assert path.exists(), f"{path.relative_to(REPO_ROOT)} is missing"
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            errors = module.validate_row(record, schema)
            assert errors == [], (
                f"{name} contains an invalid row: {errors}\n{record}"
            )
