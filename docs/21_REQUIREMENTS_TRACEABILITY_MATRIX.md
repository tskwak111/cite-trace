# CiteTrace Requirements Traceability Matrix

> **Baseline:** PRD 1.0.0, implementation plans dated 2026-08-28  
> **Purpose:** Ensure every approved requirement has an implementation owner, contract surface and verification evidence before release.

## Plan key

| Key | Plan |
|---|---|
| `F` | Foundation & ingestion |
| `R` | Reference resolution & source acquisition |
| `E` | Evidence engine |
| `P` | Reader, quality & production |

`F2` means Task 2 in `2026-08-28-citetrace-foundation-ingestion.md`; the same rule applies to the other plans.

## Functional requirements

| Requirement | Primary implementation tasks | Contract / persistence surface | Blocking verification evidence |
|---|---|---|---|
| FR-101 PDF/URL intake | F2, F3, R5–R6 | upload/document API, `source_asset` | upload API, immutable checksum and remote-intake integration tests |
| FR-102 file policy checks | F2 | source policy, quarantine record | MIME/magic/encryption/page/size/malware rejection tests; parser not called |
| FR-103 ownership/retention | F1–F3, P9 | workspace RLS, object key, retention profile | cross-tenant DB/object tests and retention-policy tests |
| FR-104 duplicate handling | F2–F3 | `(workspace_id, sha256)` uniqueness | same-tenant reuse and cross-tenant non-reuse tests |
| FR-105 cancellation | F6, P2 | analysis state/events | queued/running cancellation and no-new-fan-out tests |
| FR-201 structured extraction | F4–F5 | parsed document/node/reference/anchor tables | numeric and author-year fixture assertions |
| FR-202 coordinates | F5, P4 | document/source span coordinates | coordinate coverage and open-exact-region browser tests |
| FR-203 citation styles | F5 | citation cluster/anchor model | numeric, author-year and mixed-style regression suite |
| FR-204 multi-citation clusters | F5, E2, E5 | claim-target association | per-target judgment tests with shared context |
| FR-205 parse quality grade | F5, P1 | parsed quality grade/features, limitation | poor-layout fixture and user-visible capability gating tests |
| FR-301 identifier normalization | R1, R3 | bibliographic query/identifier contracts | DOI/arXiv/PMID canonicalization and malformed-ID tests |
| FR-302 provider adapters | R1–R2 | provider candidate/provenance | recorded contract tests, paging, rate-limit and timestamp tests |
| FR-303 candidate ranking | R3 | feature score and resolution records | golden matcher, hard-conflict and deterministic tie tests |
| FR-304 work/version separation | R4, R6 | `scholarly_work`, `work_version`, `source_asset` | preprint/publisher/accepted-manuscript identity tests |
| FR-305 resolution abstention | R3 | threshold profile and resolution status | absolute-score/margin boundary and ambiguous-case tests |
| FR-306 user correction | R4, P5 | immutable correction/feedback events | wrong-paper correction, actor/history and rerun-target tests |
| FR-401 lawful full text | R5–R6 | access decision and source provenance | approved-location, license/access and checksum tests |
| FR-402 abstract/metadata fallback | R6–R7, P1/P4 | access level, abstention, limitation | abstract-only/metadata-only API and UI honesty tests |
| FR-403 no paywall bypass | R5–R6, P9 | source policy and audit | blocked-login/CAPTCHA/paywall paths and red-team audit |
| FR-404 immutable source versions | F2, R6 | source checksum/version | byte-change creates new asset; historical analysis remains pinned |
| FR-405 risky remote quarantine | F2, R5–R6 | remote fetch and quarantine state | SSRF/content-type/decompression/malware tests |
| FR-501 citation context | E2 | citing context window artifact | sentence/neighbors/heading and section-boundary tests |
| FR-502 atomic claims | E2 | `citing_claim` | exact span, conjunction split and non-claim citation tests |
| FR-503 claim-to-cluster targets | E2, E5 | claim-target records | one-to-many, uncertain association and per-target publication tests |
| FR-504 qualifiers | E2, E5 | qualifiers and structured scope | negation, hedge, population, metric, time and condition fixtures |
| FR-601 section-aware chunks | E3 | `source_chunk` | heading/page/offset/coordinate round-trip tests |
| FR-602 hybrid retrieval | E3–E4 | lexical/vector candidate features | deterministic offline ranking and filter-first tests |
| FR-603 reranking | E4 | reranker score/version | top-k quality and model-version provenance tests |
| FR-604 non-paragraph evidence | E3–E4 | evidence type and descriptors | caption/table/equation/algorithm/appendix fixture tests |
| FR-605 exact spans | E4, E7 | `source_span`, quote hash | fabricated, altered, Unicode and out-of-bounds quote blockers |
| FR-606 counterevidence | E4–E5 | contrast candidate role | strong-claim counter-query and false-contradiction tests |
| FR-701 citation intent | E5 | closed taxonomy | multi-label macro-F1 and taxonomy/schema drift checks |
| FR-702 relation/scope | E5 | relation and scope observations | direct/partial/indirect/contradiction/scope slice metrics |
| FR-703 transformation/lineage | E6 | transformation labels/paired spans | paired-evidence and unsupported-transformation blocker tests |
| FR-704 stage confidence | E6, P1/P4 | confidence vector/profile | calibration, weakest-link cap and explanation UI tests |
| FR-705 policy abstention | R7, E5–E7, P4 | abstention and limitation | inaccessible/ambiguous/no-evidence/insufficient-evidence tests |
| FR-706 mode-relative priority | E8, P1/P4 | reference priority read model | same-reference/different-mode and no-prestige-shortcut tests |
| FR-801 relationship summary | E7 | grounded statements | current-paper relevance and supporting-record tests |
| FR-802 beginner explanation | E7, P4 | audience-specific statements | terminology/prerequisite/analogy-label tests |
| FR-803 expert explanation | E7, P4 | audience-specific statements | concise paired technical comparison tests |
| FR-804 no unsupported prose | E7, P10 | explanation/audit records | statement support coverage and release blocker |
| FR-805 reading recommendation | E8, P1/P4 | priority reasons and sections | reason-code, section-source and access-aware action tests |
| FR-901 clickable citations | P3–P4, P7 | reader state/source locator | pointer, keyboard and selected-state tests |
| FR-902 complete evidence card | P1, P4 | EvidenceLink/read model | contract snapshot and ten-block UI tests |
| FR-903 exact source navigation | P4 | source locator/coordinates | page/section/span and transform/browser tests |
| FR-904 progress/partial results | P2–P3 | durable events/SSE | reconnect, replay, duplicate and unfinished-state tests |
| FR-905 filters/grouping | P1, P3–P4 | paginated read API | intent/relation/priority/access/confidence filter tests |
| FR-906 inspectable lineage graph | P4 | evidence-backed graph edges | edge-to-evidence navigation and no-decorative-edge tests |
| FR-1001 feedback taxonomy | P5 | feedback schema/enum | category/verdict contract and drift tests |
| FR-1002 correction detail | R4, P5 | immutable event/adjudication | actor, target/span/label, history and rerun tests |
| FR-1003 private notes | P6 | note versions and visibility policy | author/workspace role, sanitization and cross-tenant tests |
| FR-1004 export | P6 | export job/artifact/schema | provenance, source restriction, checksum and expiry tests |
| FR-1005 share | P6, P9 | token hash/policy/expiry/revocation | revocation, current-policy recheck and no-private-byte tests |
| FR-1101 idempotent jobs | F6, E9, P2 | idempotency record/state | replay/conflict/redelivery tests |
| FR-1102 resumable stages | F6, E9 | stage runs/checkpoints | crash-after-side-effect and restart tests |
| FR-1103 provider degradation | R2/R7, P2/P8 | typed provider/analysis limitation | timeout/429/circuit/open and partial-completion tests |
| FR-1104 audit trail | F6, R6, E7/E9, P5/P8 | outbox/model/access/feedback/audit records | trace/provenance completeness and redaction tests |
| FR-1105 deletion | P9 | deletion job/receipt/retention state | immediate revoke, derived-artifact cleanup and backup-boundary tests |

## Non-functional requirements

| Requirement | Primary tasks | Release evidence |
|---|---|---|
| NFR-1 Trustworthiness | E4–E7, E9, P10 | zero fabricated displayed quotes; evidence-required relation; access-level disclosure; localizable uncertainty |
| NFR-2 Security/privacy | F1–F2, R5–R6, E1/E7, P6/P9/P11 | RLS/object isolation, SSRF, prompt-injection, secret/log redaction, model data routing, deletion tests |
| NFR-3 Performance | P1–P4, P8, P11 | p95 read benchmark, shell-first rendering, priority-citation scheduling, concurrency/backpressure load tests |
| NFR-4 Reliability | F6, R2/R7, E1/E9, P2/P8/P11 | durable/idempotent state, bounded dependency policies, typed schema failure, checkpoint restore and chaos tests |
| NFR-5 Accessibility | P4, P7 | WCAG 2.2 AA audit, keyboard/screen-reader, non-color semantics, structured-text alternative and focus stability |
| NFR-6 Maintainability | F/R/E/P all plans | typed adapters, versioned artifacts, public contract tests, ADR enforcement and modular-monolith dependency rules |

## Release usage

A requirement is not marked complete because code exists. It is complete only when:

1. the relevant contract and migration are reviewed,
2. the listed automated evidence passes in CI,
3. applicable gold-set or red-team gates pass,
4. security/source-policy impact is approved,
5. the user-visible behavior is demonstrated in the supported scope,
6. rollback and supersession behavior are recorded.

Any PRD change must update this matrix in the same pull request. Any implementation task that cannot identify a PRD/NFR/risk/operational reason should be challenged as possible scope creep.
