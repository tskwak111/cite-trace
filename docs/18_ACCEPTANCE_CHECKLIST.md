# CiteTrace Acceptance & Handoff Checklist

> **Version:** 1.0.0  
> **Usage:** Mark only with evidence such as test output, evaluation report, review record or deployed behavior.

---

## 1. Product scope

- [ ] One-sentence product promise matches the master blueprint.
- [ ] Initial supported document/domain scope is visible to users.
- [ ] Generic PDF-chat features have not displaced the citation-evidence core.
- [ ] Each active feature maps to a persona, job and measurable acceptance criterion.
- [ ] Non-goals and anti-features remain enforced.

## 2. Ingestion and parsing

- [ ] MIME, magic bytes, size, pages, encryption and malicious-content checks pass.
- [ ] Parser runs in isolated resource-limited environment.
- [ ] Source asset checksum, tenant, access and retention are recorded.
- [ ] Sections, bibliography and in-text anchors are extracted.
- [ ] Numeric and author–year fixtures pass.
- [ ] Citation clusters are represented as separate targets.
- [ ] Parse quality grade and limitations are user-visible.
- [ ] Coordinates/open-in-source behavior is verified on supported fixtures.

## 3. Reference resolution

- [ ] Identifiers are normalized and validated.
- [ ] Provider candidates and feature scores are retained.
- [ ] Work and work version are separate.
- [ ] Absolute score and margin thresholds are configured and calibrated.
- [ ] Ambiguous cases abstain and support user confirmation.
- [ ] Wrong-paper corrections create immutable events and rerun paths.
- [ ] Resolution evaluation targets are met for the declared launch scope.

## 4. Source acquisition

- [ ] Only approved lawful/user-authorized paths exist.
- [ ] SSRF controls pass adversarial tests.
- [ ] Redirects, content length/type and security scans are enforced.
- [ ] Access level, license/source URL, timestamp and checksum are stored.
- [ ] No paywall/login/CAPTCHA bypass is implemented.
- [ ] Abstract-only and inaccessible states are accurate and visible.
- [ ] Provider outage and rate-limit behavior is graceful.

## 5. Claim and evidence

- [ ] Atomic claim spans map exactly to citing context.
- [ ] Qualifiers, negation and target associations are retained.
- [ ] Source chunks preserve section/page/offset/coordinate provenance.
- [ ] Hybrid retrieval and reranking are tested offline.
- [ ] Counterevidence search runs for configured assertive cases.
- [ ] Displayed evidence is an exact validated source substring.
- [ ] Composite evidence shows separate spans.
- [ ] No-relevant-evidence produces a truthful limited result.

## 6. Relation and transformation

- [ ] Citation intents conform to taxonomy version.
- [ ] Relation verifier compares structured scope dimensions.
- [ ] Contradiction requires comparable scope.
- [ ] Metadata-only content cannot produce direct support.
- [ ] Transformation labels require paired evidence or qualified attribution.
- [ ] Confidence vector uses calibrated features, not model self-report alone.
- [ ] Abstention thresholds and reasons are versioned.
- [ ] Gold-set metrics meet the declared release gate.

## 7. Explanation and UX

- [ ] Quotes, paraphrases and inferences are visually and semantically distinct.
- [ ] Every material explanation statement maps to accepted spans or is marked inference.
- [ ] Evidence card contains current claim, source, evidence, relation, transformation, confidence, access and feedback.
- [ ] User can open exact source region.
- [ ] Citation clusters do not imply identical roles.
- [ ] Beginner mode preserves evidence and uncertainty.
- [ ] Review mode does not issue paper accept/reject verdicts.
- [ ] Keyboard, screen-reader and non-color state tests pass.
- [ ] Empty/limited/error copy is accurate and actionable.

## 8. Data and provenance

- [ ] Work, version, source asset and parsed version are distinct.
- [ ] Evidence links retain model/prompt/parser/taxonomy versions.
- [ ] Source span offsets/checksums validate.
- [ ] Supersession history is append-only and cycle-free.
- [ ] Private derived data inherits workspace policy.
- [ ] User corrections preserve before/after and actor.
- [ ] Exports preserve access and provenance disclosures.

## 9. Security and privacy

- [ ] Cross-tenant authorization and RLS suites pass.
- [ ] Private objects use tenant-scoped keys and short-lived access.
- [ ] Raw document text is absent from default logs/traces.
- [ ] Model data-transmission policy is enforced and visible.
- [ ] Prompt-injection red-team suite passes.
- [ ] Secrets are absent from prompts, repositories and outputs.
- [ ] Deletion revokes access immediately and completes with status/receipt.
- [ ] Sharing/export applies the strictest source policy.
- [ ] Dependency/SBOM/security review passes.

## 10. Reliability and operations

- [ ] API commands are idempotent.
- [ ] Stage handlers are retryable and resumable from checkpoints.
- [ ] Redis is not the sole source of truth.
- [ ] Provider/model timeouts, retries, circuits and quotas exist.
- [ ] High-priority citation work is isolated from background fan-out.
- [ ] Traces propagate through API, queue, provider/model and database.
- [ ] Stage, dependency, quality and cost dashboards exist.
- [ ] Backups and restores are tested.
- [ ] Critical runbooks and incident drill are complete.
- [ ] Cost per verified evidence link is measurable.

## 11. Evaluation and release

- [ ] Gold-set assets and versions are locked.
- [ ] Critical fields have dual annotation/adjudication.
- [ ] Domain and failure slices have minimum sample sizes.
- [ ] Fast, main and release suites are defined.
- [ ] Fabricated displayed quote count is zero in blocking suite.
- [ ] No source/provenance/security blocker exists.
- [ ] New prompt/model/parser route beats or safely trades against baseline.
- [ ] Human UX study confirms uncertainty interpretation.
- [ ] Rollback route and prior version remain available.

## 12. Commercial readiness

- [ ] Source/provider terms and attribution are documented.
- [ ] Copyright/privacy legal review covers target launch markets and customers.
- [ ] Product messaging avoids unsupported universal claims.
- [ ] Pricing units are understandable and cost-aware.
- [ ] Support and incident ownership is assigned.
- [ ] Beta workspace agreements describe data/model/source behavior.
