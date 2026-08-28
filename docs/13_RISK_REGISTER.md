# CiteTrace Risk Register

> **Version:** 1.0.0  
> **Scale:** Likelihood (L) and Impact (I), 1–5. Score = L × I.  
> **Review:** At milestone and release gates.

---

## 1. Risk matrix

| ID | Risk | L | I | Score | Primary control | Owner |
|---|---|---:|---:|---:|---|---|
| R-01 | Wrong cited paper/version resolved | 4 | 5 | 20 | multi-provider scoring, thresholds, ambiguity UI, corrections | ML/platform |
| R-02 | Fabricated or altered displayed quote | 3 | 5 | 15 | exact substring/checksum validator, blocking audit | ML/platform |
| R-03 | Relevant evidence not retrieved | 4 | 4 | 16 | hybrid retrieval, counterqueries, Recall@k gold set, abstention | Retrieval |
| R-04 | Support/contradiction misclassified | 4 | 5 | 20 | scope extraction, calibration, verifier ensemble, human review | ML/domain |
| R-05 | Overconfident explanation | 4 | 5 | 20 | statement grounding, stage confidence, copy rules, audit | Product/ML |
| R-06 | Full text unavailable for many references | 4 | 4 | 16 | launch-domain measurement, OA adapters, user upload, limited states | Product/platform |
| R-07 | Copyright or provider-terms violation | 3 | 5 | 15 | lawful-source policy, provenance, no bypass, legal review | Legal/product |
| R-08 | Malicious PDF compromises parser | 3 | 5 | 15 | sandbox, scanning, limits, patched images, red-team | Security |
| R-09 | Prompt injection exfiltrates data or alters analysis | 4 | 5 | 20 | untrusted evidence boundary, no unrestricted tools, schema/audit | Security/ML |
| R-10 | Cross-tenant private document leakage | 2 | 5 | 10 | RLS, object namespace, authorization tests, audit | Security/platform |
| R-11 | External provider outage/rate change | 5 | 3 | 15 | adapters, cache, circuit breaker, multi-provider degradation | Platform |
| R-12 | Model provider cost/price instability | 4 | 3 | 12 | model gateway, routing, cost ledger, budgets, private alternatives | Platform/product |
| R-13 | Parsing accuracy varies by publisher/domain | 5 | 4 | 20 | quality grades, launch scope, fixtures, repair, alternate parser path | Parsing |
| R-14 | Users trust summaries without opening evidence | 4 | 4 | 16 | evidence-first layout, source-open affordance, UX study | Product/design |
| R-15 | Product perceived as generic PDF chatbot | 3 | 4 | 12 | focused positioning and demo around evidence trace | Product/GTM |
| R-16 | Gold set too small/biased | 4 | 4 | 16 | sampling matrix, dual annotation, domain slices, versioning | Research |
| R-17 | Human annotation expensive/inconsistent | 4 | 3 | 12 | clear handbook, tooling, agreement metrics, adjudication | Research/ops |
| R-18 | Recursive lineage causes runaway cost/complexity | 4 | 3 | 12 | depth/fan-out budgets, priority, early exit | Platform/product |
| R-19 | Graph edges imply certainty without evidence | 3 | 4 | 12 | evidence-backed edge requirement, attributed styling | Product/ML |
| R-20 | Deletion incomplete across derived artifacts/backups | 3 | 5 | 15 | provenance graph, deletion workflow/receipt, restore tests | Security/platform |
| R-21 | Dependency vulnerability or parser regression | 4 | 4 | 16 | lockfiles, SBOM, staged upgrades, regression suite | Platform |
| R-22 | Users interpret mismatch as misconduct accusation | 3 | 4 | 12 | neutral technical copy and disclaimers | Product/domain |
| R-23 | Current APIs or data terms change | 5 | 3 | 15 | dated source register, adapter config, contract monitoring | Platform/legal |
| R-24 | Early build becomes microservice-heavy and stalls | 3 | 4 | 12 | modular monolith ADR and split criteria | Engineering lead |
| R-25 | No clear willingness to pay | 3 | 5 | 15 | wedge interviews, paid lab beta, value metrics | Product/GTM |

---

## 2. Critical risk response details

### R-01 Wrong work/version

**Detection:** low candidate margin, provider disagreement, user correction, DOI conflict.  
**Prevention:** exact identifier validation, feature-level score, thresholds, version model.  
**Fallback:** `ambiguous_reference`; user confirmation.  
**Release metric:** top-1 and ambiguity precision per domain.

### R-02 Fabricated quote

**Detection:** exact substring/checksum and asset-bound validation.  
**Prevention:** models return span coordinates/IDs, not free-form quotes alone.  
**Response:** block evidence card, disable affected route if systemic.  
**Tolerance:** zero in blocking suite.

### R-04 Relation error

**Detection:** gold-set confusion matrix, user correction, verifier disagreement.  
**Prevention:** scope extraction, counterevidence, comparable-condition rule.  
**Fallback:** `insufficient_evidence` or human review.  
**Communication:** never present as universal truth score.

### R-07 Copyright/provider terms

**Detection:** acquisition path audit and license/provenance gap.  
**Prevention:** approved adapters/hosts, no browser session/cookie forwarding, legal source registry.  
**Fallback:** metadata/abstract-only or user-authorized upload.  
**Response:** disable route and review affected cached assets.

### R-09 Prompt injection

**Detection:** adversarial suite, model output policy flags, unexpected tool requests.  
**Prevention:** paper text as untrusted data, no direct tools, typed operations and policy engine.  
**Fallback:** reject output or abstain.  
**Response:** rotate credentials only if exposure occurred; add blocking case.

### R-10 Cross-tenant leakage

**Detection:** RLS/auth tests, anomalous access logs, user report.  
**Prevention:** tenant context at every layer, no cross-tenant private dedup.  
**Response:** Sev 0 incident process.

---

## 3. Product assumption risks

| Assumption | Validation test | Failure response |
|---|---|---|
| Users value exact source evidence | measure source opens, task interviews | emphasize proof/reading workflow or revisit wedge |
| Enough cited sources are lawfully accessible | sample target-domain papers | make user-linked source flow central and narrow claims |
| Transformation analysis is useful | implementation-mode study | defer graph depth, focus on claim verification |
| Explicit abstention increases trust | A/B qualitative comprehension study | improve recovery actions/copy, not lower thresholds blindly |
| Labs will collaborate/correct | paid design-partner trial | prioritize individual workflow if team loop is weak |

---

## 4. Risk acceptance rules

- zero-tolerance security/quote/provenance risks cannot be accepted by ordinary product trade-off,
- legal source-access exceptions require legal and security approval,
- quality thresholds can be narrowed by declaring a smaller supported scope, not by hiding failures,
- accepted risks have an owner, review date, monitoring signal and explicit rationale,
- stale risks are reviewed at every milestone gate.
