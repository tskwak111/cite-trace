# ADR-0010: Live blocking-metric collection for the release gate

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

`scripts/run_release_evaluation.py` (Slice 2) refuses to pass on
synthetic samples alone because three blocking metrics are
unmeasured:

- `schema_valid_rate` (operator `gte 1.0`),
- `cross_tenant_access_failures` (operator `eq 0`),
- `inaccessible_source_false_full_text_claims` (operator `eq 0`).

The master blueprint §13 lists those three as blocking: a build
that ships with a non-trivial schema-invalid rate, a single
cross-tenant access failure, or any inaccessible-source
misrepresentation is not a credible release. Until v1.2.0 the
release pipeline had no instrumentation that produced those
numbers; this ADR adds it.

The metrics must be:

1. **Live**, not synthetic. The synthetic 4-case gold set is
   a contract for the scorer; the release gate is a contract
   for the running pipeline.
2. **Tenant-scoped**. The collection must be RLS-aware so a
   workspace's metrics cannot be polluted by another
   workspace's data.
3. **Auditable**. Each measurement records the schema
   hash, the contract version, and the analysis ids it
   observed, so the release audit log can replay the
   measurement.
4. **CI-runnable**. A staging environment or a recorded
   fixture is enough; the script does not need a real
   production tenant.

## Decision

Add `scripts/collect_live_blocking_metrics.py` that:

1. Connects to the live database at
   `CITETRACE_DATABASE_URL` (PostgreSQL 18 + pgvector).
2. Reads the analysis_run, evidence_link, and explanation_statement
   rows that were written since the previous successful
   collection (or since the configured window start).
3. For each analysis, re-validates the emitted `evidence-link`
   payload against `contracts/schemas/evidence-link.v1.schema.json`
   and counts the number of validations. `schema_valid_rate`
   is the fraction of valid / total.
4. Counts `cross_tenant_access_failures` from the
   `audit_decision` table where `decision_kind = 'cross_tenant_access'`
   and `outcome = 'denied'`. The blueprint invariant is that
   every cross-tenant access is denied, so the count is the
   number of *attempts* (zero is the only acceptable value).
5. Counts `inaccessible_source_false_full_text_claims` from
   the `evidence_link` table where `source_access_level =
   'not_accessible'` and the linked span quotes more than
   the 25-character abstract-only boundary. This is the
   signal that the verifier emitted a "full text" claim
   against a source that was not accessible.
6. Writes a JSON report at the path given by `--output` and
   exits 0 when the metrics are within the rubric thresholds,
   1 when a blocking metric is violated, 2 when the input is
   empty / not yet collected.

The script is wired into the release pipeline as a new
`scripts/run_release_evaluation.py` predecessor step:
`run_release_evaluation.py` will accept the live-metric
JSON as input and apply the rubric, no longer treating
the three metrics as unmeasured.

Tests in `tests/test_live_blocking_metrics.py` cover the
contract:

- `test_schema_valid_rate_is_one_for_valid_run`
- `test_cross_tenant_access_failures_counts_denied_attempts`
- `test_inaccessible_source_false_full_text_claims_is_zero_on_clean_run`
- `test_collector_exits_two_on_empty_window`

The collection is **read-only** with respect to the
canonical schema: it only reads existing tables. No new
table is created. The connection is forced to a single
tenant by `SET LOCAL app.tenant_id` so a misconfigured
script cannot read across tenants.

## Consequences

- The release gate can now pass on a real (small) staging
  run even when the human-annotated gold set is still below
  the 300-case minimum, provided the live metrics are within
  thresholds. The 300-case minimum remains a separate gate
  enforced by `scripts/build_goldset.py preflight`.
- A failing live metric surfaces immediately at the release
  step rather than after deployment, matching the
  blueprint's "never weaken evidence or security gates
  merely to make a demo pass" rule.
- The script is a single point of truth for the three
  blocking metrics. Future metrics (e.g. reference-resolution
  top-1) land in the same script under the same `--output`
  contract.

## Out of scope (explicitly)

- Recording or replaying the audit log. The script reads
  existing rows; it does not write a new audit trail.
- Synthesising missing metrics. If a metric is not
  measurable from the data, the script reports `null` and
  the release gate fails closed, matching the Slice 2
  policy.
- A new contract version. The metrics are computed against
  the existing `v1` schemas.
- Multi-tenant staging. The script is single-tenant by
  construction; multi-tenant staging is run as N separate
  invocations.
