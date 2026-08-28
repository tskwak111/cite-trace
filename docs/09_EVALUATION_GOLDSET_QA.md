# CiteTrace Evaluation, Gold Set & Quality Assurance

> **Version:** 1.0.0  
> **Purpose:** Prevent fluent but ungrounded output from reaching users and make quality changes measurable.

---

## 1. Evaluation philosophy

CiteTrace is a pipeline. A good final explanation can hide a wrong paper identity or fabricated quote. Evaluation therefore measures every critical stage and the full user-visible result.

Principles:

1. evaluate with immutable source versions,
2. measure abstention as a first-class outcome,
3. report domain and failure slices, not only aggregate scores,
4. block release on invariant failures even when average metrics improve,
5. keep human adjudication separate from model-generated labels,
6. compare model/prompt/parser versions on the same locked set.

---

## 2. Evaluation layers

### Layer A — Deterministic invariants

- quote substring and checksum
- source span boundaries
- work/version/source associations
- access-level compatibility
- schema and enum validity
- tenant/source-policy constraints

Any failure is a defect, not a statistical error.

### Layer B — Component metrics

- parsing and citation linking
- reference resolution
- evidence retrieval
- relation/scope classification
- transformation classification
- explanation grounding
- confidence calibration

### Layer C — End-to-end case evaluation

A human evaluates the full evidence card for correctness, completeness, inspectability and usefulness.

### Layer D — UX interpretation

Users must understand what is quoted, inferred, uncertain and inaccessible.

### Layer E — Operational quality

Latency, reliability, cost, provider degradation, privacy and deletion behavior.

---

## 3. Gold-set composition

### 3.1 Initial size

- internal development set: 100–150 cases
- beta gate: at least 300 adjudicated cases
- target mature baseline: 500+ cases with domain slices

A case is a citation claim–target pair, not merely a paper.

### 3.2 Sampling dimensions

- domain: computer science/AI, life science/medicine, additional pilot fields
- citation style: numeric, author–year, ranges and clusters
- section: introduction, related work, methods, experiments, discussion, appendix
- intent labels
- relation labels
- source access level
- direct/indirect and easy/hard retrieval
- version ambiguity
- text, table, figure and equation evidence
- born-digital quality variations
- positive, negative and abstention cases

### 3.3 Required hard cases

- multiple citations attached to one broad claim
- one citation supporting only one clause
- review paper citing a primary result
- same/similar title collision
- preprint vs journal revisions with changed results
- source limitation omitted by citing sentence
- correlation described causally
- source supports a narrower population/dataset
- conflicting spans within source
- cited paper does not contain the attributed result
- abstract suggests support but full text limits it
- inaccessible full text
- malicious prompt-injection text

---

## 4. Annotation schema

Each case records:

- citing paper work/version and asset checksum
- citation anchor and cluster
- atomic claim exact span
- intended reference target(s)
- canonical cited work/version
- acceptable alternative versions
- source access level
- relevant evidence spans and evidence types
- limiting/counterevidence spans
- citation intent labels
- primary evidence relation
- scope dimensions
- transformation labels and paired citing spans
- acceptable abstention outcomes
- difficulty and rationale
- annotators, agreement and adjudication

Use `eval/goldset_template.csv` for ingestion and richer JSON for multi-span annotations.

---

## 5. Annotation process

1. curator selects case and locks source assets,
2. annotator A independently labels,
3. annotator B independently labels,
4. disagreements are classified,
5. adjudicator resolves critical fields,
6. case is validated for exact spans and source versions,
7. case enters development or locked test split,
8. future edits create a new case version.

Annotators may use search tools to find spans but cannot use the candidate system output as the initial label source.

---

## 6. Metrics

### 6.1 Parsing and citation linking

- citation anchor precision/recall/F1
- bibliography entry extraction accuracy
- anchor-to-reference accuracy
- coordinate coverage and region IoU where annotated
- citation cluster expansion accuracy

### 6.2 Reference resolution

- top-1 accuracy
- Recall@5
- mean reciprocal rank
- ambiguity precision/recall
- version selection accuracy
- expected calibration error for accepted resolutions

### 6.3 Evidence retrieval

- Recall@1, @3, @5 and @10
- mean reciprocal rank
- span overlap / token F1
- section accuracy
- evidence-type accuracy
- counterevidence recall
- no-evidence abstention accuracy

### 6.4 Citation intent

Because labels are multi-label:

- micro/macro F1
- per-label precision/recall
- exact-set match
- calibration by label

### 6.5 Evidence relation

- macro-F1 across relation labels
- per-label confusion matrix
- scope-dimension F1
- comparable-scope contradiction precision
- overgeneralization precision
- abstention coverage vs risk

### 6.6 Transformation

- multi-label macro-F1
- paired-span sufficiency rate
- unsupported transformation claim rate
- graph-edge precision on audited subset

### 6.7 Explanation grounding

- displayed fabricated quote rate
- material statement evidence coverage
- unsupported statement rate
- relation/explanation consistency
- access-disclosure correctness
- human correctness and usefulness rating

### 6.8 Confidence

- reliability diagrams
- expected calibration error
- Brier score where probabilistic interpretation is validated
- selective risk curve: error rate as low-confidence cases abstain
- weakest-stage reason correctness

---

## 7. Initial release targets

Targets are aspirational gates to validate, not claims of achieved performance.

| Metric | Target |
|---|---:|
| Citation anchor precision | ≥ 98% |
| Citation anchor recall | ≥ 95% |
| Anchor-to-reference accuracy | ≥ 97% on supported documents |
| Resolution top-1 accuracy | ≥ 92% overall; ≥ 97% with valid exact identifier |
| Ambiguity precision | ≥ 90% |
| Evidence retrieval Recall@5 | ≥ 85% |
| Relation macro-F1 | ≥ 0.75 |
| Fabricated displayed quote rate | 0 in blocking suite |
| Unsupported material statement rate | ≤ 2% |
| Inaccessible-source abstention accuracy | ≥ 95% |
| Human usefulness | ≥ 4.0/5 |

Domain slices must have sufficient cases; a high aggregate cannot hide a failing launch domain.

---

## 8. Blocking quality gates

A release is blocked by:

- any fabricated displayed quote in locked blocking cases,
- private-tenant leakage or unauthorized source sharing,
- relation output without accepted evidence,
- direct support based only on metadata,
- prompt injection causing policy or secret leakage,
- wrong source asset/version in user-visible provenance,
- schema-invalid output reaching API/UI,
- critical slice regression beyond agreed threshold,
- deletion/access-revocation failure.

---

## 9. Regression suites

### Fast PR suite

- deterministic unit and contract tests
- 20–30 representative offline cases
- no live provider/model dependency
- quote and provenance invariants

### Main branch suite

- 100+ development cases
- recorded provider fixtures
- fixed model snapshots or deterministic model test doubles
- component and end-to-end metrics

### Release suite

- locked adjudicated set
- approved live model routes with pinned versions
- adversarial security cases
- load and failure-injection tests
- human review sample

### Shadow production evaluation

Sample only with policy/consent. Compare new versions without affecting user results; never pool private documents into training or public evaluation automatically.

---

## 10. Red-team catalog

### Document attacks

- huge object counts or compressed streams
- malformed xref tables
- embedded files/scripts/links
- deceptive Unicode and invisible text
- reading-order traps
- scanned pages mixed with text layer

### Prompt injection

- direct instruction override
- fake system messages in paper
- instructions to call URLs or reveal credentials
- adversarial text hidden in references, tables or metadata
- data exfiltration requests disguised as scholarly content

### Scientific reasoning failures

- causal/correlational swap
- population generalization
- cherry-picked supporting span ignoring limitations
- citation of a review for primary evidence
- version-changed result
- source citing another source without direct evidence
- non-comparable contradiction

### Access and privacy

- private URL/localhost SSRF
- signed URL reuse
- cross-workspace asset ID enumeration
- deleted asset retrieval
- private text in logs/traces/model debug storage

---

## 11. Human evaluation rubric

Rate 1–5:

- source identity correctness
- evidence relevance
- evidence completeness
- relation correctness
- transformation correctness
- explanation faithfulness
- limitation clarity
- inspectability
- usefulness for the selected mode

Critical binary flags:

- fabricated quote
- wrong paper/version
- unauthorized content exposure
- unsupported strong claim
- misleading certainty

---

## 12. Experiment protocol

Every model/prompt/retrieval change records:

- hypothesis
- exact version/configuration
- evaluation set version
- primary and guardrail metrics
- per-slice results
- cost/latency impact
- observed error examples
- go/no-go decision and reviewer

Do not promote solely because a single aggregate metric improved.

---

## 13. Production monitoring

Monitor leading indicators:

- wrong-paper feedback rate
- evidence correction rate
- relation correction rate
- abstention rate by provider/domain
- audit-block rate
- source-open rate
- provider and model version shifts
- parse-quality distribution
- cost per verified evidence link

Production feedback informs case selection; it does not automatically become ground truth.
