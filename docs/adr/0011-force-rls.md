# ADR-0011: Force row-level security on every tenant table

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

`SECURITY.md` lists `FORCE ROW LEVEL SECURITY` among the
minimum deployment controls and `docs/00_MASTER_BLUEPRINT.md §10`
treats cross-tenant access as a P0 security control. The
canonical `contracts/db/schema.sql` enables `ROW LEVEL SECURITY`
on 21 tables, but never `FORCE`s it. Without the `FORCE`
keyword, a table **owner** is exempt from the policy; an
application role that owns a table can read or write any row
without the `app.workspace_id` clause being enforced. That is
the same as having no policy for the role that actually runs
the application queries.

The v1.0 verification report already flagged this gap implicitly
when it noted that the live PostgreSQL execution had not been
verified. Slice 13 closes the gap.

## Decision

1. `contracts/db/schema.sql` adds `ALTER TABLE ... FORCE ROW
   LEVEL SECURITY;` immediately after every `ENABLE ROW LEVEL
   SECURITY;` statement, for every table that has a
   `workspace_id` column. The statement is idempotent and
   does not affect non-owner roles.
2. `starter/services/api/migrations/0001_initial.sql` stays
   byte-for-byte equal to the canonical schema (the existing
   `test_schema_sync.py` already locks the two files together).
3. The contract test in
   `tests/test_rls_force_and_cross_tenant.py`:
   - lists every table that has a `workspace_id` column and
     asserts the row-level security is `enabled` and `forced`
     in `pg_class.relrowsecurity` and `relforcerowsecurity`;
   - creates two distinct workspaces, each with one analysis
     and one evidence link, as two distinct Postgres roles
     that own the relevant tables;
   - asserts that a query from role A with
     `SET LOCAL app.workspace_id = '<A>'` returns only A's
     rows;
   - asserts that a query from role A without that setting
     returns zero rows (the policy denies the read outright
     under `FORCE`);
   - asserts that a deliberate cross-tenant write from role A
     targeting B's row is denied by the policy and that the
     `audit_decision` table records the attempt.
4. The test is wired into the existing `pgvector-smoke` CI
   job because it shares the same PostgreSQL container.

## Consequences

- The `app.workspace_id` clause is now load-bearing for every
  read and write on every tenant-scoped table. A future
  application role that bypasses the clause by mistake
  receives an empty result set rather than a security breach.
- The owner exemption no longer exists. Application roles
  must use the `app.workspace_id` GUC, which is the
  AGENTS.md invariant 'application roles must not bypass
  RLS' applied at the database level.
- The forced RLS does not affect non-tenant tables
  (`taxonomy`, `schema_registry`, `prompt_version`,
  `model_provider`, `model_pricing`, `feature_flag`) which
  carry no `workspace_id` and are read-only at runtime.
- A small set of statements in the existing migration file
  change. The previous migration hashes in any deployed
  environment will be invalidated; the migration runner
  must accept the new hash. The release checklist
  (`starter/ops/release/release-checklist.md`) is updated to
  call this out.

## Out of scope (explicitly)

- A formal benchmark of the RLS overhead. The RLS policy is
  on `workspace_id` (uuid) which is the primary tenant
  index; the overhead is negligible but a follow-up ADR
  will measure it under load.
- Per-statement policies (USING vs WITH CHECK). The current
  policies use a single `USING` clause that covers both
  SELECT and INSERT/UPDATE/DELETE; a future ADR may add
  `WITH CHECK` if a write-time invariant emerges.
- Column-level security. RLS is row-level; column-level
  security is best handled in the application layer per
  the master blueprint.
- Encryption at rest. RLS does not replace column-level
  encryption; that is a separate `pgcrypto` concern tracked
  in `SECURITY.md`.
