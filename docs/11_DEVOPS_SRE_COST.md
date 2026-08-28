# CiteTrace DevOps, SRE & Cost Control

> **Version:** 1.0.0  
> **Objective:** Operate a trustworthy asynchronous analysis system with measurable quality, graceful degradation and bounded cost.

---

## 1. Environment strategy

| Environment | Data | External calls | Purpose |
|---|---|---|---|
| Local | synthetic/developer-owned | recorded fixtures by default | development |
| CI | synthetic/licensed fixtures | no live secrets | deterministic tests |
| Staging | synthetic/licensed | sandbox/test provider accounts | production-like validation |
| Production | user/public authorized | approved live providers/models | customer use |
| Evaluation | locked licensed gold set | pinned routes | quality comparison |

Production data is never copied into local/CI environments.

---

## 2. Deployment units

Initial deployables:

- web application
- API application
- generic worker image with stage-specific command
- GROBID service
- PostgreSQL + pgvector
- Redis
- object storage
- observability collector

Workers share code but use separate queue/concurrency settings per stage.

---

## 3. CI pipeline

### Pull request

1. formatting and lint
2. type checks
3. unit tests
4. OpenAPI/JSON Schema validation
5. SQL migration validation
6. fast offline pipeline cases
7. security and secret scan
8. build images

### Main branch

- all PR checks
- integration tests with PostgreSQL/Redis/object-store emulator
- recorded-provider contract tests
- expanded evaluation set
- image vulnerability/SBOM generation

### Release

- locked evaluation suite
- migration rehearsal
- staging smoke and failure injection
- signed release artifacts
- deployment approval
- post-deploy health and canary quality checks

---

## 4. Release strategy

- semantic version application releases
- separate versions for API, events, prompts, models, taxonomy and parsers
- feature flags for model routes and high-risk analysis features
- canary by internal workspace, then small customer cohort
- retain prior model/prompt route for rollback
- database migrations are forward-compatible during rolling deployment

Model or prompt rollback must not rewrite historical results; new analyses use the selected current route.

---

## 5. SLO and error budget

### API

- monthly availability: 99.5% initial objective
- completed-card read p95: < 500 ms in target region
- command acceptance p95: < 750 ms excluding upload transfer

### Jobs

- durable state transition success: 99.99%
- completed successful jobs with complete provenance: ≥ 99%
- cancellation acknowledgement: < 5 seconds
- queue age alert thresholds by priority and stage

### Quality invariants

- fabricated displayed quotes: zero tolerance
- cross-tenant access: zero tolerance
- evidence link without source provenance: zero tolerance

Quality invariants are not traded against availability error budget.

---

## 6. Observability design

### Traces

Trace spans:

- API authorization/command
- enqueue/dequeue
- stage execution
- GROBID/provider/model call
- database transaction
- object storage operation
- audit and publication

### Metrics

#### Traffic and user value

- analyses created/completed/limited/cancelled
- priority citation requests
- evidence cards opened
- source spans opened
- feedback/correction events

#### Pipeline

- stage duration and attempts
- parse quality and coordinate coverage
- resolution accepted/ambiguous/unresolved
- source access distribution
- retrieval candidate/rank metrics in eval
- relation/abstention distribution
- audit blocks

#### Dependencies

- provider latency/status/429/cache hit
- model latency/schema failure/retry/cost
- queue depth/oldest age
- DB connections/query latency
- object storage error rate

#### Security/privacy

- denied policy actions
- SSRF blocks
- cross-tenant authorization failures
- deletion backlog
- secure-debug activations

### Logs

Structured JSON, safe identifiers, privacy redaction. Log sampling must never sample away security/audit events required by policy.

---

## 7. Alerting

Page immediately for:

- cross-tenant/security invariant signal
- fabricated quote audit defect in production
- inability to persist analysis/job state
- database/object-store unavailability
- credential exposure detection

Ticket or non-page alerts for:

- provider degradation with functioning fallback
- rising ambiguity/abstention rate
- queue age in background workloads
- cost anomaly
- evaluation drift

Alerts include runbook link, affected version and trace/query identifiers.

---

## 8. Backpressure and quotas

### Per request/document

- upload bytes/pages/references
- maximum reference fan-out
- maximum recursive depth
- model-call budget
- remote acquisition byte budget
- stage deadline and retry cap

### Per workspace

- concurrent high-priority jobs
- concurrent background jobs
- daily/monthly analysis budget
- storage and retention
- provider/model cost cap

### Global

- provider token buckets
- model route budget
- worker autoscaling ceiling
- batch/evaluation isolation

When a budget is reached, return a transparent limited state or queue decision; do not silently drop evidence.

---

## 9. Cost model

Track unit economics per:

- document
- citation analyzed
- verified evidence link
- resolved source
- full-text acquisition
- embedding/chunk count
- model stage

### Cost ledger fields

- provider/model
- call type
- request units/tokens
- cache hit/miss
- latency
- billable cost
- workspace/analysis/stage
- source access and outcome

### Optimization order

1. remove unnecessary calls and fan-out,
2. cache immutable metadata and source parses under policy,
3. prioritize citations users open,
4. route cheap deterministic/classifier steps before strong models,
5. escalate only uncertain/high-value cases,
6. batch embeddings and provider requests safely,
7. tune models only after correctness gates.

Do not reduce source verification merely to lower cost without a visible product-scope change.

---

## 10. Capacity model

Key workload drivers:

- pages per document
- citation anchors and unique references
- percentage of sources with accessible full text
- chunks per source
- active citation scope vs whole-paper scope
- recursive depth
- verifier escalation rate

Capacity planning uses distributions, not an “average paper.” Measure p50/p90/p99 document sizes and fan-out.

---

## 11. Resilience patterns

- timeouts at every external boundary
- bounded exponential backoff with jitter
- circuit breakers
- bulkheads by provider/stage
- idempotent handlers
- transactional outbox for durable events
- checkpoint/resume
- dead-letter review with safe payload metadata
- fallback from full-text provider to alternate lawful source or limited state

No fallback may silently change from private/local processing to a third-party model route.

---

## 12. Backup and disaster recovery

- encrypted automated PostgreSQL backups and point-in-time recovery
- object-store versioning/replication according to policy
- separate backup credentials
- restore tests on schedule
- metadata and object consistency reconciliation
- deletion policy propagated to backup expiry documentation

Initial objectives should be set after infrastructure choice; critical provenance and user assets require tested RPO/RTO rather than marketing-only numbers.

---

## 13. Runbook index

Required runbooks:

- API unavailable
- PostgreSQL unavailable/degraded
- Redis queue unavailable
- GROBID failure or parse-quality regression
- provider 429/outage
- model provider outage/schema failure spike
- queue backlog
- object-store access failure
- source-acquisition security block spike
- cross-tenant incident
- deletion backlog
- prompt/model quality rollback
- migration rollback/forward fix

---

## 14. Operational dashboards

### Executive trust dashboard

- verified vs limited analyses
- source-open and correction rates
- quality invariant failures
- gold-set trend
- cost per verified evidence link

### Pipeline dashboard

- stage throughput/latency/errors
- queue age
- access and abstention distribution
- provider/model health

### Security/privacy dashboard

- policy denies
- SSRF and malicious file blocks
- privileged access
- deletion status
- secret and dependency scan status

---

## 15. Production readiness review

Before production:

- SLOs and alerts implemented
- all stages idempotent and resumable
- provider/model outage drills completed
- quotas/backpressure tested
- cost ledger reconciles with provider billing samples
- backup restore completed
- migration and rollback rehearsed
- privacy-safe observability verified
- security and quality release blockers automated
