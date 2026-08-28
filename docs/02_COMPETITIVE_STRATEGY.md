# CiteTrace Competitive Strategy

> **Version:** 1.0.0  
> **Date:** 2026-08-28  
> **Purpose:** Define where to compete, where not to compete, and how to build a durable advantage.

---

## 1. Strategic thesis

The scholarly-tool market already contains strong products for paper search, chat-with-PDF, literature review, citation graphs, and citation-context classification. CiteTrace should not win by adding more generic features to that list.

It should own one high-friction moment:

> **“I see this citation in a paper. Show me exactly what the source says, whether it supports this claim, and what changed.”**

This moment is frequent, expensive, difficult to automate reliably, and directly tied to research understanding and trust.

---

## 2. Competitive capability map

| Capability | Search/review tools | PDF chat tools | Citation graph tools | Citation-context tools | CiteTrace target |
|---|---:|---:|---:|---:|---:|
| Find papers | Strong | Medium | Medium | Medium | Adequate, context-led |
| Summarize one paper | Strong | Strong | Weak | Medium | Relationship-centered |
| Build citation graph | Medium | Weak | Strong | Medium | Typed lineage graph |
| Show citation context | Medium | Medium | Medium | Strong | Strong |
| Locate exact source evidence | Limited/varies | Usually current PDF only | Weak | Medium | Core |
| Compare claim scope | Limited | Limited | Weak | Medium | Core |
| Explain adoption/change | Limited | Limited | Weak | Limited | Core |
| Expose asset/version/access | Varies | Varies | Varies | Varies | Mandatory |
| Stage-level confidence | Rare | Rare | Rare | Rare | Mandatory |
| Productive abstention | Rare | Rare | N/A | Varies | Core |

---

## 3. Positioning

### 3.1 External positioning

> CiteTrace turns every citation in a paper into an inspectable evidence trail.

### 3.2 Avoided positioning

- “AI that reads every paper for you”
- “The only research tool you need”
- “Automatically proves whether a paper is true”
- “Replaces literature review or peer review”
- “Unlimited access to any paper”

These claims create legal, scientific and trust liabilities and weaken product clarity.

### 3.3 Category entry wedge

Start with:

- AI/CS and life-science students/researchers who already read PDFs digitally,
- method-heavy papers where references are direct implementation dependencies,
- users who feel the cost of opening many references,
- papers with accessible cited versions or user-supplied source PDFs.

This wedge produces frequent, demonstrable value before expanding to institution-wide literature workflows.

---

## 4. Differentiation ladder

### Level 1 — Commodity

- extract references
- search metadata
- one-paragraph summaries
- citation graph

Necessary, but not a reason to switch.

### Level 2 — Useful

- citation intent
- relevant source section
- reading priority
- beginner explanation

Creates value, but remains replicable.

### Level 3 — Defensible product

- exact claim-to-evidence spans
- support/contradiction/scope relation
- paired transformation analysis
- asset/version/license provenance
- calibrated abstention
- structured expert correction loop

### Level 4 — Long-term moat

- large adjudicated citation-evidence dataset
- research transformation graph across versions and fields
- domain-specific verifier performance
- integration into research-team reading, implementation and review workflows
- trust brand supported by measurable quote and grounding guarantees

---

## 5. Build / integrate / avoid

| Area | Decision | Reason |
|---|---|---|
| PDF structure parsing | Integrate GROBID; add validation/normalization | mature specialist infrastructure |
| Scholarly metadata | Integrate multiple official/open providers | expensive and unnecessary to recreate |
| OA discovery | Integrate lawful discovery providers/repositories | legal provenance matters |
| Evidence retrieval | Build | central quality and product IP |
| Relation verification | Build and evaluate | core differentiation |
| Transformation graph | Build | strategic data asset |
| Generic LLM chat | Minimal | distracts from evidence experience |
| Citation manager | Integrate later | crowded workflow, not initial wedge |
| Full-text piracy/scraping | Avoid | legal and trust risk |
| Journal/author quality score | Avoid | scientifically contentious and off-mission |

---

## 6. Anti-features

Features deliberately excluded from the default experience:

1. **Uncited answer mode:** the system does not hide source links behind optional toggles.
2. **One-number truth score:** scientific claims are not reduced to a universal truth probability.
3. **Automatic misconduct accusation:** mismatch is described technically, not framed as wrongdoing.
4. **Citation-count prestige ranking:** importance means relevance to the current paper, not global status.
5. **Infinite recursive crawling:** depth and budget are controlled to prevent cost and cognitive explosion.
6. **Silent source substitution:** analysis never swaps arXiv, conference and journal versions without disclosure.
7. **Paywall bypass button:** inaccessible content remains inaccessible until lawfully supplied.
8. **Raw chain-of-thought display:** show concise evidence-based rationale and decision factors, not hidden internal reasoning.

---

## 7. Moat-building data strategy

### 7.1 High-value correction events

Capture corrections as structured records:

- selected work is wrong
- source version is wrong
- evidence span is wrong or incomplete
- intent label is wrong
- relation label is wrong
- scope dimension is missing
- transformation is wrong
- explanation overstates evidence

Each event should retain before/after values, reviewer role, confidence, and adjudication status.

### 7.2 Data quality hierarchy

1. adjudicated expert cases
2. agreement between two trained annotators
3. verified user correction with source span
4. normal user feedback
5. implicit behavior signals

Do not train critical relation models directly from clicks or unverified thumbs-up.

### 7.3 Network effects

The useful network effect is not public social activity. It is:

- more corrected reference identities,
- more verified evidence spans,
- better domain-specific scope patterns,
- richer transformation edges,
- more reliable calibration.

Private customer data must not be pooled without explicit rights and policy.

---

## 8. Distribution strategy

### 8.1 Individual adoption

- frictionless PDF upload
- arXiv URL import
- shareable evidence card with lawful excerpt policy
- Zotero/browser integration after core reliability
- student/research-lab onboarding templates

### 8.2 Team adoption

- shared reading queue
- correction and review workflow
- private notes
- export to Markdown/Notion-compatible formats
- audit trail for R&D and review teams

### 8.3 Institutional adoption

- SSO, data retention and regional deployment
- library proxy/link resolver integrations only through authorized mechanisms
- private corpus and on-prem/private-cloud options
- legal/source policy controls by institution

---

## 9. Pricing hypotheses

Pricing is a hypothesis to test, not a fixed commitment.

| Tier | Core value | Likely limiter |
|---|---|---|
| Free | Experience one or several papers | documents/month, priority references, retention |
| Student/Individual | Regular reading and implementation | monthly analyses and advanced modes |
| Research Lab | Shared workspace and higher limits | seats, storage, concurrent jobs |
| Enterprise/R&D | governance, private deployment, audit | annual contract and capacity |

Avoid token-like pricing in user-facing copy. Users understand papers, priority references, storage and team seats better than model tokens.

---

## 10. Strategic tests

Before large-scale build, validate:

1. Do users open exact source evidence, or only read generated explanations?
2. Is the highest-value mode understanding, implementation, or review?
3. What fraction of cited sources can be lawfully acquired without user upload in the launch domains?
4. How often does transformation analysis change the user's understanding?
5. Does explicit abstention increase trust or create excessive frustration?
6. Which errors cause immediate abandonment: wrong paper, wrong quote, wrong relation, or slow processing?
7. Will research labs pay for shared correction/provenance rather than only individual summaries?

---

## 11. Strategic success conditions

CiteTrace has product-market evidence when:

- users repeatedly analyze papers without being prompted,
- source evidence opens are common rather than exceptional,
- users save and revisit reference trails,
- corrections improve later runs measurably,
- teams share evidence cards as part of real research work,
- willingness to pay correlates with trust and workflow depth, not only output volume.
