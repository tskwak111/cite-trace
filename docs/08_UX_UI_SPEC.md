# CiteTrace UX/UI Specification

> **Version:** 1.0.0  
> **Primary experience:** Evidence-first paper reader

---

## 1. UX objectives

The interface must help users:

1. inspect evidence faster than manually opening references,
2. understand why a citation matters without hiding the original source,
3. distinguish verified facts, model inferences and access limitations,
4. prioritize where human attention is needed,
5. learn domain concepts without mistaking simplified explanations for source text.

The product should feel like a **research instrument**, not an omniscient chatbot.

---

## 2. Information architecture

```text
Workspace
├── Library
│   ├── Papers
│   ├── Reading queues
│   └── Exports
├── Paper workspace
│   ├── Reader
│   ├── References
│   ├── Lineage graph
│   ├── Notes
│   └── Analysis history
├── Review queue
└── Settings
    ├── Data & retention
    ├── Source access
    ├── Model/privacy
    └── Team & roles
```

---

## 3. Main reader layout

### Desktop

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ ← Library | Paper title | Mode: Understand | Analysis state | actions      │
├─────────────────────────────┬──────────────────────────────┬───────────────┤
│                             │                              │               │
│ Paper viewer                │ Evidence panel               │ Reference map │
│                             │                              │               │
│ Text/PDF toggle             │ Current claim                │ Filters       │
│ Citation anchors            │ Why cited                    │ Priority list │
│ Evidence highlights         │ Exact source evidence        │ Groups        │
│ Page navigation             │ Relation & scope             │ Mini lineage  │
│                             │ Adopted / changed             │               │
│                             │ Confidence / limitations      │               │
│                             │ Feedback                      │               │
├─────────────────────────────┴──────────────────────────────┴───────────────┤
│ Stage progress / errors / source-access disclosures                       │
└────────────────────────────────────────────────────────────────────────────┘
```

Recommended responsive behavior:

- ≥ 1440px: three panes
- 1024–1439px: reader + evidence; reference map as drawer
- < 1024px: single pane with persistent tabs; preserve source/claim comparison via stacked card

---

## 4. Citation anchor interaction

### Visual states

- unprocessed
- queued
- analyzing
- verified
- limited
- review required
- error
- selected

Never convey states by color alone. Use icons, labels and accessible descriptions.

### Keyboard behavior

- `Tab` focuses citation anchors in document order
- `Enter`/`Space` opens evidence panel
- `[` and `]` navigate previous/next citation when focus is in reader mode
- `Esc` closes drawers without losing document position
- screen reader label: “Citation 12, method adoption, verified, opens evidence details”

### Citation cluster

For `[3–7]`, opening the cluster displays each reference as a subtab with shared claim context. The interface must not imply each source has the same role or relation.

---

## 5. Evidence card anatomy

### Block 1 — Current claim

- exact citing sentence/claim
- surrounding context expandable
- citation marker highlighted
- section and page
- “AI-separated atomic claim” badge when claim is extracted from a longer sentence

### Block 2 — Why it is cited

Show multi-label chips with a plain explanation:

```text
Method adoption · The current paper says it follows this source's training procedure.
```

### Block 3 — Resolved source

- title, authors, year, venue
- DOI/arXiv/PMID
- analyzed version badge
- version alternatives
- resolution confidence and candidate-review action

### Block 4 — Exact source evidence

- verbatim excerpt
- page and section
- evidence type
- “Open in source”
- additional and limiting evidence tabs
- access badge: full text / repository manuscript / abstract only

Quotes are visually distinct from generated explanation.

### Block 5 — Relationship judgment

Example:

```text
Scope mismatch
The source reports results on two image datasets with 10% labels.
The current sentence generalizes to limited-label settings without naming that scope.
```

### Block 6 — Adopted and changed

Two-column comparison:

| From source | In current paper |
|---|---|
| contrastive objective | retained |
| image encoder | replaced by time-series encoder |
| no temporal regularizer | temporal consistency added |

Each row opens paired spans.

### Block 7 — Explanation levels

Tabs:

- Quick
- Detailed
- Beginner
- Implementation

Beginner text includes prerequisites and analogies but is marked as explanation, never as a quote.

### Block 8 — Confidence and limitations

Default display:

```text
Overall: Review recommended
Weakest stage: Relation verification
Reason: The source result is narrow and the citing claim is linguistically broad.
```

Expandable stage table:

| Stage | Status | Score | Reason |
|---|---|---:|---|
| PDF parsing | High | 0.99 | anchor and coordinates aligned |
| Paper identity | High | 0.96 | DOI and provider agreement |
| Source access | Full | 1.00 | OA full text analyzed |
| Evidence retrieval | High | 0.91 | stable top span |
| Relation | Medium | 0.84 | scope language requires interpretation |
| Explanation | High | 1.00 | all material statements linked |

### Block 9 — Reading recommendation

- importance to current paper
- recommended source sections
- estimated conceptual prerequisites, not time estimate
- save to reading queue

### Block 10 — Feedback

Primary actions:

- Correct
- Wrong paper
- Wrong evidence
- Wrong relation
- Missing nuance
- Explanation unclear

Feedback opens a structured form only as deep as needed.

---

## 6. Reference map

### Default groups

- Core foundations
- Methods adopted/extended
- Datasets and metrics
- Comparisons
- Supporting/contrasting results
- Background mentions
- Needs review
- Inaccessible

### Sort options

- reading priority
- document order
- number of citation occurrences
- confidence
- review risk
- year

### Reference row

- local label
- short title/year
- intent icons
- analysis/access state
- priority
- occurrence count
- save state

No global prestige score is shown by default.

---

## 7. Lineage graph

### Graph semantics

Node: work version  
Edge: verified or attributed relationship

Edge styles include:

- adopts
- extends
- transfers
- combines
- contrasts
- reuses dataset/metric
- cites without verified semantic relation

### Interaction

- selecting edge opens evidence card
- unverified/attributed edges use distinct style and label
- collapse background/perfunctory edges
- depth defaults to one hop; user expands intentionally
- graph has a list/table alternative for accessibility

The graph is not considered useful if edges cannot be inspected.

---

## 8. Progress experience

### Stages

```text
Checking document → Structuring paper → Matching references → Finding source text
→ Retrieving evidence → Comparing claims → Auditing results
```

### Principles

- show results incrementally per citation
- never use a fake linear progress bar disconnected from work units
- surface blocked references without failing the entire paper
- let users prioritize one citation
- let users cancel whole-paper expansion
- preserve already completed, valid evidence cards after partial failure

---

## 9. Empty, limited and error states

### No relevant evidence

> We searched the accessible source but did not find a passage that directly addresses this claim. This may mean the citation is indirect, the relevant content is in another version, or the source requires human inspection.

### Abstract only

> This judgment uses the abstract only. Method details, tables and limitations in the full text were not available to CiteTrace.

### Ambiguous reference

Show 2–5 candidates with title, author, year, venue, identifier and why each matched. Do not preselect a low-confidence candidate as fact.

### Unsupported PDF

Explain exact reason: scanned pages, missing text layer, damaged file, excessive size, unsupported encryption. Offer supported alternatives without implying automatic success.

### Provider outage

> Source matching is temporarily limited. The paper remains available, and completed evidence cards are unchanged. This citation will remain marked as pending until a retry is requested or another source is supplied.

---

## 10. Beginner mode

Beginner mode adds:

- terms and prerequisite cards
- “before this source / source contribution / current paper change” timeline
- short analogy separated from evidence
- acronym expansion
- formula variable glossary
- recommended reading order

It does not remove uncertainty or source links.

---

## 11. Review mode

Review mode prioritizes:

- wrong-paper risk
- low resolution margin
- `overgeneralized`
- `scope_mismatch`
- `contradicts`
- no relevant evidence
- version uncertainty
- citation cluster ambiguity

It provides compact paired evidence and supports private notes. It never outputs an automatic accept/reject recommendation.

---

## 12. Accessibility

- WCAG 2.2 AA target
- semantic landmarks and headings
- keyboard-complete operation
- text alternatives for graph and confidence visualization
- minimum contrast and user-scalable text
- no essential information in hover-only surfaces
- focus announcements for asynchronous card completion
- source quotes and generated explanations clearly labeled for screen readers

---

## 13. Design system tokens

Use semantic tokens rather than hard-coded relation colors:

```text
status.verified
status.limited
status.review
status.error
relation.support
relation.partial
relation.contrast
relation.scope
access.full
access.abstract
access.none
```

Every token maps to color, icon, label and accessible description.

---

## 14. UX validation plan

Test with at least three experience levels and tasks:

1. find why a citation is used,
2. open and validate source evidence,
3. interpret a scope mismatch,
4. distinguish quote from generated explanation,
5. explain why the system abstained,
6. correct a wrong paper/evidence relation,
7. build a five-paper reading queue.

Success is measured by task correctness and interpretation, not only completion speed or preference.
