# ADR-0019: DB-backed gold-set ingestion pipeline

- **Status:** Accepted
- **Date:** 2026-08-30

## Context

The annotation pipeline (Slice 14) produces `adjudicated.jsonl`
as its final output. A human annotator or adjudicator has
reviewed each citation-level claim and assigned a
`evidence_relation`, `citation_intents`, and
`transformation_kind`. The output is a JSON Lines file where
each line is one evidence-link record.

The `evidence_link` table in the canonical PostgreSQL schema
is the relational representation of these records. The gap
is a tool that reads `adjudicated.jsonl` and upserts the rows
into the database so that:
- the gold-set is queryable via SQL
- the quality metrics (Krippendorff α, Slice 19-D) can be
  computed from the DB directly
- downstream consumers (analytics dashboard, audit reports)
  do not need to parse JSON Lines

## Decision

`scripts/ingest_adjudicated.py` is the ingestion command.
It:

1. Reads `adjudicated.jsonl` (default path;
   configurable via `--input` / `CITETRACE_ADJUDICATED_JSONL`)
   line by line.
2. For each line, validates the record against the
   `AdjudicatedRecord` Pydantic model.
3. Resolves the cited work's `work_id` and `work_version_id`
   by matching the adjudicated record's external identifiers
   (DOI, title+authors) against the `scholarly_work` and
   `work_version` tables.
4. Upserts an `analysis_run` row (the analysis the adjudicator
   was working within).
5. Upserts a `citing_claim` row.
6. Upserts an `evidence_link` row with the adjudicated
   `evidence_relation`, `citation_intents`,
   `transformation_kind`, and `confidence_vector`.
7. Emits a progress bar and a summary table on completion.

The command is idempotent: re-running it with the same
`analysis_id` overwrites the existing rows (upsert via
`ON CONFLICT DO UPDATE`). This allows incremental ingestion
and re-ingestion after corrections.

The command is NOT part of `make test` because:
- `make test` is offline-only (no DB connection)
- Ingestion requires a live PostgreSQL + pgvector instance
- The adjudicated.jsonl file may not be present in all
  environments

The command is wired into the CI pipeline as a separate step
that runs after `make check` and requires the live DB.

## Data model

`AdjudicatedRecord` (Pydantic, validated at ingest time):

```
analysis_id: UUID
workspace_id: UUID
citing_asset_id: UUID
citing_claim_span: str
cited_external_ids: dict[str, str]   # e.g. {"doi": "10.x/...", "title": "..."}
evidence_relation: evidence_relation
citation_intents: list[citation_intent]
transformations: list[transformation_kind]
confidence_vector: dict[str, float]  # e.g. {"precision": 0.9, "recall": 0.7}
calibration_profile: str
status: evidence_link_status
access_level: access_level
model_execution_ids: list[UUID]
```

## Consequences

- The gold-set is stored in PostgreSQL, not just in a JSON
  Lines file. SQL queries can compute per-relation accuracy,
  per-intent coverage, and per-workspace aggregation.
- The Krippendorff α computation in the contract test can
  be rewritten to read from the DB instead of from the JSON
  Lines file, making it self-contained.
- The ingestion command is a one-line addition to the
  production deploy checklist (ADR-0002 §Deploy).
- If the adjudicated.jsonl contains a reference to a work
  that is not yet in the database, the ingest command logs
  a warning and skips the row (it does not create a stub
  scholarly_work row). A follow-up run after the work is
  registered will ingest the missing row.

## Out of scope (explicitly)

- Real-time streaming ingestion. The adjudicated.jsonl is a
  batch file; streaming ingestion is a follow-up.
- Schema migration for the gold-set tables. The current
  schema already covers the needed columns.
- A web UI for reviewing/adjudicating. That is the
  Streamlit annotator UI (ADR-0016) which writes to the
  same adjudicated.jsonl file this command reads.
