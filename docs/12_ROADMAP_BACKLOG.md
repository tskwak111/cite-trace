# CiteTrace Roadmap & Backlog

> **Version:** 1.0.0  
> **Planning rule:** Vertical slices must end in working, inspectable software.  
> **No calendar promise:** Sequence is fixed by dependency and risk; team capacity determines timing.

---

## 1. Roadmap principles

1. Prove the evidence invariant with one citation before whole-paper automation.
2. Build evaluation and provenance before optimizing model sophistication.
3. Integrate only lawful source paths.
4. Make limited/abstained results usable from the first slice.
5. Do not build collaboration, billing or broad graph features ahead of core evidence quality.

---

## 2. Milestone M0 — Contract and quality foundation

### Outcome

A runnable repository with stable domain types, API/event/schema contracts, source policy, evaluation fixtures and CI.

### Scope

- repository/tooling and local dependencies
- analysis status state machine
- source asset and evidence data contracts
- exact quote validation utility
- taxonomy files
- synthetic evaluation cases
- security and provider adapter protocols
- observability IDs and safe logging rules

### Exit gate

- scaffold and tests pass from clean checkout
- public contracts validate
- quote/provenance invariant tests pass
- no external live credentials required
- architecture and source-policy ADRs accepted

---

## 3. Milestone M1 — One uploaded paper, parsed citations

### Outcome

Upload a supported PDF and see structured text, bibliography and clickable citation anchors.

### Scope

- secure upload metadata flow
- object storage registration
- GROBID adapter and sandbox boundary
- TEI normalization
- numeric and author–year fixtures
- parse quality grade
- reader shell with citation states

### Exit gate

- citation anchor precision/recall targets met on M1 evaluation set
- citation cluster and unmatched-reference states shown
- low-quality documents enter limited/unsupported state
- no raw private text in logs

---

## 4. Milestone M2 — One citation, user-supplied source, exact evidence

### Outcome

The user links a cited-source PDF and receives an exact evidence span for one citation claim.

### Scope

- reference entry and manual identity confirmation
- cited source upload/association
- source parsing and chunking
- atomic claim extraction
- hybrid retrieval
- exact span validator
- basic evidence card and “open in source”
- no-relevant-evidence abstention

### Exit gate

- displayed quote fabricated rate is zero on blocking suite
- Recall@5 target approached/met on selected supported cases
- source asset/version/access visible
- user can correct evidence span

---

## 5. Milestone M3 — Automated reference resolution and lawful acquisition

### Outcome

Most supported references are matched and accessible OA versions are acquired automatically when lawful.

### Scope

- Crossref/OpenAlex/Semantic Scholar metadata adapters
- transparent candidate scoring
- ambiguity UI
- Unpaywall/arXiv/PMC or approved repository acquisition
- SSRF-safe fetch pipeline
- provider cache, rate limits and circuit breakers
- version relationship model

### Exit gate

- top-1 resolution accuracy target on supported slice
- ambiguity precision target
- no paywall bypass path
- provider outage degrades visibly
- every acquired asset has provenance, checksum and access level

---

## 6. Milestone M4 — Relation, scope and citation intent

### Outcome

Evidence cards classify why the source is cited and whether the source supports the claim at the stated scope.

### Scope

- multi-label intent
- source proposition/scope extraction
- relation verifier
- counterevidence search
- confidence vector and calibration
- abstention policy
- explanation statement grounding
- quality auditor

### Exit gate

- relation macro-F1 target or narrower supported-domain gate met
- direct support never based on metadata-only content
- scope mismatch and contradiction rules pass adversarial cases
- unsupported statement rate target met
- UI users distinguish relation from confidence

---

## 7. Milestone M5 — Transformation and implementation mode

### Outcome

Users can see what the current paper adopted, changed or extended and build a reproduction-oriented reading queue.

### Scope

- paired source/citing method spans
- transformation labels
- method/dataset/metric/tool dependency extraction
- implementation mode
- source section recommendations
- verified resource links
- transformation lineage edges

### Exit gate

- transformation edges have paired evidence or qualified attribution
- unsupported transformation claim rate within gate
- implementation-mode user study shows correct dependency understanding

---

## 8. Milestone M6 — Whole-paper analysis and lineage

### Outcome

Analyze a full supported paper asynchronously, prioritize references and explore controlled-depth lineage.

### Scope

- reference importance scoring by mode
- per-citation incremental completion
- high/normal/low priority queues
- depth-1/2 lineage expansion with budgets
- reference map and graph/list alternatives
- reading queue and Markdown/JSON export

### Exit gate

- large supported documents remain within cost/fan-out budget
- graph edges are inspectable
- partial provider/source failures do not destroy completed cards
- exports preserve provenance and access disclosure

---

## 9. Milestone M7 — Team beta and production trust

### Outcome

Research labs can collaborate safely with measurable quality and operational reliability.

### Scope

- workspace roles and private notes
- structured correction/adjudication
- SSO-ready identity boundary
- retention and deletion controls
- production dashboards/SLOs
- 300+ adjudicated gold cases
- release comparison and rollback
- institutional source-policy controls

### Exit gate

- security/privacy/copyright review complete
- RLS and deletion tests pass
- release quality gates automated
- incident and provider/model outage drills complete
- beta teams demonstrate repeat usage and trust

---

## 10. Deferred expansion backlog

Prioritize only after M7 evidence:

- multilingual parsing and models
- OCR/scanned papers
- full table/figure reasoning
- books, theses, patents and standards
- browser extension
- Zotero and reference-manager sync
- private institutional corpus search
- authoring-time citation verification
- review-management integrations
- on-prem/private-cloud distribution
- domain-specialized verifier packs

---

## 11. Backlog by capability

### Parsing

- numeric/author–year styles
- nested citation marker edge cases
- footnote/endnote citations
- supplement/appendix linkage
- table/figure in-text references
- parser ensemble or repair rules

### Resolution

- DOI/arXiv/PMID normalization
- title transliteration and punctuation normalization
- version linking
- duplicate work merge/split workflow
- retraction/correction notice ingestion

### Retrieval

- structural chunking
- hybrid search
- query expansion
- counterevidence retrieval
- table/figure indexing
- source version diff

### Verification

- intent classifier
- scope extraction
- relation verifier
- transformation comparison
- confidence calibration
- disagreement and human-review routing

### Product

- reader shell
- evidence card
- reference map
- lineage graph
- beginner/implement/review modes
- feedback and exports

### Platform

- tenant/RLS
- queue/checkpoints
- provider/model gateways
- observability/cost
- security sandbox
- retention/deletion

---

## 12. Prioritization score

Use a decision score, not as an automatic truth:

```text
Priority =
  0.30 * CorePromiseImpact
+ 0.20 * TrustRiskReduction
+ 0.15 * UserFrequency
+ 0.15 * LearningValue
+ 0.10 * RevenueEnablement
+ 0.10 * DependencyUnlock
- 0.15 * ComplexityRisk
```

Security, privacy and legal blockers override the score.

---

## 13. Scope control rules

A feature enters active implementation only if:

- the user problem and target persona are named,
- success and failure behavior are testable,
- provenance/access implications are defined,
- quality evaluation case exists or is created first,
- it fits the current milestone exit gate,
- it does not introduce an unreviewed external data route.
