# Rollback

This runbook covers rolling the CiteTrace product back to a previous
release. It is intentionally short because the prerequisites
(observability, automation, change records) are heavy; the actual
steps are a small number of deliberate actions.

## When to use this runbook

- The release quality gate has regressed in production and a
  faster-than-fix response is required.
- A security advisory (model provider, dependency CVE, GROBID
  CVE) requires an immediate version change.
- A legal hold or takedown notice is received that the current
  release cannot honour; the previous release is the safest state.

## Pre-conditions

- The on-call has the `release:rollback` IAM role bound.
- The previous release's evidence gate report is in the artifact
  store and is **not** the artefact that triggered the rollback.
  If the previous release also failed, the rollback target is the
  release before that.

## Procedure

1. **Mark the current release as `paused` in the registry.**
   `python -m citetrace_api.release.registry mark --release <current> --state paused`
   so that no new analyses target the bad version.

2. **Pin the previous release as the new default.**
   `python -m citetrace_api.release.registry set-default --release <previous>`
   This changes the database flag, not the running pods. The change
   is read on every analysis start, so in-flight analyses finish on
   the bad version but no new analysis picks it up.

3. **Roll the deployment back.**
   `kubectl rollout undo deploy/api -n citetrace --to-revision=<previous>`
   and `kubectl rollout undo deploy/worker -n citetrace --to-revision=<previous>`.
   The web app is rolled back by re-tagging the image and re-running
   the standard `make deploy-web` target.

4. **Run the post-rollback smoke test.**
   `make smoke POST_RELEASE=<previous>` from the `ops/` directory.
   Smoke must pass within 10 minutes; if not, the rollback has
   surfaced a deeper issue and the incident is escalated.

5. **Open a postmortem within 24 hours** including the trigger,
   the time-to-rollback, the queue depth at the moment of pin, and
   any evidence-chain artefacts that were emitted by the bad
   release. The postmortem owner is the on-call SRE who triggered
   the rollback.

## What this runbook does not cover

- Schema rollbacks. A schema change that needs reverting must go
  through the database-restore runbook instead, because a code-only
  rollback on top of a new schema produces a database state with no
  corresponding code path.
- Forward-only fixes for evidence quality. If a release is bad
  because it weakens the evidence gate, the right action is to
  write a follow-up release that restores the gate, not to
  permanently disable it via rollback.
