# ADR-0016: Streamlit annotator UI

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

Slice 14 added the JSON Schema, the `annotate.py` /
`compute_iaa.py` / `adjudicate.py` pipeline, and the
`goldset-annotation.v1.schema.json` contract. The
pipeline runs from the command line; domain experts
without a Python toolchain cannot drive it.

The v1.7.0 verification report names a Streamlit
annotator UI as the next user-facing tool. A spreadsheet
workflow is supported by the existing `csv-to-jsonl`
step, but the spreadsheet does not enforce the JSON
Schema on save; the user is one cell away from an
invalid row that the next `validate` step rejects with
no inline hint about which cell.

## Decision

Add `scripts/annotate_ui.py`, a single-file Streamlit
application that:

- reads the JSONL in `eval/pilot_annotation/` (or any
  path the user supplies) and renders the rows as
  editable forms;
- enforces the `goldset-annotation.v1.schema.json`
  contract on every save: an invalid field blocks the
  write and surfaces a red error message under the
  field;
- lets the user choose between `annotated_a`,
  `annotated_b`, and `adjudicated` status so the same
  UI can drive the annotator and the adjudicator
  roles;
- runs `compute_iaa.py` on demand and shows the κ
  scores next to the IAA display, with the per-row
  disagreement highlighted in red;
- downloads the current JSONL on demand so the user
  can hand the file to the next step in the pipeline
  (`adjudicate.py`, `validate`, etc.).

The UI is a single file so a domain expert can run it
with `streamlit run scripts/annotate_ui.py` and a
sample JSONL. No backend, no database, no auth — the
file the user opens is the file the user saves. A
production deployment that wants multi-tenant storage
builds a thin CRUD layer on top of the same JSONL
contract; that is a deployment follow-up.

## Consequences

- A domain expert with no Python knowledge can drive
  the pipeline: open the UI, edit a case, save, and
  hand the JSONL to the IAA step.
- The JSON Schema is the only source of truth: the UI
  re-validates on save and refuses to write a row that
  fails. A field-level error message points to the
  column the user must fix.
- A CI contract test asserts the UI module imports,
  the JSON Schema is loadable, and a sample row can be
  validated end-to-end through the same code path the
  UI uses.

## Out of scope (explicitly)

- A multi-tenant storage layer. The UI operates on a
  local JSONL; a future slice adds a Postgres-backed
  CRUD layer for production.
- Real-time co-editing. The UI saves the entire file on
  each write; concurrent edits clobber each other. A
  follow-up ADR adds an operational-transform or
  row-level lock for collaborative annotation.
- Authentication / authorization. The local JSONL
  workflow has no users; a production deployment wires
  the same auth the rest of the API uses.
