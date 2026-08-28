# Prompt: Citation Intent Classifier

**Template ID:** `citation_intent_classifier`  
**Version:** `1.0.0`

## System instruction

Classify why the citing paper invokes each target reference. This is a multi-label classification over the closed CiteTrace taxonomy. Use only the citing-paper context and structural metadata. Do not infer support or contradiction from the cited source; that is a separate task.

Return only JSON.

## Allowed labels

`background`, `definition`, `problem_framing`, `method_adoption`, `method_extension`, `dataset_use`, `metric_use`, `benchmark_comparison`, `result_support`, `result_contrast`, `limitation`, `future_direction`, `tool_or_software_use`, `perfunctory_mention`.

## Inputs

```json
{
  "claim": {"id": "uuid", "text": "string", "qualifiers": []},
  "citation_context": {
    "previous_sentence": "string|null",
    "containing_sentence": "string",
    "next_sentence": "string|null",
    "section_path": ["string"]
  },
  "target_reference": {"id": "uuid", "raw_reference": "string", "resolved_title": "string|null"}
}
```

## Rules

1. Select every justified intent and no speculative intent.
2. `method_adoption` means the current work uses a method or component; `method_extension` means it explicitly changes or builds on it.
3. `result_support` and `result_contrast` concern empirical or theoretical findings, not mere topical similarity.
4. `perfunctory_mention` is appropriate only when the target is one example among a broad list with no substantive dependence.
5. Output an empty label list with `review_required=true` when syntax is too ambiguous.

## Output contract

```json
{
  "reference_entry_id": "uuid",
  "labels": [
    {"id": "allowed_label", "confidence": 0.0, "rationale": "one sentence grounded in the context"}
  ],
  "review_required": false,
  "reason_codes": ["stable_snake_case_code"]
}
```
