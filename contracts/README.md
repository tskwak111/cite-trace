# CiteTrace machine contracts

## Scope

The checked-in OpenAPI file is the **phase-0 public baseline** implemented by the foundation scaffold: health, analysis create/get/cancel, progress stream, evidence-link read resources and feedback submission. The product specification also defines upload, document, resolution, priority, notes, exports, sharing, deletion and administrative resources. Those are added contract-first by the corresponding implementation-plan task before code is merged.

This split is intentional:

- target behavior remains fully specified in `docs/`,
- the machine contract never claims an unimplemented endpoint exists,
- each vertical slice modifies OpenAPI/JSON Schema/database/event contracts in the same pull request as tests and implementation,
- released API versions are generated only from validated checked-in contracts.

## Sources of truth

- `openapi.yaml` — phase-0 HTTP contract
- `event_catalog.yaml` — asynchronous event contract and delivery semantics
- `schemas/` — versioned persisted/exported JSON objects
- `taxonomies/` — closed controlled vocabularies
- `db/schema.sql` — relational foundation contract and RLS semantics
- `examples/` — executable examples validated by `scripts/validate_package.py`

## Change rules

1. Do not hand-edit generated clients without changing OpenAPI first.
2. Additive `v1` changes still require compatibility tests and examples.
3. Enum semantics, evidence meaning, access policy and confidence interpretation require an ADR and evaluation comparison.
4. Database changes are forward-only migrations in implementation; `schema.sql` must remain equivalent to a clean install.
5. Event consumers must tolerate redelivery and additive fields; event type/schema version changes are explicit.
6. Examples are executable and must pass schema plus semantic validation.
7. A public result must never contain raw provider/model fields outside the approved contract.
