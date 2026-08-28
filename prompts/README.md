# CiteTrace prompt pack

These prompts are versioned contracts, not informal instructions. Runtime code must combine each prompt with:

- exact JSON input schema validation,
- untrusted-content delimiters,
- provider/model/version metadata,
- output JSON Schema validation,
- one bounded schema-repair attempt,
- deterministic postconditions,
- a model execution audit record.

## Required sequencing

1. Claim extraction
2. Citation intent
3. Reference fallback only after deterministic candidate generation
4. Evidence query planning
5. Deterministic retrieval and exact span validation
6. Relation verification
7. Transformation analysis when the intent warrants it
8. Relationship summary
9. Beginner explanation when requested
10. Independent quality audit

No generated explanation may become visible before the quality auditor publishes the evidence link.
