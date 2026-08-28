# CiteTrace Team Operating Model

> **Version:** 1.0.0  
> **Purpose:** Help a small, possibly student-heavy team run the project with professional discipline.

---

## 1. Roles and decision rights

| Role | Accountable for |
|---|---|
| Product/domain lead | user problem, scope, PRD, copy and launch decisions |
| Engineering lead | architecture, code quality, integration and delivery flow |
| ML/retrieval lead | retrieval, verification, calibration and evaluation |
| Frontend/product engineer | reader UX, accessibility and interaction quality |
| Data/annotation lead | gold-set sampling, handbook, agreement and adjudication |
| Security/privacy reviewer | threat model, tenant/privacy/source-access gates |
| Operations owner | deployment, SLOs, cost and incident readiness |

One person may hold multiple roles, but every high-risk decision names one accountable reviewer.

---

## 2. Working artifacts

| Artifact | Purpose | Owner |
|---|---|---|
| Master blueprint | single product/system truth | product + engineering |
| PRD | user behavior and acceptance | product |
| ADR | irreversible/architecture decision | engineering |
| API/schema contracts | interface truth | owning engineers |
| Gold set/evaluation report | quality truth | ML + annotation |
| Risk register | known risk and mitigation | all leads |
| Implementation plans | executable work sequence | engineering |
| Release report | evidence for shipping | release owner |

Chat messages and meeting memory are not authoritative until reflected in these artifacts.

---

## 3. Cadence

### Weekly planning/review

- review user/quality/operational signals
- select plan tasks whose dependencies are complete
- inspect risk changes
- confirm evaluation cases for new behavior
- assign owners and review gates

### Short engineering sync

Focus on blockers, contract changes, quality risks and integration—not status narration.

### Weekly quality review

- inspect wrong-paper/evidence/relation examples
- review gold-set disagreement
- compare current vs baseline metrics
- decide whether issues are data, parsing, retrieval, model, prompt, UX or policy

### Milestone gate

- demonstrate end-to-end acceptance scenario
- show test/evaluation evidence
- review security/source policy
- update docs and risk register
- explicitly approve next milestone scope

---

## 4. Work item readiness

A task is Ready only when it has:

- named user/system outcome
- exact acceptance criteria
- files/contracts/interfaces identified
- failure/abstention behavior
- privacy/source implications
- tests or evaluation cases
- dependencies resolved

---

## 5. Definition of Done

- acceptance criteria pass
- tests written first or failure reproduced
- focused and full relevant tests pass
- schemas/contracts/docs synchronized
- observability added
- security and provenance invariants tested
- evaluation impact measured when semantic behavior changes
- code reviewed
- rollback/feature flag for risky model behavior
- no unowned follow-up required for the feature to be safe

---

## 6. Git and review flow

- protected `main`
- short-lived branches or isolated worktrees
- conventional, scoped commits
- one independently reviewable plan task per PR when practical
- required CI and reviewer approval
- architecture/security/semantic model changes require specialist reviewer
- no force push to shared protected branches

PR description includes:

- goal and plan task
- behavior before/after
- tests/evaluation evidence
- contract/migration impact
- privacy/source-policy impact
- screenshots for UX
- rollback considerations

---

## 7. Decision process

### Reversible decisions

Owning engineer decides after documenting assumptions and tests.

### Hard-to-reverse decisions

ADR required for:

- storage/runtime service
- public API semantics
- identity/version model
- confidence/abstention policy
- model/source data transmission
- source acquisition path
- tenancy or retention behavior

### Disagreement

Use evidence order:

1. safety/legal constraints
2. product invariants
3. user research
4. evaluation/operational data
5. reversible experiment
6. accountable owner decision

---

## 8. Annotation operations

- annotators receive handbook and qualification cases
- source assets and versions are locked
- two independent labels for critical fields
- disagreement categories recorded
- adjudication done by domain-qualified reviewer
- annotators cannot see system prediction before initial label
- regular drift and fatigue checks
- rights and privacy of evaluation content documented

---

## 9. Incident and defect learning

For critical quality/security defects:

- contain affected route/version
- identify earliest missing control
- add minimal reproducible test/gold case
- repair system and documentation
- check similar classes, not only one example
- record postmortem without blame

A fabricated quote or cross-tenant leak is not treated as an ordinary UI bug.

---

## 10. New team member onboarding

1. read README, master blueprint and AGENTS.md,
2. run starter tests locally,
3. trace one synthetic evidence case through contracts/database,
4. review one wrong-paper and one scope-mismatch case,
5. make a small test-first change,
6. complete security/source-policy briefing before touching acquisition/model routes.
