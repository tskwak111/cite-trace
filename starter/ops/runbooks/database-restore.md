# Database Restore

This runbook covers restoring the CiteTrace PostgreSQL database from a
point-in-time archive when a full or partial restore is required (region
failure, accidental schema corruption, evidence chain corruption).

## When to use this runbook

- A user-visible incident that requires the database to be rolled back
  to a known-good state.
- The verification-report contract hash recorded in `schema_registry`
  no longer matches the running schema (this means a migration
  partially failed or the wrong contract is in production).
- `pg_dump`-based on-demand restore after a legal hold or compliance
  request, before the customer-facing read replica is rewound.

## Pre-conditions

- PagerDuty incident channel open and acknowledged by the on-call DBA.
- Latest `schema_registry` row read from the read replica and recorded
  in the incident ticket. This hash is the target contract version.
- Read replicas paused via `ALTER SYSTEM SET default_transaction_read_only = on;`
  and `pg_reload_conf()` so no in-flight transaction drifts during the
  restore window.
- Object-store archive keys for the target point-in-time are listed
  by the retention service and the read-replica lag is `0 seconds`.

## Procedure

1. **Open a maintenance window.** Disable public API ingress at the
   load balancer (`kubectl scale deploy/api --replicas=0 -n citetrace`)
   so that no new tenant sessions open a connection pool. The
   async workers (resolution, acquisition, retrieval) must be
   drained before step 2: run
   `kubectl exec deploy/worker -n citetrace -- python -m citetrace_api.orchestration.drain --timeout 600`
   and confirm that the queue depth on `redis://citetrace-queue/0`
   is `0` for the named tenant sets.

2. **Pause writes.** Run
   `kubectl exec deploy/api -n citetrace -- psql "$DATABASE_URL" -c "SET LOCAL citetrace.maintenance = 'restore';"`
   and set the `MAINTENANCE_MODE` environment variable on every
   `api` pod so that the FastAPI process refuses to start new
   transactions. This is a hard pre-condition; if any connection
   pool returns a session with `MAINTENANCE_MODE=off`, abort.

3. **Snapshot the current state.** Run
   `pg_dump --schema-only --no-owner $DATABASE_URL > /var/tmp/pre-restore-schema.sql`
   and copy it to the incident ticket. This is the artifact auditors
   will request to confirm what was live before the restore.

4. **Restore from object-store archive.**
   `aws s3 cp s3://citetrace-archive/db/<contract-hash>/<pitr-timestamp>.pg_dump .`
   then
   `pg_restore --clean --if-exists --no-owner --dbname=$DATABASE_RESTORE_URL restore.pg_dump`
   into the restore URL, **never** into the production URL.

5. **Verify the contract hash.** Compare the SHA-256 of
   `/var/tmp/pre-restore-schema.sql` against the schema hash the
   restore produced. They must match unless the incident was a
   schema migration regression; in that case open a new ticket
   tagged `schema-drift` and stop here.

6. **Promote the restored database.** Atomically flip the
   `DATABASE_URL` secret in the secret manager and reload the API
   pods. Confirm via
   `SELECT 1 FROM schema_registry WHERE contract_hash = '<expected>';`
   that the production contract matches the restored contract.

7. **Re-enable traffic.** `kubectl scale deploy/api --replicas=<N>`,
   then re-enable worker queues. Watch the queue depth and the
   `analysis_pipeline_age_seconds` metric for 10 minutes. If either
   exceeds the runbook threshold, escalate to the quality-gate
   regression runbook.

## Roll-forward

If step 5 reveals an unexpected schema difference and the restored
copy is unusable, do **not** attempt a second restore. Open a P2
ticket and follow the rollback runbook instead.

## Postmortem requirements

Within 48 hours: write a postmortem that includes the pre-restore
schema dump, the contract hash, the time spent at each step, the
queue depth at promotion, and the time-to-recovery for the slowest
tenant. The postmortem is reviewed in the weekly evidence-quality
meeting; it is not optional.
