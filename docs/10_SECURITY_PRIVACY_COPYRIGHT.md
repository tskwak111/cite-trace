# CiteTrace Security, Privacy & Copyright Specification

> **Version:** 1.0.0  
> **Scope:** Application, workers, source acquisition, models, storage, collaboration and exports  
> **Note:** This is a technical product policy, not jurisdiction-specific legal advice.

---

## 1. Security objectives

1. Prevent untrusted papers and remote content from compromising systems.
2. Prevent cross-workspace disclosure of documents, evidence and notes.
3. Ensure model/provider calls follow explicit data-transmission policy.
4. Prevent unauthorized acquisition or redistribution of scholarly content.
5. Preserve auditability without logging sensitive raw text by default.
6. Make deletion, retention and sharing behavior understandable and enforceable.

---

## 2. Data classification

| Class | Examples | Default handling |
|---|---|---|
| Public metadata | DOI, public title, authors, venue | cache under provider terms |
| Public OA content | openly licensed/repository manuscript | retain with license and access provenance |
| Workspace-private content | user-uploaded PDF, private notes, derived chunks | tenant-scoped encryption and access |
| Sensitive operational data | credentials, API keys, signed URLs | secrets manager; never prompts/logs |
| Derived judgments | evidence relation, explanation, confidence | inherit strictest source policy |
| Evaluation data | licensed/adjudicated source spans and labels | isolated access and documented rights |

A publicly reachable URL does not automatically make content redistributable.

---

## 3. Threat model

### 3.1 Assets

- user papers and private research materials
- source assets and license metadata
- exact evidence spans and notes
- provider/model credentials
- workspace membership and exports
- gold set and corrections
- provenance and audit records

### 3.2 Adversaries

- unauthenticated internet attacker
- malicious or compromised user
- malicious PDF/source author
- compromised external provider response
- overly privileged internal operator
- accidental developer/logging error
- model prompt injection and data-exfiltration behavior

### 3.3 Trust boundaries

- browser ↔ edge/API
- API ↔ database/object store
- API/orchestrator ↔ worker queue
- worker ↔ document sandbox
- controlled egress ↔ external providers
- model gateway ↔ model provider
- workspace ↔ workspace
- private source ↔ public export

---

## 4. Upload and document processing security

### Required controls

- validate MIME and magic bytes
- reject unsupported encryption/password protection
- limit bytes, pages, object count and decompression ratio
- antivirus and content-disarm policy where available
- strip or ignore active PDF actions, JavaScript and embedded files
- parse in non-root, resource-limited isolated worker
- read-only runtime and no default outbound network
- temporary working directory with quota and secure cleanup
- parser timeout and process kill
- validate parser output before importing to trusted data plane

### Default limits for alpha profile

- maximum upload: 50 MiB
- maximum pages: 60
- maximum references: 150 before explicit limited-mode decision
- maximum parsing time per attempt: policy-configured, bounded
- maximum remote redirects: 3

Limits are configurable by workspace plan but cannot disable core safety checks.

---

## 5. Prompt injection and model safety

### Model input rule

All paper text, metadata and retrieved web content are wrapped as untrusted evidence. Prompts state that content may contain adversarial instructions and must never override system policies.

### Tool isolation

Analysis models do not receive unrestricted tools. Network/source acquisition is handled by typed application adapters with policy checks. A model can request a known operation through a schema; policy code decides whether it executes.

### Output controls

- JSON Schema validation
- enum and span-ID validation
- exact quote verification
- URL/identifier allowlist validation
- unsupported statement audit
- retry cap and typed failure
- separate model gateway credentials and per-route permissions

### Exfiltration prevention

- no secrets in prompts
- redact signed URLs and internal paths
- private document transmission allowed only under workspace model policy
- provider zero-retention/data-training options recorded where applicable
- self-hosted/private model route available for stricter deployments

---

## 6. SSRF and remote acquisition

Remote fetch must:

1. accept only approved schemes,
2. parse and canonicalize URL,
3. resolve DNS and reject private, loopback, link-local, multicast, reserved and cloud-metadata ranges,
4. connect with strict timeout,
5. validate each redirect and final host/IP,
6. limit response bytes and streaming rate,
7. check content type and magic bytes,
8. disallow cookies, browser sessions and ambient credentials,
9. never forward user authentication headers,
10. log safe acquisition metadata and policy decision.

A URL returned by a scholarly provider is a candidate, not automatically trusted.

---

## 7. Authentication and authorization

### Authentication

- secure session/OIDC for web
- short-lived access tokens
- rotating refresh/session protection
- MFA required for privileged operator roles
- service-to-service identity for workers

### Authorization

Roles:

- workspace owner
- admin
- researcher/editor
- viewer
- annotator/reviewer
- platform operator with narrowly scoped audited access

Permissions are resource-specific. Knowing an asset UUID is never sufficient authorization.

### Database isolation

- `workspace_id` on private records
- PostgreSQL RLS for workspace queries
- transaction-scoped tenant context
- service roles that bypass RLS prohibited in user request path
- automated cross-tenant tests

---

## 8. Storage and encryption

- TLS for all service and provider communication
- encryption at rest for database, object storage and backups
- envelope encryption or provider-managed keys; enterprise tenant keys where required
- object keys contain non-guessable IDs and tenant namespace
- signed download URLs are short-lived, single-purpose where feasible
- source assets never served from public buckets by default
- backup restore access is audited

---

## 9. Logging and observability privacy

Default logs may include:

- opaque IDs
- stage and status
- latency, size buckets and provider names
- safe error code
- trace ID

Default logs must not include:

- raw paper paragraphs or evidence quotes
- full reference strings when private
- user notes
- prompt bodies
- credentials, signed URLs or authorization headers
- full provider responses containing licensed text

A secure debug mode requires explicit environment and workspace authorization, short retention and audited access.

---

## 10. Source access and copyright policy

### Allowed acquisition

- user uploads a file they are authorized to process
- openly accessible publisher content under applicable terms
- repository manuscript or preprint
- lawful OA location discovered by an approved locator
- metadata and abstract delivered by a provider under its terms

### Prohibited behavior

- bypassing login, paywall, CAPTCHA, robots/access control or technical protection
- using leaked credentials or shared institutional sessions
- scraping publisher pages contrary to access controls
- redistributing private or licensed PDFs to other users
- displaying excessive source text beyond verification need
- treating an unlicensed cached asset as globally reusable

### Excerpt policy

- display the minimal source excerpt needed to inspect the relationship
- retain exact source span internally under access policy
- attribute title/version/page/section and access source
- apply stricter provider/license-specific rules when required
- exports preserve source and access disclosure

### Version and notices

Record known correction, retraction or editorial-notice metadata when supplied by authorized providers. Do not infer misconduct from a notice alone; display source and status.

---

## 11. Privacy policy behavior

### Defaults

- private uploads are not used to train shared models
- private documents are not indexed for other workspaces
- user feedback tied to private evidence remains private
- model transmission policy is visible and workspace-configurable
- analytics exclude raw content and use pseudonymous IDs

### User controls

- delete document and derived analysis
- set retention duration
- choose approved model route where offered
- export own data and provenance
- manage collaborators and shared links
- revoke shared access

### Deletion

1. access is revoked immediately,
2. active jobs are cancelled,
3. database records enter deletion workflow,
4. object-store assets and derived artifacts are removed,
5. caches are invalidated,
6. backup expiration follows documented schedule,
7. deletion status/receipt is available.

---

## 12. Sharing and exports

Before sharing/exporting:

- verify actor permission
- apply strictest relevant source policy
- avoid embedding full private source files unless explicitly authorized
- limit excerpts
- include access/attribution/provenance
- make links revocable and expiring where appropriate
- prevent search-engine indexing of private shares

A derived explanation may still reveal sensitive research content; it inherits source privacy.

---

## 13. Supply-chain security

- dependency lockfiles
- automated vulnerability and license scanning
- signed/verified container images where possible
- pinned GROBID and base-image versions
- SBOM generation for releases
- secret scanning
- protected branches and required CI
- least-privilege CI credentials
- staged dependency upgrades with parser/evaluation regression tests

---

## 14. Incident response

Severity examples:

- Sev 0: confirmed cross-tenant/private source disclosure
- Sev 1: active exploitation, credential leak, paywall-bypass path, quote provenance corruption at scale
- Sev 2: localized authorization defect, significant provider/model policy violation
- Sev 3: non-sensitive operational degradation

Response flow:

1. contain and revoke access,
2. preserve forensic evidence under privacy policy,
3. disable affected feature/provider/model route,
4. assess scope and affected users,
5. notify according to contractual/legal requirements,
6. repair and add regression tests,
7. publish internal postmortem and tracked actions.

---

## 15. Pre-launch security gates

- threat model reviewed
- upload/parser sandbox penetration tests
- SSRF test suite passes
- cross-tenant authorization/RLS suite passes
- prompt-injection red-team suite passes
- no secrets/raw text in normal logs
- deletion and restore behavior tested
- provider/source terms documented
- dependency/SBOM scan passes release policy
- incident runbook exercised
- commercial copyright/privacy review completed for target markets and customers
