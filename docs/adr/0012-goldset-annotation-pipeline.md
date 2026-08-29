# ADR-0012: Human-annotated gold-set pipeline

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

The release gate refuses to pass on synthetic samples alone.
`scripts/build_goldset.py` (Slice 7) enforces the 300-case
minimum but ships only four synthetic cases. The blueprint
§11 requires "300 adjudicated citation cases across at least
8 research domains" plus 50 multi-reference clusters, 40
inaccessible/abstract-only references, 40 scope-mismatch /
overgeneralization / contradiction cases, and 30
method-transformation cases. None of these have a tool, a
schema, or a workflow yet.

The v1.6.0 verification report lists the 300-case human
gold set as the next blocker for a "first credible release".
This ADR adds the *infrastructure* to collect, validate, and
adjudicate that set; the annotation itself is a
human-in-the-loop activity that this ADR explicitly
recognises it cannot complete on its own.

## Decision

The Slice 14 deliverable is the four-script + one-schema
pipeline that the user (or a future human-in-the-loop
process) drives:

1. `contracts/schemas/goldset-annotation.v1.schema.json`
   validates every row of the human annotation. The schema
   pins the 27 columns from `eval/goldset_template.csv`
   plus a `version` field so future schema changes are
   explicit. A row that fails validation is reported with
   the column that failed, never silently coerced.
2. `scripts/annotate.py` provides three sub-commands:
   - `init` writes a starter JSONL with one row per
     case-id the user supplies (e.g. from the synthetic
     seed or from a CSV of cited papers).
   - `validate` checks every row against the JSON Schema
     and reports the count of valid / invalid / total rows.
   - `summary` prints the per-domain and
     per-evidence-relation counts so the user can see
     which slices still need cases.
3. `scripts/compute_iaa.py` reads two (or more)
   annotation files produced by different annotators and
   reports Cohen's κ for the nominal dimensions
   (`gold_evidence_relation`, `gold_citation_intents`,
   `gold_transformations`, `expected_abstention_code`).
   The threshold the blueprint implies is κ ≥ 0.7; values
   below are flagged.
4. `scripts/adjudicate.py` merges two annotation files
   into a single adjudicated file. For each case the
   adjudicator's file is the source of truth; if the
   adjudicator file is missing the majority vote is used;
   ties are surfaced for human review.

The contract tests in
`tests/test_goldset_annotation_pipeline.py` cover the four
scripts end-to-end and a `tests/test_goldset_minimum.py`
extension asserts the existing 300 / 8 minimum is enforced
on the *human* gold set (not just the synthetic seed).

## Consequences

- A user with a CSV of cited papers and two domain
  experts can produce a credible 300-case gold set
  without writing any code. The infrastructure is
  available; the labour is the work of the experts.
- The release gate continues to refuse to pass on the
  synthetic seed alone; the gate passes only when the
  human gold set is ≥ 300 and the IAA is ≥ 0.7. The
  existing `scripts/build_goldset.py preflight` is the
  surface that surfaces this.
- A future slice can land a Streamlit or a simple HTML
  annotator UI; this ADR does not add a UI because the
  primary annotators are domain experts with their own
  toolchain (currently a shared spreadsheet). The CLI
  pipeline is the contract; the UI is a follow-up.

## Out of scope (explicitly)

- The 300 human-annotated cases themselves. This ADR
  adds the *infrastructure* for the gold set, not the
  gold set. The 300 cases remain the next blocker for a
  first credible release; they are a multi-week
  human-in-the-loop activity, not an AI task.
- An annotator UI. The CLI pipeline accepts
  `csv-to-jsonl` and `jsonl-to-csv` so a spreadsheet
  workflow is supported without code.
- A streaming or async ingest path. The pipeline is
  synchronous and single-process; the 300-case file
  fits in memory on any laptop.
- An inter-annotator agreement for ordinal dimensions.
  The blueprint's annotation dimensions are all
  nominal or scale; we compute Cohen's κ for nominal
  and leave Krippendorff's α for scale (usefulness) as
  a follow-up if a scale dimension is added.
