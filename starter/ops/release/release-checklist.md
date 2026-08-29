# Release Checklist

A CiteTrace release is not a single artifact; it is the combination
of the API image, the web image, the database contract hash, the
prompt versions, and the model provider configuration. Every item
below must be confirmed before the release is marked as the default
in the registry. Skipping an item is grounds for the on-call to
abort the release and roll back.

## Pre-release

- [ ] `make test` passes locally and in CI.
- [ ] `uv run --with pyyaml python scripts/run_release_evaluation.py --gold eval/sample_cases.jsonl --predictions eval/sample_predictions.jsonl --rubric eval/rubric.yaml --output /tmp/eval.json`
      is run and the report is archived in the release ticket.
      The script's exit code must be `0` for the release to be
      considered; the synthetic contract must be supplemented by
      the live blocking metrics from the staging environment.
- [ ] `make contract-validate` passes (OpenAPI, JSON Schema,
      event catalog, examples).
- [ ] Database migration is forward-only and the contract hash
      is recorded in `schema_registry`.
- [ ] Prompt versions in `prompts/` are pinned by commit SHA in
      the release ticket; the change log lists which prompts
      changed and why.
- [ ] Model provider configuration in `config/model-routing.yaml`
      lists every provider used by the release and the keys have
      been rotated within the configured retention window.
- [ ] Feature flags in `config/feature-flags.yaml` are reviewed
      and any default-flipping flag is explicitly listed.
- [ ] Security advisories over the previous 7 days are triaged.
- [ ] `SECURITY.md` controls (MIME verification, byte/page limits,
      RLS enforcement test, secret manager) are confirmed for the
      new release.
- [ ] Evidence quality gold set is current (no cases older than
      90 days without re-annotation).

## Release window

- [ ] On-call SRE is online and has the `release:promote` role.
- [ ] Maintenance window is announced on the status page 30
      minutes before the cut.
- [ ] `kubectl apply -f starter/ops/deploy/base/` is applied and
      the new pods reach `Ready` within 5 minutes.
- [ ] Smoke test passes (see `ops/runbooks/rollback.md` step 4).
- [ ] `analysis_pipeline_age_seconds` is below the runbook
      threshold for 10 minutes after the cut.

## Post-release

- [ ] The release artifact (image digests, prompt SHAs, contract
      hash, evaluation report JSON) is archived in the artifact
      store and linked from the release ticket.
- [ ] The status page is updated to "all systems operational".
- [ ] The changelog entry is published on the next business day.
- [ ] A 24-hour watch is set on the release health dashboard and
      any regression is escalated via the rollback runbook.
