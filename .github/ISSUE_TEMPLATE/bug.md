---
name: Bug report
about: Report a regression or unexpected behaviour in the evidence pipeline
title: "bug: <one-line summary>"
labels: ["bug", "needs-triage"]
---

## Symptom

A user-visible symptom, not the suspected cause. Include the
endpoint, the analysis id (if available), the tenant id (if
shareable), and the time the symptom was observed.

## Reproduction

The minimum steps to reproduce. For pipeline bugs this is
typically a paper id + reference id + the citation that fails.

## Expected behaviour

What should have happened, per the master blueprint or the
relevant ADR.

## Observed behaviour

What actually happened. Paste the relevant log line, the
evidence card, the API response, or the screenshot.

## Evidence quality impact

- [ ] Quote fabrication
- [ ] Span mismatch
- [ ] Scope mismatch
- [ ] Overgeneralization
- [ ] False abstention
- [ ] False support
- [ ] Cross-tenant leakage
- [ ] Other (describe)

## Severity

- [ ] P0 — evidence quality gate violated, or a security control bypassed
- [ ] P1 — major regression, no workaround
- [ ] P2 — minor regression, workaround exists
- [ ] P3 — cosmetic / wording

## Triage

A maintainer will assign the slice and link the relevant ADR.
