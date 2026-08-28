# Security Policy

## Supported baseline

The `v1.0` package is a design and foundation scaffold. Security fixes apply to the latest maintained branch and must be backported when a deployed release remains supported.

## Reporting

Do not disclose a suspected vulnerability in a public issue. Report it privately to the project security owner with:

- affected component and version,
- reproduction steps or proof of concept,
- impact and required privileges,
- whether private papers, credentials, provider keys, or cross-workspace data may be exposed,
- suggested containment when known.

The deploying organization must replace this section with a monitored security address and response policy before external launch.

## Highest-priority threat classes

- cross-workspace data access or RLS bypass,
- SSRF through DOI, repository, publisher, redirect, or user-supplied URLs,
- malicious PDFs, decompression bombs, parser exploitation, and unsafe file rendering,
- prompt injection embedded in papers, metadata, references, web pages, or retrieved text,
- quotation or coordinate fabrication,
- credential leakage in logs, traces, prompts, exports, or model-provider requests,
- unauthorized persistence or training use of private uploads,
- paywall or access-control circumvention,
- unsafe HTML/Markdown rendering and export injection,
- denial of service through large documents, citation fan-out, recursive lineage, or provider retries.

## Minimum deployment controls

- isolated upload quarantine and malware/content scanning,
- media-type verification independent of filename,
- byte, page, object-count, recursion, timeout, and decompression limits,
- allowlisted outbound providers plus DNS/IP revalidation on every redirect,
- private/link-local/loopback/metadata network denial,
- short-lived scoped credentials and secret-manager storage,
- workspace context set inside each database transaction,
- `FORCE ROW LEVEL SECURITY` verification in integration tests,
- encryption in transit and at rest,
- structured log redaction and no raw private paper text in telemetry,
- immutable source fingerprints and exact-quote validators,
- model gateway enforcing schema, source policy, data classification, and provider routing,
- retention/deletion jobs with receipts and backup aging,
- dependency, container, IaC, and secret scanning in CI,
- incident runbooks for provider compromise, data exposure, and incorrect scientific claims.

## Prompt-injection boundary

All document and provider content is untrusted data. It must never override system policy, tool permissions, source acquisition rules, output schemas, or workspace boundaries. Models propose structured judgments; deterministic code validates identifiers, URLs, offsets, hashes, access decisions, and publication gates.
