# Prompt: Evidence-Grounded Relationship Summary

**Template ID:** `relationship_summary`  
**Version:** `1.0.0`

## System instruction

Write a compact explanation of why a cited work appears at this citation and what the validated evidence establishes. Every material sentence must cite supplied artifact IDs. Never add facts from memory. Separate direct evidence from inference and limitations. Do not reproduce long passages; quote only the already-approved short source spans.

Return only JSON.

## Inputs

```json
{
  "audience": "beginner|intermediate|expert",
  "mode": "understand|implement|review|survey|present",
  "citing_claim": {"id": "uuid", "text": "string"},
  "cited_work": {"work_version_id": "uuid", "title": "string"},
  "citation_intents": ["string"],
  "relation": "evidence_relation",
  "scope_observations": [],
  "transformations": [],
  "source_spans": [{"id": "uuid", "quote": "string"}],
  "citing_spans": [{"id": "uuid", "quote": "string"}],
  "limitations": []
}
```

## Rules

1. Start with the citation's role, not a generic paper summary.
2. State the relation and its most important scope condition.
3. Explain adoption or change only when a transformation record exists.
4. A sentence labeled `evidence_based` must list supporting span IDs.
5. A sentence labeled `inference` must say it is an inference and list the supporting records.
6. A limitation must not be softened or omitted.
7. In `implement` mode, prioritize exact components, settings and missing reproducibility details.
8. In `review` mode, prioritize claim–evidence mismatch and uncertainty.
9. Do not use a numeric confidence as rhetorical certainty.

## Output contract

```json
{
  "headline": "string",
  "statements": [
    {
      "kind": "evidence_based|inference|limitation|instruction",
      "text": "string",
      "supporting_citing_span_ids": ["uuid"],
      "supporting_source_span_ids": ["uuid"],
      "supporting_record_ids": ["uuid"]
    }
  ],
  "reading_priority": "essential|high|medium|low",
  "recommended_sections": ["string"],
  "unanswered_questions": ["string"]
}
```
