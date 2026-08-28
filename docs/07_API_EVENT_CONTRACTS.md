# CiteTrace API & Event Contracts

> **REST baseline:** v1  
> **Event baseline:** 1.0  
> **Canonical machine contracts:** `contracts/openapi.yaml`, `contracts/event_catalog.yaml`, `contracts/schemas/`  
> **Machine-contract scope:** Phase-0 analyses/evidence/feedback baseline. The target resource map below is extended contract-first by each milestone before implementation.

---

## 1. Contract principles

- Public HTTP resources use stable UUIDs and ISO 8601 UTC timestamps.
- Mutating commands accept `Idempotency-Key`.
- Long-running work returns `202 Accepted` and a durable analysis resource.
- Responses expose limitations and access level, not only success/failure.
- Errors follow RFC 9457-style problem details.
- Model/provider-specific fields never leak into public contracts.
- Enums are versioned controlled vocabularies.
- Events are immutable and include schema version, trace ID and idempotency key.

---

## 2. Core REST resources

### Workspace

```text
GET  /v1/workspaces/{workspace_id}
GET  /v1/workspaces/{workspace_id}/members
```

### Documents and assets

```text
POST /v1/workspaces/{workspace_id}/uploads
POST /v1/workspaces/{workspace_id}/documents:import
GET  /v1/documents/{document_id}
GET  /v1/documents/{document_id}/citations
GET  /v1/documents/{document_id}/references
DELETE /v1/documents/{document_id}
```

### Analyses

```text
POST /v1/analyses
GET  /v1/analyses/{analysis_id}
POST /v1/analyses/{analysis_id}:cancel
GET  /v1/analyses/{analysis_id}/events
GET  /v1/analyses/{analysis_id}/stream
```

### Evidence

```text
GET /v1/analyses/{analysis_id}/evidence-links
GET /v1/evidence-links/{evidence_link_id}
GET /v1/source-spans/{source_span_id}
```

### Resolution and correction

```text
GET  /v1/references/{reference_entry_id}/candidates
POST /v1/references/{reference_entry_id}:confirm
POST /v1/evidence-links/{evidence_link_id}/feedback
```

### Export

```text
POST /v1/analyses/{analysis_id}/exports
GET  /v1/exports/{export_id}
```

---

## 3. Create analysis

### Request

```http
POST /v1/analyses
Idempotency-Key: 63beaf9f-9d3a-4e15-b30b-59b6a109c134
Content-Type: application/json
```

```json
{
  "workspace_id": "70a60a3b-e064-48f8-b938-3d23cc13cc18",
  "document_id": "f77f1be1-d0e0-4104-a536-5afc8fc4e38f",
  "mode": "understand",
  "scope": {
    "kind": "citation_anchors",
    "citation_anchor_ids": ["d83e533e-1246-484b-9f7c-a92a39f290c5"]
  },
  "audience": "beginner",
  "source_policy_profile": "workspace-default"
}
```

### Response

```json
{
  "id": "0d0f9f53-5284-4730-8521-19d43b37d4df",
  "workspace_id": "70a60a3b-e064-48f8-b938-3d23cc13cc18",
  "document_id": "f77f1be1-d0e0-4104-a536-5afc8fc4e38f",
  "status": "created",
  "mode": "understand",
  "audience": "beginner",
  "progress": {
    "stage": "created",
    "completed_units": 0,
    "total_units": 0,
    "percent": 0
  },
  "limitations": [],
  "created_at": "2026-08-28T10:00:00Z",
  "updated_at": "2026-08-28T10:00:00Z",
  "completed_at": null,
  "links": {
    "self": "/v1/analyses/0d0f9f53-5284-4730-8521-19d43b37d4df",
    "stream": "/v1/analyses/0d0f9f53-5284-4730-8521-19d43b37d4df/stream",
    "evidence_links": "/v1/analyses/0d0f9f53-5284-4730-8521-19d43b37d4df/evidence-links"
  }
}
```

### Idempotency behavior

- same workspace, key and equivalent request → return existing logical analysis
- same key with materially different request → `409 idempotency_conflict`
- idempotency record survives normal retries and API process restarts

---

## 4. Evidence link representation

The following object is also stored as the executable example `contracts/examples/evidence-link.verified.v1.json` and is validated against `contracts/schemas/evidence-link.v1.schema.json`.

```json
{
  "id": "e43401b8-4da9-44ad-aa46-49dc49117920",
  "analysis_id": "0d0f9f53-5284-4730-8521-19d43b37d4df",
  "status": "verified",
  "citing_claim": {
    "id": "24905f34-c8e1-434c-aa34-4a1df277ef2c",
    "text": "The method remains effective with limited labeled data.",
    "document_span": {
      "page": 4,
      "start_offset": 2110,
      "end_offset": 2172,
      "bounding_boxes": []
    },
    "qualifiers": [
      "remains effective",
      "limited labeled data"
    ]
  },
  "cited_work": {
    "work_id": "c36d6e18-1844-412f-bb10-6d0de40b3140",
    "work_version_id": "9d02c214-dc58-4358-b85b-51a214f719ef",
    "title": "Example Source Paper",
    "authors": [
      "A. Researcher",
      "B. Scientist"
    ],
    "year": 2025,
    "identifiers": {
      "doi": "10.0000/example"
    },
    "resolution_status": "resolved"
  },
  "citation_intents": [
    "result_support"
  ],
  "evidence_relation": "scope_mismatch",
  "scope_observations": [
    {
      "dimension": "dataset",
      "citing_scope": "general low-label settings",
      "source_scope": "two image-classification datasets",
      "supporting_source_span_ids": [
        "1f746f0a-bf64-48ae-b3fd-70607f775329"
      ]
    }
  ],
  "transformations": [],
  "source_spans": [
    {
      "id": "1f746f0a-bf64-48ae-b3fd-70607f775329",
      "asset_id": "36a6150b-a504-457e-b5fd-a648220e155d",
      "parsed_document_id": "9f62cd4f-218e-42b9-af5c-b88794b5175b",
      "access_level": "open_access_full_text",
      "page": 7,
      "section_path": [
        "4 Experiments",
        "4.2 Low-label setting"
      ],
      "quote": "With 10% of labels, the model improves accuracy on Dataset A and Dataset B.",
      "quote_sha256": "13774b1255fe5536e194d62018e637ceedd685a14966a1c01584ce8c07af829b",
      "start_offset": 8321,
      "end_offset": 8398,
      "evidence_type": "text_span",
      "bounding_boxes": []
    }
  ],
  "abstention": null,
  "explanation": {
    "summary": "The source supports a low-label result on two image datasets, but not a general claim across settings.",
    "statements": [
      {
        "text": "The experiment used 10% labeled data on two image-classification datasets.",
        "kind": "evidence_based",
        "supporting_span_ids": [
          "1f746f0a-bf64-48ae-b3fd-70607f775329"
        ],
        "confidence": 0.96
      },
      {
        "text": "Generalization beyond those datasets is not established by this source.",
        "kind": "inference",
        "supporting_span_ids": [
          "1f746f0a-bf64-48ae-b3fd-70607f775329"
        ],
        "confidence": 0.84
      }
    ]
  },
  "confidence": {
    "parse": 0.99,
    "reference_resolution": 0.96,
    "source_access": 1.0,
    "evidence_retrieval": 0.91,
    "relation_verification": 0.84,
    "explanation_grounding": 1.0,
    "weakest_link": 0.84,
    "balanced_score": 0.949,
    "calibration_profile": "relation-en-cs-v1",
    "reasons": [
      {
        "stage": "relation_verification",
        "code": "scope_language_ambiguous",
        "detail": "The citing claim is broader than the two evaluated datasets."
      }
    ]
  },
  "provenance": {
    "pipeline_version": "1.0.0",
    "taxonomy_version": "1.0.0",
    "prompt_pack_version": "2026-08-28.1",
    "parser_version": "grobid-0.9.1+normalizer-1.0.0",
    "source_policy_profile": "lawful-open-or-user-upload",
    "source_asset_ids": [
      "36a6150b-a504-457e-b5fd-a648220e155d"
    ],
    "source_asset_checksums": {
      "36a6150b-a504-457e-b5fd-a648220e155d": "1111111111111111111111111111111111111111111111111111111111111111"
    },
    "producer_records": [
      {
        "producer_type": "parser",
        "name": "grobid-normalizer",
        "version": "0.9.1+1.0.0",
        "operation": "parse_and_normalize",
        "input_fingerprint": "1111111111111111111111111111111111111111111111111111111111111111",
        "output_fingerprint": "2222222222222222222222222222222222222222222222222222222222222222",
        "occurred_at": "2026-08-28T10:01:00Z",
        "trace_id": "trace-example-001"
      },
      {
        "producer_type": "model",
        "name": "relation-verifier",
        "version": "route-profile-v1",
        "operation": "verify_relation",
        "input_fingerprint": "3333333333333333333333333333333333333333333333333333333333333333",
        "output_fingerprint": "4444444444444444444444444444444444444444444444444444444444444444",
        "occurred_at": "2026-08-28T10:03:00Z",
        "trace_id": "trace-example-001"
      }
    ],
    "access_decisions": [
      {
        "asset_id": "36a6150b-a504-457e-b5fd-a648220e155d",
        "access_level": "open_access_full_text",
        "acquisition_method": "open_repository",
        "policy_profile": "lawful-open-or-user-upload",
        "license_spdx": "CC-BY-4.0",
        "decided_at": "2026-08-28T10:00:30Z"
      }
    ]
  },
  "created_at": "2026-08-28T10:03:12Z"
}
```

---

## 5. Limited and abstained results

Abstention is represented as an evidence link/result, not an HTTP failure. The complete executable object is `contracts/examples/evidence-link.blocked-inaccessible.v1.json`; the excerpt below highlights the domain outcome.

```json
{
  "status": "limited",
  "abstention": {
    "code": "inaccessible_source",
    "message": "The work was resolved, but no lawfully analyzable full text or abstract was available.",
    "recoverable_actions": ["upload_authorized_source"]
  },
  "cited_work": {
    "resolution_status": "resolved"
  },
  "source_spans": [],
  "evidence_relation": "inaccessible_source"
}
```

HTTP `200` is appropriate because the analysis resource was processed correctly and truthfully reached a limited result.

---

## 6. Problem details

```json
{
  "type": "https://errors.citetrace.local/document-too-large",
  "title": "Document exceeds the processing limit",
  "status": 413,
  "code": "document_too_large",
  "detail": "The uploaded PDF has 214 pages; this workspace profile allows 60 pages.",
  "instance": "/v1/workspaces/.../uploads/...",
  "trace_id": "01J6...",
  "retryable": false
}
```

Error codes are stable machine identifiers. Human messages may be localized.

---

## 7. SSE progress

```text
event: analysis.stage.started
id: 129
retry: 5000
data: {"analysis_id":"...","stage":"retrieving_evidence","occurred_at":"...","progress":{"completed_units":3,"total_units":10}}

```

Clients resume with `Last-Event-ID`. SSE delivery may be at-least-once; event IDs and state queries provide deduplication.

---

## 8. Internal event envelope

```yaml
schema_version: '1.0'
event_id: 1ca91103-cb19-4a85-806e-a257a042388c
event_type: analysis.stage.completed
occurred_at: '2026-08-28T10:02:00Z'
trace_id: 5fd0c2f8c4604d9d
workspace_id: 70a60a3b-e064-48f8-b938-3d23cc13cc18
aggregate_type: analysis_run
aggregate_id: 0d0f9f53-5284-4730-8521-19d43b37d4df
idempotency_key: parsing:asset-sha:parser-profile
producer: parsing-worker@1.0.0
payload:
  stage: parsing
  attempt: 1
  output_artifact_ids:
    - 5d0a75a8-c8d4-43af-b2f7-69894898b3dd
  limitations: []
```

---

## 9. Event semantics

### Commands

Commands express intent and may be rejected:

- `analysis.requested`
- `analysis.cancel.requested`
- `source.acquire.requested`
- `reference.confirm.requested`
- `feedback.submit.requested`

### Facts

Facts are immutable:

- `source_asset.registered`
- `document.parsed`
- `reference.resolved`
- `reference.resolution.ambiguous`
- `source.acquired`
- `evidence.retrieved`
- `relation.verified`
- `evidence_link.audited`
- `analysis.completed`
- `feedback.submitted`

Do not name an attempted action as a completed fact.

---

## 10. Concurrency and consistency

- analysis and feedback writes use optimistic versioning where user edits may collide,
- stage handlers acquire short-lived logical locks keyed by analysis/stage/input fingerprint,
- authoritative state is committed transactionally with an outbox event,
- queue delivery may be repeated; handlers must be idempotent,
- read models can be eventually consistent but expose last event/version.

---

## 11. Pagination and filtering

```text
GET /v1/documents/{id}/references?relation=scope_mismatch&access_level=open_access_full_text&limit=50&cursor=...
```

- opaque cursor
- stable sort keys
- maximum limit 100
- response includes `next_cursor` when more data exists

---

## 12. Contract evolution

Backward-compatible:

- add optional field
- add new endpoint
- add enum only when clients are required to handle unknown values safely; otherwise new API version

Breaking:

- rename/remove field
- change field type or semantics
- change confidence meaning
- change default source-policy behavior

Breaking changes require new API/versioned schema and migration period.
