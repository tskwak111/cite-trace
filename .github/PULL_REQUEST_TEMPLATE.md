## What this PR does

One sentence summary; the body should make it obvious whether the
change can ship without further context.

## Slice / ADR

- [ ] Touches a public shape (REST, event, JSON Schema, taxonomy, prompt, schema.sql, K8s manifest). The relevant contract file is updated in the same commit.
- [ ] Has an ADR or links to an existing ADR under `docs/adr/`.
- [ ] Touches a runtime gate. The corresponding `tests/test_*.py` and `starter/ops/tests/test_*.py` are updated in the same commit.
- [ ] Touches a prompt, model, or feature flag. `eval/` is updated or the change is recorded in the ADR.

## Evidence quality

- [ ] No new source-quote, span, or evidence chain is introduced without the corresponding version and span coordinates.
- [ ] No "synthetic passes" relaxation: the release gate is not weakened to make a demo pass.
- [ ] No `passed: True` is hard-coded in a script that is reachable from a release pipeline.

## Tests

- [ ] `pytest -q starter/services/api/tests` passes locally.
- [ ] `pytest -q starter/ops/tests` passes locally.
- [ ] `uv run --no-project --with pyyaml --with jsonschema --with openapi-spec-validator python scripts/validate_package.py` reports 8/8 PASS.
- [ ] `uv run --no-project --with pyyaml python scripts/run_release_evaluation.py --gold eval/sample_cases.jsonl --predictions eval/sample_predictions.jsonl --rubric eval/rubric.yaml --output /tmp/eval.json` is run; the report is archived in the PR description (the synthetic contract is expected to fail until the live blocking metrics are wired in).
- [ ] If the change touches GROBID integration, the live smoke test (`pytest -q CITETRACE_GROBID_URL=http://localhost:8070 starter/services/api/tests/test_grobid_live_smoke.py`) is run with a local `grobid/grobid:0.9.1-crf` container.

## Security

- [ ] No new secret, key, or credential is committed. The secret-manager boundary (`starter/ops/policies/secret_manager_boundary.yaml`) is updated if a new secret is introduced.
- [ ] The OTel collector config (`starter/ops/observability/otel-collector.yaml`) is updated if a new secret attribute is emitted.
- [ ] No `print` of `pdf_bytes`, parsed text, model output, or any user content is added.

## Documentation

- [ ] `CHANGELOG.md` has an entry under the current version.
- [ ] `docs/adr/` has a new ADR if the change is architecture-affecting.
- [ ] `VERIFICATION_REPORT_*.md` is updated if the verification conclusion changes.

## Reviewer checklist

- [ ] CI is green.
- [ ] The "smallest coherent change" rule is honoured: one commit per logical change, each with a passing test.
- [ ] If the change is large, it is split into vertical slices and the slice order is consistent with `docs/adr/0008-vertical-slice-rebuild.md` or a successor ADR.
