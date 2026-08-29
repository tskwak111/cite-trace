"""Streamlit annotator UI for the CiteTrace gold set.

This is a single-file Streamlit application that drives
the human-annotated gold set pipeline (Slice 14 / ADR-0016).
It reads and writes a JSONL file that conforms to
`contracts/schemas/goldset-annotation.v1.schema.json`; the
same contract is enforced by the offline `validate` step
in `scripts/annotate.py`.

Run:

    pip install streamlit jsonschema
    streamlit run scripts/annotate_ui.py

The UI is intentionally a single file with no database,
no auth, and no multi-tenant storage. The file the user
opens is the file the user saves. A production
deployment wires a CRUD layer on top of the same JSONL
contract; that is a deployment follow-up.

The module also exposes three helper functions
(`validate_row`, `fields_for_form`,
`compute_per_row_agreement`) that the contract test
in `tests/test_annotate_ui.py` exercises without launching
the Streamlit server. The Streamlit widgets are the
load-bearing UI surface; the helpers are the offline
contract.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "contracts" / "schemas" / "goldset-annotation.v1.schema.json"
DEFAULT_PILOT = REPO_ROOT / "eval" / "pilot_annotation" / "annotator_a.jsonl"

# Schema enums that the form widgets need to render
# (select boxes for fields with a closed value set).
EVIDENCE_RELATIONS = (
    "direct_support",
    "partial_support",
    "indirect_support",
    "contradicts",
    "overgeneralized",
    "scope_mismatch",
    "no_relevant_evidence",
    "insufficient_evidence",
    "inaccessible_source",
)
RESOLUTION_STATUSES = (
    "exact_version",
    "correct_work_wrong_or_uncertain_version",
    "ambiguous",
    "unresolved",
    "incorrect",
)
SOURCE_ACCESS_LEVELS = (
    "open_access_full_text",
    "open_access_abstract_only",
    "user_uploaded",
    "publisher_paywalled",
    "not_accessible",
)
SPLITS = ("development", "calibration", "test", "challenge")
ANNOTATION_STATUSES = (
    "pending",
    "annotated_a",
    "annotated_b",
    "adjudicated",
    "rejected",
)
DOMAINS = (
    "machine_learning",
    "natural_language_processing",
    "computer_vision",
    "robotics",
    "computational_biology",
    "physics",
    "economics",
    "psychology",
    "medicine",
    "chemistry",
    "earth_sciences",
    "mathematics",
)


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def validate_row(row: dict, schema: dict | None = None) -> list[str]:
    """Return a list of human-readable validation errors for
    `row` against the JSON Schema. An empty list means
    the row is valid."""
    schema = schema or _load_schema()
    errors: list[str] = []
    for err in sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(row),
        key=lambda e: list(e.absolute_path),
    ):
        path = ".".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{path}: {err.message}")
    return errors


def fields_for_form() -> list[dict]:
    """The ordered list of fields the form renders. The
    `widget` entry names the Streamlit widget the UI
    should use; the `options` entry lists the valid
    choices for select fields and is None otherwise.

    The contract test asserts that every required
    column from the JSON Schema is in this list; the UI
    is allowed to add convenience widgets later.
    """
    return [
        {"name": "case_id", "label": "Case ID", "widget": "text_input",
         "options": None, "required": True},
        {"name": "split", "label": "Split", "widget": "selectbox",
         "options": SPLITS, "required": True},
        {"name": "domain", "label": "Domain", "widget": "selectbox",
         "options": DOMAINS, "required": True},
        {"name": "citing_asset_id", "label": "Citing asset ID",
         "widget": "text_input", "options": None, "required": True},
        {"name": "citing_work_version_id", "label": "Citing work version ID",
         "widget": "text_input", "options": None, "required": True},
        {"name": "citation_cluster_id", "label": "Citation cluster ID",
         "widget": "text_input", "options": None, "required": True},
        {"name": "citation_anchor_id", "label": "Citation anchor ID",
         "widget": "text_input", "options": None, "required": False},
        {"name": "reference_entry_id", "label": "Reference entry ID",
         "widget": "text_input", "options": None, "required": True},
        {"name": "claim_text", "label": "Claim text",
         "widget": "text_area", "options": None, "required": True},
        {"name": "claim_start_offset", "label": "Claim start offset",
         "widget": "number_input", "options": None, "required": True},
        {"name": "claim_end_offset", "label": "Claim end offset",
         "widget": "number_input", "options": None, "required": True},
        {"name": "gold_work_id", "label": "Gold work ID",
         "widget": "text_input", "options": None, "required": False},
        {"name": "gold_work_version_id", "label": "Gold work version ID",
         "widget": "text_input", "options": None, "required": False},
        {"name": "resolution_status", "label": "Resolution status",
         "widget": "selectbox", "options": RESOLUTION_STATUSES, "required": True},
        {"name": "source_access_level", "label": "Source access level",
         "widget": "selectbox", "options": SOURCE_ACCESS_LEVELS, "required": True},
        {"name": "gold_evidence_relation", "label": "Gold evidence relation",
         "widget": "selectbox", "options": EVIDENCE_RELATIONS, "required": True},
        {"name": "expected_abstention_code", "label": "Expected abstention code",
         "widget": "text_input", "options": None, "required": False},
        {"name": "annotation_status", "label": "Annotation status",
         "widget": "selectbox", "options": ANNOTATION_STATUSES, "required": True},
        {"name": "annotator_a", "label": "Annotator A",
         "widget": "text_input", "options": None, "required": True},
        {"name": "annotator_b", "label": "Annotator B",
         "widget": "text_input", "options": None, "required": True},
        {"name": "adjudicator", "label": "Adjudicator",
         "widget": "text_input", "options": None, "required": False},
        {"name": "notes", "label": "Notes",
         "widget": "text_area", "options": None, "required": False},
    ]


def compute_per_row_agreement(
    a_rows: list[dict], b_rows: list[dict]
) -> dict[str, list[str]]:
    """Return a mapping from case_id to the list of
    fields on which the two annotators disagree. The
    UI highlights the disagreement in red so the
    adjudicator can address the most important
    differences first."""
    a_by_id = {r["case_id"]: r for r in a_rows}
    b_by_id = {r["case_id"]: r for r in b_rows}
    diff: dict[str, list[str]] = {}
    for case_id in sorted(set(a_by_id) & set(b_by_id)):
        a, b = a_by_id[case_id], b_by_id[case_id]
        disagreed: list[str] = []
        for dim in (
            "gold_evidence_relation",
            "gold_citation_intents_json",
            "gold_transformations_json",
            "resolution_status",
            "source_access_level",
        ):
            if a.get(dim) != b.get(dim):
                disagreed.append(dim)
        if disagreed:
            diff[case_id] = disagreed
    return diff


def iaa_summary(a_rows: list[dict], b_rows: list[dict]) -> dict[str, float]:
    """Compute κ for the four nominal dimensions. The UI
    renders this next to the per-row agreement table."""
    from compute_iaa import _aligned, _aligned_sets, cohens_kappa, jaccard

    a_by_id = {r["case_id"]: r for r in a_rows}
    b_by_id = {r["case_id"]: r for r in b_rows}
    summary: dict[str, float] = {}
    for dim in ("gold_evidence_relation", "resolution_status"):
        av, bv = _aligned(dim, a_by_id, b_by_id)
        summary[dim] = cohens_kappa(av, bv)
    for dim in ("gold_citation_intents_json", "gold_transformations_json"):
        av, bv = _aligned_sets(dim, a_by_id, b_by_id)
        summary[dim] = sum(jaccard(x, y) for x, y in zip(av, bv)) / max(len(av), 1)
    return summary


def main() -> int:
    """The Streamlit entry point. The function reads the
    JSONL at the path the user supplies (default:
    `eval/pilot_annotation/annotator_a.jsonl`), renders
    every row as a form, and writes the file back on
    save. The schema is enforced on save; an invalid
    field blocks the write and shows a red error
    message under the field.
    """
    try:
        import streamlit as st
    except ImportError:
        print(
            "streamlit is required; install with: uv pip install streamlit",
            file=__import__("sys").stderr,
        )
        return 1

    st.set_page_config(page_title="CiteTrace annotator", layout="wide")
    st.title("CiteTrace gold-set annotator")
    path = Path(
        st.text_input("JSONL path", str(DEFAULT_PILOT.relative_to(REPO_ROOT)))
    ).resolve()
    if not path.exists():
        st.error(f"file not found: {path}")
        return 0

    rows = _read_jsonl(path)
    schema = _load_schema()
    fields = fields_for_form()

    st.write(f"loaded {len(rows)} rows from {path}")

    edited: list[dict] = []
    for index, row in enumerate(rows):
        st.subheader(f"row {index + 1} — {row.get('case_id', '?')}")
        new_row = dict(row)
        errors_by_field: dict[str, list[str]] = {}
        for field in fields:
            name = field["name"]
            label = field["label"]
            widget = field["widget"]
            current = row.get(name, "" if widget != "number_input" else 0)
            key = f"{name}-{index}"
            if widget == "text_input":
                new_row[name] = st.text_input(label, value=str(current or ""), key=key)
            elif widget == "text_area":
                new_row[name] = st.text_area(label, value=str(current or ""), key=key)
            elif widget == "number_input":
                new_row[name] = st.number_input(
                    label, value=int(current or 0), step=1, key=key
                )
            elif widget == "selectbox":
                options = field["options"] or ()
                idx = options.index(current) if current in options else 0
                new_row[name] = st.selectbox(label, options, index=idx, key=key)
        # JSON-list fields
        intents = ", ".join(row.get("gold_citation_intents_json", []) or [])
        new_intents = st.text_input(
            "Citation intents (comma-separated)",
            value=intents,
            key=f"intents-{index}",
        )
        new_row["gold_citation_intents_json"] = [
            s.strip() for s in new_intents.split(",") if s.strip()
        ]
        transformations = ", ".join(row.get("gold_transformations_json", []) or [])
        new_transformations = st.text_input(
            "Transformations (comma-separated)",
            value=transformations,
            key=f"transformations-{index}",
        )
        new_row["gold_transformations_json"] = [
            s.strip() for s in new_transformations.split(",") if s.strip()
        ]
        row_errors = validate_row(new_row, schema)
        if row_errors:
            st.error("; ".join(row_errors))
        else:
            st.success("row valid")
        edited.append(new_row)

    if st.button("Save JSONL"):
        errors_total = sum(
            len(validate_row(row, schema)) for row in edited
        )
        if errors_total:
            st.error(f"refusing to save: {errors_total} field error(s)")
        else:
            _write_jsonl(path, edited)
            st.success(f"saved {len(edited)} rows to {path}")

    st.divider()
    st.header("Inter-annotator agreement")
    a_path = Path(
        st.text_input("annotator A path", str(DEFAULT_PILOT.relative_to(REPO_ROOT)))
    ).resolve()
    b_path = Path(
        st.text_input(
            "annotator B path",
            str(
                (REPO_ROOT / "eval" / "pilot_annotation" / "annotator_b.jsonl")
                .relative_to(REPO_ROOT)
            ),
        )
    ).resolve()
    if a_path.exists() and b_path.exists():
        a_rows = _read_jsonl(a_path)
        b_rows = _read_jsonl(b_path)
        kappas = iaa_summary(a_rows, b_rows)
        st.write("**κ / Jaccard per dimension**")
        for dim, score in kappas.items():
            below = (
                score < 0.7 if "kappa" in dim or "jaccard" in dim else False
            )
            st.write(f"- `{dim}`: {score:.3f}" + ("  ⚠ below 0.7" if below else ""))
        diff = compute_per_row_agreement(a_rows, b_rows)
        if diff:
            st.write("**per-row disagreement**")
            for case_id, fields_ in diff.items():
                st.write(
                    f"- `{case_id}`: {', '.join(fields_)}"
                )

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
