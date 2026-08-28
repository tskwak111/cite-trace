# CiteTrace evaluation kit

The evaluation suite measures whether CiteTrace is inspectable and scientifically conservative, not merely fluent.

## Dataset layers

1. **Parser set:** citation anchors, reference entries, text offsets and page coordinates.
2. **Resolution set:** reference string to exact work/version identity.
3. **Retrieval set:** atomic claim to relevant source spans.
4. **Relation set:** support, contradiction, scope and abstention labels.
5. **Transformation set:** what was adopted, changed or only compared.
6. **Explanation set:** statement-level grounding and usefulness.
7. **Security set:** prompt injection, malicious PDFs, SSRF and cross-tenant access.

## Split policy

- `development`: prompt and model iteration.
- `calibration`: thresholds and confidence calibration.
- `test`: release gates; hidden from day-to-day prompt authors.
- `challenge`: adversarial and rare cases; never used for fitting.

A paper family, near-duplicate version or citation lineage must remain in one split to prevent leakage.

## Minimum credible release set

- 300 adjudicated citation cases across at least 8 research domains.
- At least 50 multi-reference clusters.
- At least 40 inaccessible or abstract-only references.
- At least 40 scope mismatch, overgeneralization or contradiction cases.
- At least 30 method-transformation cases.
- At least 30 table, equation, figure, algorithm or appendix evidence cases.
- At least 30 adversarial document or prompt-injection cases.

## Running the scaffold evaluator

```bash
python scripts/validate_eval_assets.py
python scripts/score_sample_predictions.py \
  --gold eval/sample_cases.jsonl \
  --predictions eval/sample_predictions.jsonl
```

The included sample cases are synthetic contract examples. They are not scientific benchmark claims and must not be reported as model performance.
