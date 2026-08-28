# Contributing to CiteTrace

CiteTrace is evidence-critical software. A change is acceptable only when it preserves inspectability, lawful source handling, tenant isolation, and explicit uncertainty.

## Required workflow

1. Read `AGENTS.md`, the relevant specification, and the ADRs before editing.
2. Create a narrowly scoped branch or worktree.
3. Write or update a failing test before behavior changes.
4. Keep public contracts backward compatible within `v1`; use an ADR for semantic changes.
5. Run the repository gates before opening a pull request.
6. Include an evaluation comparison for changes to prompts, models, retrieval, relation labels, confidence, or abstention.
7. Ask for security/legal review when source access, upload handling, retention, export, or workspace isolation changes.

## Local quality gates

From the package root:

```bash
python scripts/validate_package.py
PYTHONPATH=starter/services/api/src pytest -q starter/services/api/tests
python -m compileall -q starter/services/api/src starter/services/api/tests scripts
node scripts/validate_typescript_syntax.js
python scripts/validate_eval_assets.py
python scripts/score_sample_predictions.py \
  --gold eval/sample_cases.jsonl \
  --predictions eval/sample_predictions.jsonl
```

With development dependencies installed:

```bash
cd starter
make api-lint
make api-typecheck
make api-test
make web-check
make contracts-check
```

## Pull-request evidence

Every pull request must state:

- user-visible behavior changed,
- contracts or migrations changed,
- tests added or updated,
- evaluation slice and before/after metrics,
- privacy/security/source-policy impact,
- rollback method,
- screenshots for reader UI changes,
- known limitations that remain.

## Non-negotiable review blockers

A reviewer must block a change that can:

- display a quotation not exactly anchored to retained normalized source text,
- classify metadata-only content as direct empirical support,
- bypass a paywall, robots/terms restriction, or workspace source policy,
- let model output select arbitrary URLs or execute document instructions,
- hide an abstention or collapse stage confidence into unexplained certainty,
- mix private assets, embeddings, feedback, or exports across workspaces,
- change a closed taxonomy without migration and regression evaluation.

## Commit style

Use small commits with a conventional prefix, for example:

```text
feat: add deterministic DOI candidate scoring
fix: reject redirected source URLs into private networks
test: lock scope-mismatch regression cases
docs: record source-acquisition ADR
chore: update contract examples and checksums
```
