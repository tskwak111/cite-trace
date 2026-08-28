# CiteTrace Domain Taxonomy

> **Taxonomy version:** 1.0.0  
> **Purpose:** Stable labels for annotation, APIs, model outputs, UI copy and evaluation.

---

## 1. Design rules

1. Citation intent and transformation are **multi-label**.
2. Evidence relation has one primary label plus optional secondary observations.
3. Labels describe evidence relationships, not author morality or overall paper quality.
4. Every label has inclusion, exclusion and ambiguity rules.
5. Taxonomy changes require migration, evaluation remapping and ADR.

---

## 2. Citation intent taxonomy

### `background`

**Meaning:** Establishes general context, field state or broad prior knowledge.

**Include:** “Deep networks have been widely used for image classification [1–4].”  
**Exclude:** A source from which the exact model is adopted.  
**Ambiguity:** May co-occur with `result_support` when an empirical generalization is claimed.

### `definition`

**Meaning:** Supplies a term, formal definition, notation or conceptual framing.

**Include:** “We use calibration as defined by Guo et al. [7].”  
**Exclude:** Merely mentioning a concept without relying on its definition.

### `problem_framing`

**Meaning:** Establishes the problem, gap, motivation or consequence that justifies the current work.

**Include:** Evidence that current methods fail under a stated condition.  
**Exclude:** Generic field background with no problem implication.

### `method_adoption`

**Meaning:** Uses a method, component, algorithm, loss, architecture or procedure from the cited source.

**Include:** “We follow the optimization procedure of [12].”  
**Exclude:** Comparing against the method without using it.

### `method_extension`

**Meaning:** Explicitly builds on or modifies a cited method.

**Include:** “We extend [12] with a temporal module.”  
**Exclude:** Independent method that only shares vocabulary.

### `dataset_use`

**Meaning:** Uses, filters, merges or derives data from a cited dataset or data-collection work.

**Include:** Dataset paper and benchmark dataset source.  
**Exclude:** A paper that merely reports results on the same dataset if it is not the source used.

### `metric_use`

**Meaning:** Uses an evaluation metric, protocol or statistical test defined or popularized by the cited work.

**Include:** Metric definition or official evaluation protocol.  
**Exclude:** Citing a benchmark result expressed with the metric.

### `benchmark_comparison`

**Meaning:** Compares current results, complexity or behavior against a cited method or reported number.

**Include:** Baseline table entries and state-of-the-art comparison.  
**Exclude:** Using the method as a component.

### `result_support`

**Meaning:** Cited empirical or theoretical result is presented as evidence supporting the current statement.

**Include:** “Prior studies found X [3].”  
**Exclude:** Citation only establishes that a method exists.

### `result_contrast`

**Meaning:** Highlights disagreement, different findings or a limitation relative to the cited work.

**Include:** “Unlike [5], we observe no improvement.”  
**Exclude:** Neutral comparison without contradiction.

### `limitation`

**Meaning:** Attributes or discusses a limitation of prior work or a limitation inherited by the current work.

**Include:** “This approach requires labels [8].”  
**Exclude:** General problem framing not tied to a source limitation.

### `future_direction`

**Meaning:** Cites work to motivate a proposed extension, opportunity or unresolved direction.

**Include:** “Recent work suggests extending this to multimodal settings [9].”  
**Exclude:** Current method extension already implemented.

### `tool_or_software_use`

**Meaning:** Uses software, a library, package, model release, benchmark server or experimental tool.

**Include:** software paper or official tool citation.  
**Exclude:** Citing the method implemented by the tool while not using that implementation.

### `perfunctory_mention`

**Meaning:** The source is listed as a representative example without a specific evidentiary or methodological dependency.

**Include:** Long survey-like citation clusters with no source-specific claim.  
**Exclude:** Cases where a concrete claim can be mapped to the source.

---

## 3. Evidence relation taxonomy

### `direct_support`

The source explicitly states or demonstrates the citing claim at substantially the same scope.

**Required checks:** proposition, population/domain, condition, metric and strength align.

### `partial_support`

The source supports part of the claim, or supports it under narrower/different conditions that the citing text preserves or acknowledges.

**Example:** Source shows improvement on two datasets; citing text says it improved on those datasets.

### `indirect_support`

The source is relevant but the claimed proposition is inferred, synthesized, or supported through another source rather than directly shown.

**Example:** A review cites a primary study; the current paper cites the review for the primary result.

### `contradicts`

The source reports a materially opposite conclusion under comparable scope and conditions.

**Caution:** Different datasets or conditions generally indicate `scope_mismatch`, not contradiction.

### `overgeneralized`

The citing claim expands beyond the evidence's supported scope or certainty.

**Signals:** “always,” “across domains,” causal wording from correlational evidence, population expansion, stronger statistical certainty.

### `scope_mismatch`

The source is relevant but differs in one or more critical scope dimensions such that it cannot directly justify the current claim.

### `no_relevant_evidence`

The accessible source was searched adequately but no evidence relevant to the citing claim was found.

**Do not infer:** This does not prove the source lacks any such evidence under all versions or assets.

### `insufficient_evidence`

Candidates exist, but quality, ambiguity, parsing failure or competing interpretations prevent a reliable relation judgment.

### `inaccessible_source`

The source identity may be known, but the required content was not lawfully available to the system.

---

## 4. Transformation taxonomy

### `adopted_unchanged`

The citing work states or demonstrates use of the source method/component without a material change relevant to the analyzed claim.

### `parameter_changed`

The core method is retained while hyperparameters, thresholds, sizes, schedules or configuration are altered.

### `domain_transferred`

The method or concept is applied to a materially different domain, task, population or modality.

### `extended`

The source method receives a new component, objective, theoretical result or capability.

### `simplified`

The citing work removes components, assumptions or computational steps while retaining the core idea.

### `combined`

Two or more cited methods/components are integrated into a composite approach.

### `benchmark_only`

The cited work is used only as a comparison baseline; its method is not a component of the current approach.

### `dataset_reused`

The current work reuses, filters, augments or re-splits a cited dataset.

### `metric_reused`

The current work adopts a metric or protocol from the cited work.

### `conceptual_inspiration`

The current work claims inspiration without enough implementation overlap for stronger labels.

---

## 5. Scope dimensions

Each evidence relation may record zero or more structured mismatches.

| Dimension | Examples |
|---|---|
| `population` | adults vs children; human vs animal; customer segment |
| `dataset` | one benchmark vs multiple datasets; synthetic vs real |
| `domain` | images vs text; medicine vs finance |
| `task` | classification vs generation; prediction vs causal estimation |
| `time_period` | historical window, follow-up duration |
| `geography` | one country vs global claim |
| `intervention_or_model` | different architecture, dose, policy or treatment |
| `metric` | accuracy vs F1; surrogate vs clinical outcome |
| `experimental_condition` | lab vs field; clean vs noisy setting |
| `statistical_strength` | exploratory trend vs significant result |
| `causal_status` | association vs causal effect |
| `claim_strength` | may/can vs always/proves |
| `version` | preprint vs revised journal result |

---

## 6. Access levels

- `user_private_full_text`
- `open_access_full_text`
- `repository_manuscript`
- `publisher_open_full_text`
- `abstract_only`
- `metadata_only`
- `not_accessible`

Access level is not a confidence score. It describes what content the system was permitted and able to inspect.

---

## 7. Evidence types

- `text_span`
- `equation`
- `table_cell_or_region`
- `figure_or_caption`
- `algorithm_block`
- `appendix_span`
- `metadata_field`
- `abstract_span`

Relations based only on metadata cannot receive direct empirical support labels.

---

## 8. Resolution status

- `resolved`
- `resolved_with_version_uncertainty`
- `ambiguous`
- `unresolved`
- `not_a_scholarly_work`
- `user_confirmed`

---

## 9. Analysis status

- `created`
- `validating`
- `parsing`
- `resolving_references`
- `acquiring_sources`
- `retrieving_evidence`
- `verifying_relations`
- `generating_explanations`
- `auditing`
- `completed`
- `completed_with_limits`
- `failed`
- `cancelled`

---

## 10. Confidence vector

| Field | Meaning |
|---|---|
| `parse` | correctness of document structure, anchor and span extraction |
| `reference_resolution` | confidence that selected canonical work/version is correct |
| `source_access` | completeness and integrity of inspected source asset |
| `evidence_retrieval` | confidence top evidence includes the relevant material |
| `relation_verification` | confidence in relation/scope judgment |
| `explanation_grounding` | proportion and validity of explanation claims grounded to evidence |

Scores are calibrated within task/domain slices. A number without model/policy version and calibration context is not meaningful.

---

## 11. Review priority

- `critical` — possible wrong work, fabricated/missing quote invariant, severe scope or privacy risk
- `high` — relation unstable, strong overgeneralization, conflicting evidence
- `medium` — low confidence, indirect support, version uncertainty
- `low` — clear, high-confidence evidence trail

Review priority is operational triage, not a judgment of paper quality.

---

## 12. Annotation decision sequence

Annotators and models follow this sequence:

1. Is the citation target correctly identified?
2. What exact current claim depends on the target?
3. What role does the citation play?
4. Is relevant source content accessible?
5. Which exact source spans are relevant?
6. What scope dimensions are stated on each side?
7. What primary evidence relation follows?
8. Is there a demonstrable transformation?
9. What uncertainty or competing interpretation remains?
10. Should the system abstain?

Skipping earlier steps invalidates later labels.
