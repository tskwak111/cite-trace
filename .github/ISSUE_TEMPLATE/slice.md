---
name: Slice / task
about: Track a vertical slice from docs/adr/ or a follow-up
title: "slice: <short name>"
labels: ["slice"]
---

## Slice

- [ ] Named in `docs/adr/0008-vertical-slice-rebuild.md` or a successor ADR
- [ ] Not yet started
- [ ] In progress
- [ ] Blocked
- [ ] Completed

## Acceptance criteria

Concrete, testable bullets. A slice is done only when every
bullet is checked and a contract test asserts it.

- [ ] ...
- [ ] ...
- [ ] ...

## Required artefacts

- [ ] Failing test written before the implementation.
- [ ] Implementation committed with a conventional-commit message that names the slice.
- [ ] `pytest -q starter/services/api/tests` and `pytest -q starter/ops/tests` are green.
- [ ] `scripts/validate_package.py` is 8/8 PASS.
- [ ] Any public contract (REST, event, JSON Schema, taxonomy, prompt, schema.sql, K8s manifest) is updated in the same commit.
- [ ] If the change is architecture-affecting, an ADR is added or updated.

## Out of scope

Anything explicitly excluded from this slice so the reviewer's
expectations are aligned.

## Notes

Free-form notes for the implementer and the reviewer.
